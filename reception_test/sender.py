#!/usr/bin/env python3

from time import sleep, time
from lora_reception_tester import LoraReceptionTester
from lora import TxStats
from lora.exceptions import LoraTxTimeoutException


class Sender(LoraReceptionTester):
    """
    Sender class, subclass of LoraReceptionTester
    Date: 29/02/2020
    """

    __WINDOW_SIZE = 5
    __TX_TRIES = 3

    __COL_ZERO = 'Packets'
    __COL_ONE = 'Lost packets'
    __COL_TWO = 'Avg. lost packets'
    __COL_THREE = 'Avg. SNR'
    __COL_FOUR = 'Bits/s'

    def __init__(self):
        """
        Class initializer
        """
        super().__init__()

    def init_sending(self):
        """
        Initialize LoRa data transmitting
        """
        self.init_lora()
        print("Sending packets of {} Bytes{}.".format(self._BYTES_PER_PCKT,
                                                      ' random data'
                                                      if self._RNDM_DAT
                                                      else ''))
        print(f"{self._PCKT_DELAY}s delay between each packet.")

    def start_sending(self):
        """
        Start LoRa transmissions
        """
        retx_counts = []
        snr_values = []
        data_rates = []
        packet_count = loss_count = i = 0
        print(f"Averages are of last {self.__WINDOW_SIZE} packets\n")
        print("{:10}{:15}{:20}{:<10}{}".format(self.__COL_ZERO,
                                               self.__COL_ONE,
                                               self.__COL_TWO,
                                               self.__COL_THREE,
                                               self.__COL_FOUR))

        while True:
            t_start = time()
            try:
                msg_stats = self.lora.send_message(self.expctd_msg(), self.__TX_TRIES)
            except LoraTxTimeoutException:
                msg_stats = TxStats(packet_count=0, tx_count=self.__TX_TRIES, snr=-128)
            t_send = time() - t_start

            packet_count += msg_stats.packet_count
            loss_count += msg_stats.loss_count()
            dr = msg_stats.packet_count * int(8 * self._BYTES_PER_PCKT / t_send)

            if len(retx_counts) < self.__WINDOW_SIZE:
                retx_counts.append(msg_stats.loss_count())
                snr_values.append(msg_stats.snr)
                data_rates.append(dr)
            else:
                retx_counts[i] = msg_stats.loss_count()
                snr_values[i] = msg_stats.snr
                data_rates[i] = dr

            avg_retx = round(sum(retx_counts) / len(retx_counts), 3)
            avg_snr = round(sum(snr_values) / len(snr_values), 3)
            avg_data_rate = sum(data_rates) // len(data_rates)
            print(
                "{:<10}{:<15}{:<20}{:<10}{}".format(packet_count,
                                                    loss_count,
                                                    avg_retx,
                                                    avg_snr,
                                                    avg_data_rate),
                end="\r")
            sleep(self._PCKT_DELAY)
            i = (i + 1) % self.__WINDOW_SIZE


def main():
    sndr = Sender()
    sndr.init_sending()
    sndr.start_sending()


if __name__ == '__main__':
    main()
