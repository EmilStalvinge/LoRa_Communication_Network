#!/usr/bin/env python3

import csv
from time import time
from lora_reception_tester import LoraReceptionTester
from lora.exceptions import LoraRxTimeoutException


class Receiver(LoraReceptionTester):
    """
    Receiver class, subclass of LoraTransmission
    Date: 29/02/2020
    """

    __CSV_FILE = 'receiver_data.csv'
    __COL_ZERO = 'Packet'
    __COL_ONE = 'Bit Errors'
    __COL_TWO = 'Radio Errors'
    __COL_THREE = 'SNR'
    __COL_FOUR = 'Bits/s'
    __WINDOW_SIZE = 5

    def __init__(self):
        """
        Class initializer
        """
        super().__init__()

    def count_bit_errors(self, pckt_msg: bytes):
        """
        Count number bit differences between 2 byte sequences
        :param pckt_msg: message from a received packet
        :return: bit error count
        """
        return bin(int.from_bytes(pckt_msg, 'big') ^ int.from_bytes(self.expctd_msg(), 'big')).count('1')

    def init_receiving(self):
        """
        Initialize LoRa data transmission receiving and recording
        """
        self.init_lora()

        with open(self.__CSV_FILE, mode="w") as f:
            writer = csv.writer(f)
            writer.writerow([self.__COL_ONE,
                             self.__COL_TWO,
                             self.__COL_THREE,
                             self.__COL_FOUR])

        print("{:9}{:12}{:14}{:8}{}".format(self.__COL_ZERO,
                                            self.__COL_ONE,
                                            self.__COL_TWO,
                                            self.__COL_THREE,
                                            self.__COL_FOUR))

    def start_receiving(self):
        """
        Start LoRa transmission receiving and recording
        """
        radio_error_count = bit_error_count = packet_count = 0

        data_rates = []
        i = 0
        while True:
            t_start = time()
            try:
                packet = self.lora.recv_message()
            except LoraRxTimeoutException as e:
                print(e)
                continue
            t_send = time() - t_start

            dr = int(8 * len(packet.message) / t_send)
            if len(data_rates) < self.__WINDOW_SIZE:
                data_rates.append(dr)
            else:
                data_rates[i] = dr

            packet_count += 1
            bit_error_count += self.count_bit_errors(packet.message)
            radio_error_count += packet.error_count
            avg_data_rate = sum(data_rates) // len(data_rates)

            with open(self.__CSV_FILE, mode="w") as f:
                writer = csv.writer(f)
                writer.writerow([packet_count,
                                 bit_error_count,
                                 radio_error_count,
                                 packet.snr,
                                 avg_data_rate])

            s = "{:<9}{:<12}{:<14}{:<10}{}".format(packet_count,
                                                   bit_error_count,
                                                   radio_error_count,
                                                   packet.snr,
                                                   avg_data_rate)
            print(s, end="\r")

            i = (i + 1) % self.__WINDOW_SIZE


def main():
    rcvr = Receiver()
    rcvr.init_receiving()
    rcvr.start_receiving()


if __name__ == '__main__':
    main()
