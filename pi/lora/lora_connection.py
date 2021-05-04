from time import sleep

from . import LoraSerial
from .sequence_nr import SequenceNr
from .tx_stats import TxStats
from .packet import Packet
from .tcp_handshake import ThreeWayHandshake
from .exceptions import LoraRxTimeoutException, LoraTxTimeoutException, LoraRxRadioException


class LoraConnection(LoraSerial):
    """A stateful connection over LoRa, akin to TCP
    Args:
        debug_packets: Whether to print packets being sent/received.
        debug_ack_nack: Whether to print NACKs and missed ACKs

    Attributes:
        sender_seq_nr: Sequence number of next packet to send
        recv_seq_nr: Sequence number of expected next packet to be received
        debug_packets: Whether to print all incoming and outgoing LoRa traffic
        debug_ack_nack: Whether to print NACKs and missed ACKs
    """

    ACK = b'\xff\xff'   # Message sent as 'ACK'
    NACK = b'\x00\x00'  # Message sent as 'NACK'

    PAYLOAD_BYTES = 255
    ACK_NACK_DELAY = 25  # Milliseconds of time to wait before sending an ACK, to give sender time to start listening
    ACK_TIMEOUT = 500  # ms receive timeout for LoRa ACK after sending a packet

    def __init__(self, *args, debug_packets: bool = False, debug_ack_nack: bool = False, **kwargs):
        super().__init__(*args, **kwargs)

        self.sender_seq_nr = SequenceNr()
        self.recv_seq_nr = SequenceNr()
        self.debug_packets = debug_packets
        self.debug_ack_nack = debug_ack_nack

    def recv_message(self, timeout_ms: int = 5000) -> Packet:
        """ Listen for a radio message.
        Returns:
            A Packet instance containing message etc.
        Raises:
            LoraRxTimeoutException: If no packet is received within timeout_ms milliseconds
            SerialConnectionException: If any serial response times out
        """
        error_count = 0
        resp = None
        while not resp:
            try:
                resp = self._recv_single_packet(timeout_ms)
            except LoraRxRadioException:
                sleep(self.ACK_NACK_DELAY / 1000)
                self._send_single_packet(self.recv_seq_nr, self.NACK)
                error_count += 1
        seq_nr, message = resp

        previous_seq_nr = SequenceNr(self.recv_seq_nr.nr - 1)
        if seq_nr != previous_seq_nr:
            packet = Packet(seq_nr, message, error_count, self.snr())

            sleep(self.ACK_NACK_DELAY / 1000)
            self._send_single_packet(seq_nr, self.ACK)

            self.recv_seq_nr = seq_nr
            self.recv_seq_nr.increase()

            return packet
        # If we received the same packet as before, our ACK was probably lost
        else:
            if self.debug_ack_nack:
                print("ACK not received by sender. Retransmitting.")
            sleep(self.ACK_NACK_DELAY / 1000)
            self._send_single_packet(previous_seq_nr, self.ACK)

            # Still want to receive a packet, so we need to go again
            return self.recv_message(timeout_ms)

    def send_message(self, message: bytes, max_tries: int = 5, packet_delay: float = 0.0) -> TxStats:
        """ Send a message over radio.
        Args:
            message: A byte sequence of any length.
            packet_delay: Delay between each packet, in seconds
            max_tries: Number of times to at most try to send each packet
        Raises:
            LoraTxTimeoutException: If any packet fails to be ACKed withing max_tries attempts.
            SerialConnectionException: If any serial response times out
        Returns a collection of stats for the transmitted packets
        """
        data_bytes = self.PAYLOAD_BYTES - self.sender_seq_nr.n_bytes

        seg_start = 0
        seg_end = min(seg_start + data_bytes, len(message))

        tx_total = 0
        snr_total = 0
        packet_count = 0
        # Can only transmit a set amount of bytes per command
        while (seg_start < seg_end):
            self._send_single_packet(self.sender_seq_nr, message[seg_start:seg_end])
            packet_tx_tries = 1

            while not self._wait_ack_or_nack(self.sender_seq_nr):
                if (self.debug_ack_nack):
                    print("ACK not received from receiver. Retransmitting.")
                self._send_single_packet(self.sender_seq_nr, message[seg_start:seg_end])

                if packet_tx_tries < max_tries:
                    packet_tx_tries += 1
                else:
                    raise LoraTxTimeoutException(packet_tx_tries)

            snr_total += self.snr()
            tx_total += packet_tx_tries
            packet_count += 1

            self.sender_seq_nr.increase()
            sleep(packet_delay)

            seg_start = seg_end
            seg_end = min(seg_start + data_bytes, len(message))

        return TxStats(packet_count, tx_total, snr_total / packet_count)

    def _wait_ack_or_nack(self, expected_seq_nr: SequenceNr):
        """Waits for an ACK or a NACK for the given sequence number
        Args:
            expected_seq_nr: The sequence number to wait for
        Returns:
            True if an ACK was received, or False if a NACK was received or reception timed out.
        Raises:
            SerialConnectionException: If serial connection times out
        """
        try:
            (received_seq_nr, message) = self._recv_single_packet(self.ACK_TIMEOUT)
            return received_seq_nr == expected_seq_nr and message == self.ACK
        except (LoraRxTimeoutException, LoraRxRadioException):
            return False

    def _recv_single_packet(self, timeout_ms: int) -> (SequenceNr, bytes):
        """
        Receive a raw message, without sending any ACK/NACK
        Args:
            timeout_ms: Timeout in milliseconds before the reception should time out.
        Returns:
            The message as (sequence nr, message)
        Raises:
            LoraRxTimeoutException: If nothing is received within the timeout
            LoraRxRadioException: If radio received, but indicated an error in packet
            SerialConnectionException: If serial connection times out
        """
        payload = self.recv_raw(timeout_ms)
        seq_nr, message = SequenceNr.from_bytes(payload[:self.sender_seq_nr.n_bytes]), payload[self.sender_seq_nr.n_bytes:]

        self._print_packet("<--", seq_nr, message)
        return (seq_nr, message)

    def _send_single_packet(self, seq_nr: SequenceNr, message: bytes):
        """Send a raw message with the given sequence number, without waiting for any ACK/NACK
        Raises:
            SerialConnectionException: If serial connection times out
        """
        self.send_raw(seq_nr.as_bytes() + message)
        self._print_packet("-->", seq_nr, message)

    def _print_packet(self, prefix: str, seq_nr: SequenceNr, message: bytes):
        if self.debug_packets:
            if message == self.ACK:
                message = "ACK"
            elif message == self.NACK:
                message = "NACK"
            print(f"{prefix} (n={seq_nr.as_hex()}) {message}")
