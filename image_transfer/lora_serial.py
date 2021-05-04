import serial.tools.list_ports
from sys import argv


def recv_line(ser):
    """Receive characters until line end ('\r\n')"""
    message = ""
    while message[-2:] != "\r\n":
        message += ser.read().decode('ascii')

    print("<", message[:-2])
    return message


def recv_radio_message(ser):
    """Listen for a message and remove 'radio rx' and '\r\n' from response """
    send_line(ser, "radio rx 0")
    return recv_line(ser).split(' ')[-1].strip()


def send_line(ser, line,):
    """Send line followed by a line end ('\r\n'), and wait for the response."""
    print(">", line)
    ser.write((line + "\r\n").encode('ascii'))
    return recv_line(ser)


def send_radio_message(ser, message):
    """Send a message over radio """
    send_line(ser, "radio tx " + message)
    recv_line(ser)  # Wait for a "radio_tx_ok"


def connect_serial(port_name):
    """Connect to a serial port, and return a serial object (or None if no device was found)"""
    print("Connecting to " + port_name + "... ", end='')
    try:
        ser = serial.Serial(port_name, 57600)
        print("Ok")
        return ser
    except serial.SerialException:
        print("Failed")


def get_serial_connection():
    if len(argv) < 2:
        print("Usage: python3 " + argv[0] + " PORT")
        print("e.g. python3 " + argv[0] + " COM5")
        print("or python3 " + argv[0] + " /dev/ttyUSB0")
        return None
    return connect_serial(argv[1])


def send_lines(ser, watchdog):
    send_line(ser, "sys reset")
    send_line(ser, "mac pause")
    send_line(ser, "radio set " + watchdog)
    send_line(ser, "radio set mod fsk")

