from take_picture import take_pic, get_unsent_pics, mark_pics_sent
from send_image import SendImage
from send_battery import SendBattery
from lora.exceptions import LoraTxTimeoutException, SerialConnectionException
from arduino_com import ArduinoCom
import subprocess


BATTERY_THRESHOLD = 3.3


def main():
    arduino = ArduinoCom()

    print("Checking GPIO pin")
    if not arduino.is_motion_wakeup():
        print("Timer wakeup")
        print("Sending pictures")
        unsent = get_unsent_pics()
        print("Unsent pictures:", unsent)

        if unsent:
            for pic in unsent:
                try:
                    if SendImage(pic).start_sending():
                        mark_pics_sent(pic)
                    else:
                        print(f"Image '{pic}' could not be sent.")
                except (LoraTxTimeoutException, SerialConnectionException) as e:
                    print("Sending image failed:", e)
                    print("Aborting image sending")
                    break
        else:
            send_battery = SendBattery(arduino)
            if arduino.get_battery() < BATTERY_THRESHOLD:
                print("Sending battery voltage")
                send_battery.send()
    else:
        print("PIR active, taking picture")
        arduino.ir_led_on()
        take_pic()
        arduino.ir_led_off()

    print("Sending shutdown signal to Arduino")
    # TODO Do we need to add arduino.set_timer here?
    print("arduino.shutdown_mosfet()")
    # arduino.shutdown_mosfet()
    arduino.close()
    print("Shutting down")
    print("subprocess.Popen(['sudo', 'halt'])")
    # subprocess.Popen(['sudo', 'halt'])


if __name__ == '__main__':
    main()
