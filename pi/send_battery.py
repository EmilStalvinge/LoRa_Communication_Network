#!/usr/bin/env python3

from float_encode_decode import encode_float
from lora_base import LoraBase
from lora.tcp_handshake import ThreeWayHandshake
from arduino_com import ArduinoCom


class SendBattery(LoraBase):
    """
    Sends battery voltage
    """
    def __init__(self, arduino: ArduinoCom):
        """
        Class initializer
        """
        super().__init__()
        self.arduino = arduino

    def send(self):
        """
        Send battery voltage
        Raises:
            LoraTxTimeoutException: If sending times out. Timeout length is defined in base class
            SerialConnectionException: If serial connection to the RN2483 LoRa module times out
        """
        lora = self.init_lora()

        if lora and ThreeWayHandshake(lora).request_conn():
            self.lora.send_message(self._START_BAT_TRANS, self._MAX_TX_TRIES)
            battery_msg = encode_float(self.arduino.get_battery())
            self.lora.send_message(battery_msg, self._MAX_TX_TRIES)
            self.lora.send_message(self._FINISH_BAT_TRANS, self._MAX_TX_TRIES)

            self.close_serial_conn()


def main():
    SendBattery().send()


if __name__ == '__main__':
    main()
