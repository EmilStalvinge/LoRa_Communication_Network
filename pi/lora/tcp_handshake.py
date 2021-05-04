#!/usr/bin/env python3

from struct import pack, unpack
from time import time, sleep
from lora.exceptions import LoraRxTimeoutException, LoraRxRadioException

CHAR_ENCODING = "UTF-8"


class HandShakePacket:
    """
    Packet class for TCP 3-way handshake transmissions
    Date: 06/03/2020
    """

    __MAGIC_NO = 0x645F  # For identifying packet validity
    __DATA_TYPE_SYN = 0  # Distinguishes SYN packet type
    __DATA_TYPE_ACK = 1  # Distinguishes ACK packet type
    __HDR_SUM = 16  # The sum of the bytes of 4 packed integer values
    __FMT = "iiii"  # The format for the byte pack and unpack

    def __init__(self, check_sum=None, magic_no=None, data_type=None, data_len=None, data=None):
        """
        Class constructor
        :param check_sum: Length of byte packet header
        :param magic_no: For identifying a packets validity
        :param data_type: Distinguishes the packet type
        :param data_len: The byte message being sent in the packet
        :param data: Data being transmitted with packet
        """
        self.chk_sum = check_sum  # Length of byte packet header
        self.magic_no = magic_no  # For identifying a packets validity
        self.data_type = data_type  # Distinguishes the packet type
        self.data_len = data_len  # Declares the length of data in the packet
        self.data = data  # Data being transmitted with packet

    def __valid_packet(self):
        """
        Checks if data received is a valid SYN/ACK packet with matching ID
        :return: True if packet has matching magic num and no data, false otherwise
        """
        return self.magic_no == self.__MAGIC_NO

    def valid_ack(self):
        """
        Checks if data received is a valid ACK packet
        :return: True if data type is ACK, false otherwise
        """
        return self.data_type == self.__DATA_TYPE_ACK

    def valid_syn(self):
        """
        Checks if data received is a valid SYN packet
        :return: True if data type is SYN, false otherwise
        """
        return self.data_type == self.__DATA_TYPE_SYN

    def __valid_data(self):
        """
        Checks if data received is equal to the provided data len
        :return: True if data is same size as provided data len, false otherwise
        """
        return self.data_len == len(str(self.data))

    def __valid_check_sum(self):
        """
        Validates the check sum equals the sum of magic num, data type and data len
        :return: True if check sum equals magic num, data type and data len sum, false otherwise
        """
        return self.chk_sum == (self.magic_no + self.data_type + self.data_len)

    def buffer(self, msg_type, msg=b''):
        """
        Converts a SYN/ACK data package into a byte pack for transmitting
        :param msg_type: whether the transmitting message is a SYN or ACK message
        :param msg: The byte message being sent in the packet
        :return: The data converted to a byte pack
        """
        if msg_type:
            self.data_type = self.__DATA_TYPE_ACK
        else:
            self.data_type = self.__DATA_TYPE_SYN
        self.data_len = len(msg)
        self.chk_sum = self.__MAGIC_NO + self.data_type + self.data_len
        return pack(self.__FMT + str(self.data_len) + "s", self.chk_sum,
                    self.__MAGIC_NO, self.data_type, self.data_len, msg)

    def un_buffer(self, msg_type, packet):
        """
        Unpacks received byte pack and converts it to a SYN/ACK data packet
        :param msg_type: whether the expected message is a SYN or ACK message
        :param packet: The received data packet
        :return: an instance for received packet or None if packet invalid
        """
        self.chk_sum, self.magic_no, self.data_type, \
            self.data_len = unpack(self.__FMT, packet[:self.__HDR_SUM])

        if self.__valid_packet() and self.__valid_data() and \
                ((msg_type and self.valid_ack()) or
                 (not msg_type and self.valid_syn())):
            if not self.__valid_check_sum():
                self.data_len = self.chk_sum - \
                                (self.magic_no + self.data_type)
            data = unpack(str(self.data_len) + "s",
                          packet[self.__HDR_SUM:self.data_len +
                                 self.__HDR_SUM])[0].decode(CHAR_ENCODING)
            return HandShakePacket(self.chk_sum, self.magic_no, self.data_type,
                                   self.data_len, eval(data))
        return None


class ThreeWayHandshake:
    """
    Class for managing TCP 3-way handshake transmissions
    Date: 06/03/2020
    """

    __SYN = 4500
    __SYN_ACK = 4501
    __ACK = 4502
    __MAX_TIME = 20  # maximum time attempting to establish connection (s)
    __SLEEP_TIME = 0.2  # the time between each transmission
    __PACK_TIMEOUT = 500  # ms to listen for a packet before timing out

    def __init__(self, lora_conn):  # battery_status=None):
        """
        Class constructor
        """
        self.lora_conn = lora_conn
        self.packet = HandShakePacket()
        # self.battery_status = battery_status
        self.trans_cnt = 0

    def request_conn(self):
        """
        Request establishing a LoRa connection for transmitting data using 3-way handshake
        :return: True if connection established with the server using 3-way handshake, False otherwise
        """
        end_time = time() + self.__MAX_TIME

        while time() < end_time:
            if not self.trans_cnt:
                self.lora_conn.send_raw(self.packet.buffer(0, bytes(str(self.__SYN),
                                                                    encoding=CHAR_ENCODING)))
                self.trans_cnt += 1
            elif self.trans_cnt == 1:
                try:
                    new_pckt = self.packet.un_buffer(1, self.lora_conn.recv_raw(self.__PACK_TIMEOUT))
                except (LoraRxRadioException, LoraRxTimeoutException):
                    new_pckt = None

                if new_pckt and new_pckt.valid_ack():
                    # this is where battery status can be included in the message
                    self.lora_conn.send_raw(self.packet.buffer(1, bytes(str(self.__ACK),
                                                                        encoding=CHAR_ENCODING)))
                    return True
                else:
                    self.trans_cnt -= 1
            sleep(self.__SLEEP_TIME)
        return False

    def accept_conn(self):
        """
        Accept establishing a LoRa connection for transmitting data using 3-way handshake
        :return: True if connection established with the client using 3-way handshake, False otherwise
        """
        end_time = time() + self.__MAX_TIME

        while time() < end_time:
            if not self.trans_cnt:
                try:
                    new_pckt = self.packet.un_buffer(0, self.lora_conn.recv_raw(self.__PACK_TIMEOUT))
                except (LoraRxRadioException, LoraRxTimeoutException):
                    new_pckt = None

                if new_pckt and new_pckt.valid_syn():
                    self.lora_conn.send_raw(self.packet.buffer(1, bytes(str(self.__SYN_ACK),
                                                                        encoding=CHAR_ENCODING)))
                    self.trans_cnt += 1
            elif self.trans_cnt == 1:
                try:
                    new_pckt = self.packet.un_buffer(1, self.lora_conn.recv_raw(self.__PACK_TIMEOUT))
                except (LoraRxRadioException, LoraRxTimeoutException):
                    new_pckt = None

                if new_pckt and new_pckt.valid_ack():
                    return True
                else:
                    self.lora_conn.send_raw(self.packet.buffer(1, bytes(str(self.__SYN_ACK),
                                                                        encoding=CHAR_ENCODING)))
            sleep(self.__SLEEP_TIME)
        return False
