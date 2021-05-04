import serial
import time


class ArduinoCom:
    """Handles serial communication with the Arduino."""

    # Serial Settings
    _SERIAL_PORT = "/dev/ttyAMA0"
    _BAUD = 9600
    _TIMEOUT = 3

    # Commands
    _GET_BATTERY = "1"
    _MOSFET_SHUTDOWN = "2"
    _IR_LED_ON = "3"
    _IR_LED_OFF = "4"
    _IS_MOTION_WAKEUP = "5"

    def __init__(self):
        """Initialize serial communciation with the Arduino"""
        try:
            print(f"Connecting to Arduino on '{self._SERIAL_PORT}'...", end='')
            self.ser = serial.Serial(self._SERIAL_PORT, self._BAUD, timeout=self._TIMEOUT)
            # Reset buffers to start with a clean slate
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            print("Ok")
        except serial.SerialException as e:
            print("Failed:", e)

    def get_battery(self) -> float:
        """Gets battery level from the Arduino"""
        resp = self.send_command(self._GET_BATTERY)
        try:
            return float(resp)
        except ValueError as e:
            print(f"Error parsing battery voltage '{resp}':", e)
            return 0.0

    def shutdown_mosfet(self) -> str:
        """Tells the Arduino to shut down the mosfet"""
        return self.send_command(self._MOSFET_SHUTDOWN)

    def ir_led_on(self) -> str:
        return self.send_command(self._IR_LED_ON)

    def ir_led_off(self) -> str:
        return self.send_command(self._IR_LED_OFF)

    def is_motion_wakeup(self) -> bool:
        return self.send_command(self._IS_MOTION_WAKEUP) == "1"

    def set_time(self, minutes: int) -> str:
        # Need to get response two times, since arudino responds with two lines
        return self.send_command(str(minutes)) + self.recv_response()

    def serial_ok(self) -> bool:
        """True if serial is connected ready to go, else false"""
        return self.ser is not None

    def close(self):
        """Close connection to Arduino"""
        self.ser.close()

    def recv_response(self) -> str:
        try:
            return self.ser.readline().decode('ascii').strip('\r\n')
        except UnicodeDecodeError as e:
            print("Error receiving Arduino response:", e)
            return ""

    def send_command(self, command: str) -> str:
        """Send command and wait for response"""
        if self.serial_ok():
            print(f"Sending command '{ command }' (ascii-code: { int.from_bytes(command.encode(), 'little') })")
            self.ser.write(command.encode())
            return self.recv_response()
        else:
            print("Error: Can't send Arduino command. Serial not initialized.")


def main():
    # Main function with just some tests
    arduino = ArduinoCom()

    time.sleep(1)
    print(arduino.get_battery())
    time.sleep(1)
    print(arduino.ir_led_on())
    time.sleep(1)
    print(arduino.ir_led_off())
    time.sleep(1)
    print(arduino.settime(10))


if __name__ == '__main__':
    main()
