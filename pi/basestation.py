from basestation_receiver import BasestationReceiver
from lora.exceptions import SerialConnectionException, LoraRxTimeoutException
from arduino_com import ArduinoCom
import subprocess


def main():

    print("Receiving pictures/battery data")
    try:
        BasestationReceiver().start_receiving()
    except (LoraRxTimeoutException, SerialConnectionException) as e:
        print("Sending image failed:", e)
        print("Aborting image sending")

    print("Sending shutdown signal to Arduino")
    # TODO Do we need to add arduino.set_timer here?
    arduino = ArduinoCom()
    print("arduino.shutdown_mosfet()")
    # arduino.shutdown_mosfet()
    arduino.close()
    print("Shutting down...")
    print("subprocess.Popen(['sudo', 'halt'])")
    # subprocess.Popen(['sudo', 'halt'])


if __name__ == '__main__':
    main()
