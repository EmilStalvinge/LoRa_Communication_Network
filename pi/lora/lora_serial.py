import serial
from time import sleep, time
from sys import argv
from .exceptions import SerialConnectionException, LoraRxTimeoutException, LoraRxRadioException

DEFAULT_PORT = "/dev/ttyUSB0"


def get_serial_connection() -> serial.Serial:
    """
    Connect to the serial port provided as a command line argument,
    or DEFUALT_PORT if no argument was given.
    Returns a serial object (or None if no device was found)
    """
    if len(argv) < 2:
        port = DEFAULT_PORT
        print(f"No port specified. Using '{port}'")
    else:
        port = argv[1]

    print(f"Connecting to {port}... ", end='')
    try:
        ser = serial.Serial(port, 57600)
        print("Ok")
        return ser
    except serial.SerialException as e:
        print("Failed: ", e)


class LoraSerial:
    """Handles a connection to a RN2483 LoRa chip
    Args:
        ser: The serial connection (from pyserial)
        bandwidth: The bandwidth of the radio, in kHz. Valid values are 125, 250, 500.
        sf Spreadfactor of radio, only valid for 'lora'. Valid values are 'sf7' to 'sf12'
        power Power of radio, in dBm. Valid values are -3 to 15.
        coding_rate: Ratio of data to total size (i.e. data + redundancy). Valid values are '4/5', '4/6', '4/7', '4/8'
        debug_serial: Whether to print all messages to and from the RN2483.

    Attributes:
        ser: The serial connection (from pyserial)
        debug_serial: Whether to print all messages to and from the RN2483.
        wdt: The latest applied watchdog timer

    Raises:
        SerialConnectionException: If serial connection response from RN2483 module times out
    """
    SERIAL_READ_TIMEOUT = 3000  # ms read timeout for serial connection to RN2483

    def __init__(self, ser: serial.Serial, bandwidth: float = 250, sf: str = "sf7", freq: int = 863500000,
                 power: int = 14, coding_rate: str = "4/5", debug_serial: bool = False):
        self.ser = ser
        self.ser.timeout = self.SERIAL_READ_TIMEOUT
        self.debug_serial = debug_serial
        self.wdt = 0

        self._send_init_commands([
                "sys reset",
                "mac pause",
                f"radio set freq {freq}",
                f"radio set wdt {self.wdt}",
                "radio set mod lora",
                f"radio set sf {sf}",
                f"radio set pwr {min(max(power, -3), 15)}",
                # Crc is not supported by the fipy LoRa, so leave it off always
                f"radio set crc off",
                f"radio set cr {coding_rate}",
                f"radio set bw {bandwidth}"
        ])

    def _send_init_commands(self, commands):
        """Send a list of commands as initialization of the RN2483
        Raises:
            SerialConnectionException: If any command response times out
        """
        for comm in commands:
            print(comm, end=": ")
            resp = self._send_command(comm)
            print(resp)

    def recv_raw(self, timeout_ms) -> bytes:
        """Receive a raw message over LoRa
        Args:
            timeout_ms: Timeout in milliseconds before the reception should time out.
        Returns:
            The bytes received.
        Raises:
            LoraRxTimeoutException: If no packet is received within timeout_ms milliseconds
            LoraRxRadioException: If packet is detected, but could not be received
            SerialConnectionException: If any serial response from RN2483 times out
        """
        self._set_radio_timeout(timeout_ms)

        # Radio might be busy, try until ready
        while (self._send_command("radio rx 0") != "ok"):
            pass
        t_start = time()

        # Add a slight offset to serial timeout, to never time out serial while waiting for message.
        response = self._recv_command(timeout_ms + 200)

        if response.startswith("radio_rx"):
            hex_message = response.lstrip("radio_rx ")
            try:
                return bytes.fromhex(hex_message)
            # If for some reason RN2483 returns uneven-length data
            except ValueError:
                print(f"ERROR: Got non-even length hex string '{hex_message}'")
                return bytes.fromhex(hex_message[:-1])
        else:
            # RN2483 returns 'radio_err' on both timeout and error.
            if time() - t_start > timeout_ms / 1000:
                raise LoraRxTimeoutException(timeout_ms)
            else:
                raise LoraRxRadioException

    def send_raw(self, message: bytes):
        """Send a raw message over LoRa, without waiting for any ACK/NACK
        Args:
            message: Bytes to send, must be at most 255 bytes
        Raises:
            SerialConnectionException: If any serial response times out
        """
        self._set_radio_timeout(0)
        command = "radio tx " + message.hex()

        command_resp = self._send_command(command)
        while (command_resp != 'ok'):
            if (command_resp == 'busy'):
                sleep(0.1)
                command_resp = self._send_command(command)
            else:
                print("Received 'invalid_param'. Non-hex characters in message string?")
                break

        self._recv_command()  # Wait for a "radio_tx_ok"

    def snr(self) -> int:
        """Get SNR of last received transmission (dB)
        Raises:
            SerialConnectionException: If response times out
        """
        snr = self._send_command("radio get snr")
        try:
            return int(snr)
        except ValueError:
            print(f"Unable to convert SNR '{snr}' to an int")
            return 0

    def _set_radio_timeout(self, timeout_ms: int):
        """Set the time in milliseconds of radio watchdog, after which 'radio...' commands to RN2483 return radio_err
        Raises:
            SerialConnectionException: If serial connection times out
        """
        if (self.wdt != timeout_ms):
            self._send_command("radio set wdt " + str(timeout_ms))
            self.wdt = timeout_ms

    def _recv_command(self, timeout_ms: int = SERIAL_READ_TIMEOUT) -> str:
        """Receive a command from the RN2483 (e.g. 'radio_tx_ok')
        Args:
            timeout_ms: Time in milliseconds to wait at most for a response
        Returns:
            The command string received.
        Raises:
            SerialConnectionException: If response times out
        """
        self.ser.timeout = timeout_ms / 1000
        message = ""
        while message[-2:] != "\r\n":
            message_part = self.ser.read().decode('ascii')
            if message_part:
                message += message_part
            else:  # Timeout
                raise SerialConnectionException()

        message = message.rstrip("\r\n")
        if (self.debug_serial):
            if (len(message) < 50):
                print("<", message)
            else:
                print("<", message[:50] + "...")
        return message

    def _send_command(self, line: str, timeout_ms: int = SERIAL_READ_TIMEOUT) -> str:
        """Send line to RN2483 followed by a line end ('\r\n'), and return response.
        Args:
            timeout_ms: Time in milliseconds to wait at most for a response
        Raises:
            SerialConnectionException: If response times out
        """
        if (self.debug_serial):
            if (len(line) < 50):
                print(">", line)
            else:
                print(">", line[:50] + "...")
        self.ser.timeout = None
        self.ser.write((line + "\r\n").encode('ascii'))
        return self._recv_command(timeout_ms)
