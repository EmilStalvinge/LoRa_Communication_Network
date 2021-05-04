#!/usr/bin/env python3

import traceback
from sys import path, platform
path.append('..')
from lora import get_serial_connection, LoraConnection


class LoraBase:
    """
    Base class for a Lora connection between base station and a node
    """

    _START_BAT_TRANS = b'\x0F'  # Tells receiver it's about to receive a battery voltage
    _FINISH_BAT_TRANS = b'\xF0'  # Tells receiver the battery voltage transfer is complete
    _START_IMG_TRANS = b'\x00'  # Tells receiver it's about to receive an image
    _FINISH_IMG_TRANS = b'\xFF'  # Tells receiver image transfer is complete
    _SYS_PLTFRM = platform

    _MAX_TX_TRIES = 20  # Max transmit attempts. Used with LoraConnection.send_message
    _RX_TIMEOUT = 10000  # Receive timeout in ms. Used with LoraConnection.recv_message

    __DEBUG_PCKTS = True

    def __init__(self):
        """
        Class initializer
        """
        self.ser = self.lora = None

    def init_lora(self):
        """
        Initializes Lora connection
        :return true if lora initialized, false otherwise
        """
        self.ser = get_serial_connection()

        if self.ser:
            try:
                self.lora = LoraConnection(self.ser,
                                           debug_packets=self.__DEBUG_PCKTS)
                return self.lora
            except Exception as e:
                traceback.print_tb(e.__traceback__)
                print(e)
                return False

    def close_serial_conn(self):
        """
        Closes serial connection
        """
        self.ser.close()
