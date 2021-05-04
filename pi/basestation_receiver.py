#!/usr/bin/env python3

import tarfile
import os
import subprocess
from float_encode_decode import decode_float
from lora_base import LoraBase
from gdrive import GdriveUploader
from lora import ThreeWayHandshake


class BasestationReceiver(LoraBase):
    """
    Receive image/battery voltage class
    """

    __RCVD_IMG = 'received_image.jpeg'
    __RCVD_TAR = 'received_image.tar.gz'
    __BAT_FILE = 'battery_voltages.txt'
    __LINUX_SYS = 'linux'
    __WINDOWS_SYS = 'win32'
    __APPLE_SYS = 'darwin'
    __LINUX_IMG_VWR = 'xdg-open'
    __WINDOWS_IMG_VWR = 'explorer'
    __APPLE_IMG_VWR = 'open'

    def __init__(self):
        """
        Class initializer
        """
        super().__init__()
        self.gdrive = GdriveUploader()

    def open_image(self):
        """
        Open an image in system's default viewer
        """
        image_viewer = {self.__LINUX_SYS: self.__LINUX_IMG_VWR,
                        self.__WINDOWS_SYS: self.__WINDOWS_IMG_VWR,
                        self.__APPLE_SYS: self.__APPLE_IMG_VWR}[self._SYS_PLTFRM]
        try:
            subprocess.run([image_viewer, self.__RCVD_IMG])
        except FileNotFoundError:
            pass

    def receive_until(self, end: bytes) -> bytes:
        """
        Receive bytes until end marker
        Raises:
            LoraRxTimeoutException: If receiving times out. Timeout length is defined in base class
            SerialConnectionException: If serial connection to the RN2483 LoRa module times out
        """
        received_bytes = b''
        message = self.lora.recv_message(self._RX_TIMEOUT).message

        while message != end:
            received_bytes += message
            message = self.lora.recv_message(self._RX_TIMEOUT).message

        return received_bytes

    def receive_image(self):
        """
        Receive and store an image into file
        Raises:
            LoraRxTimeoutException: If receiving times out. Timeout length is defined in base class
            SerialConnectionException: If serial connection to the RN2483 LoRa module times out
        """
        print("Receiving image...")
        received_bytes = self.receive_until(self._FINISH_IMG_TRANS)

        print("Writing tar...")
        with open(self.__RCVD_TAR, "wb") as tar:
            tar.write(received_bytes)
            print("Done!")

        print("Extracting image...")
        if tarfile.is_tarfile(self.__RCVD_TAR):
            try:
                with tarfile.open(self.__RCVD_TAR, 'r:gz') as tar:
                    members = tar.getmembers()
                    if len(members) > 0:
                        if len(members) > 1:
                            print("WARNING: Expected 1 file in received .tar,"
                                  "got {len(members)}")
                        tar.extract(members[0])
                        os.rename(members[0].name, self.__RCVD_IMG)
                        print("Done!")
                    else:
                        print("ERROR: No files in received tar")
            except Exception as e:
                print("ERROR: Can't extract received .tar file:", e)
        else:
            print("ERROR: Received file is not a valid .tar file.")

    def receive_battery(self) -> float:
        """
        Receive battery voltage and append it to a file
        Raises:
            LoraRxTimeoutException: If receiving times out. Timeout length is defined in base class
            SerialConnectionException: If serial connection to the RN2483 LoRa module times out
        """
        print("Receiving battery...")
        received_bytes = self.receive_until(self._FINISH_BAT_TRANS)

        print("Writing file...", end='')
        with open(self.__BAT_FILE, "a") as f:
            f.write(str(decode_float(received_bytes)))
            f.write('\n')
        print("Done!")

    def start_receiving(self):
        """
        Receive transmission(s)
        Raises:
            LoraRxTimeoutException: If receiving times out. Timeout length is defined in base class
            SerialConnectionException: If serial connection to the RN2483 LoRa module times out
        """
        lora = self.init_lora()

        if lora:
            while ThreeWayHandshake(lora).accept_conn():
                message = self.lora.recv_message(self._RX_TIMEOUT).message

                if message == self._START_IMG_TRANS:
                    self.receive_image()
                    print("Now uploading the picture to GDrive")
                    self.gdrive.upload_from_disk(self.__RCVD_IMG)
                    print("Done.")
                    self.open_image()

                elif message == self._START_BAT_TRANS:
                    self.receive_battery()
                    print("Now uploading battery to GDrive")
                    self.gdrive.overwrite_from_disk(self.__BAT_FILE)
                    print("Done")

            print("3-way handshake failed. Terminating listening")
            self.close_serial_conn()


def main():
    BasestationReceiver().start_receiving()


if __name__ == '__main__':
    main()
