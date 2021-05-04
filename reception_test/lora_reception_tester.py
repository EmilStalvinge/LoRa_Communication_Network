#!/usr/bin/env python3

from random import getrandbits, seed
import sys
sys.path.append('../pi')
from lora import get_serial_connection, LoraConnection


class LoraReceptionTester:
    """
    Super class for Lora reception tests
    Date: 29/02/2020
    """

    __FIXED_DATA = b'\xFF'  # stop on "FF" so sender can say it is done

    __LORA_SRL_PWR = 14
    __LORA_SRL_SF = "sf7"
    __LORA_SRL_FREQ = 863000000
    __LORA_DEBUG_PCKTS = False
    __LORA_DEBUG_ACK_NACK = False

    _BYTES_PER_PCKT = 254  # 1-254 for LoRa, 1-63 for FSK (if 1 byte seq num)
    _RNDM_DAT = False
    _PCKT_DELAY = 0  # Delay between each of our packets

    def __init__(self):
        """
        Class initializer
        """
        if self._RNDM_DAT:
            seed(0)  # seed is the same so that data is verified by receiver
        self.fxd_bytes = self.__FIXED_DATA * self._BYTES_PER_PCKT
        self.rndm_bytes = bytes(getrandbits(8) for i in range(self._BYTES_PER_PCKT))
        self.lora = None

    def init_lora(self):
        """
        Initialize LoRa
        """
        ser = get_serial_connection()

        if not ser:
            exit(-1)
        self.lora = LoraConnection(ser,
                                   power=self.__LORA_SRL_PWR,
                                   freq=self.__LORA_SRL_FREQ,
                                   sf=self.__LORA_SRL_SF,
                                   debug_packets=self.__LORA_DEBUG_PCKTS,
                                   debug_ack_nack=self.__LORA_DEBUG_ACK_NACK)
        print("LoRa module connected.\n")

    def expctd_msg(self):
        """
        Gets a type of bytes sequence determined by whether data is random or not
        :return: random byte sequence if data is random, fixed byte sequence otherwise
        """
        return self.rndm_bytes if self._RNDM_DAT else self.fxd_bytes
