#!/usr/bin/env python3

import tarfile
from lora_base import LoraBase
from lora import ThreeWayHandshake


class SendImage(LoraBase):
    """
    Send image class
    """

    TAR_FILE = "photo.tar.gz"

    def __init__(self, file_name):
        """
        Class initializer
        """
        super().__init__()
        self.file_name = file_name

    def start_sending(self):
        """
        Send image transmissions
        Returns:
            True if image was sent successfully, else false
        Raises:
            LoraTxTimeoutException: If sending times out. Timeout length is defined in base class
            SerialConnectionException: If serial connection to the RN2483 LoRa module times out
        """
        lora = self.init_lora()

        if lora:
            if ThreeWayHandshake(lora).request_conn():
                with tarfile.open(self.TAR_FILE, "w:gz") as tar:
                    tar.add(self.file_name)
                with open(self.TAR_FILE, "rb") as f:
                    tar_bytes = f.read()

                self.lora.send_message(self._START_IMG_TRANS, self._MAX_TX_TRIES)
                self.lora.send_message(tar_bytes, self._MAX_TX_TRIES)
                self.lora.send_message(self._FINISH_IMG_TRANS, self._MAX_TX_TRIES)

                self.close_serial_conn()
                return True

            else:
                print("3-way handshake failed.")
                self.close_serial_conn()

        return False


def main():
    snd_img = SendImage("image.jpg")
    snd_img.start_sending()


if __name__ == '__main__':
    main()
