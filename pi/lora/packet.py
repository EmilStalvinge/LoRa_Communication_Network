from .sequence_nr import SequenceNr


class Packet:
    """A packet received over the radio
    Attributes:
        seq_nr: The sequence number of the received packet
        message: The message of the received packet
        error_count: The number of radio errors before successfully receiving the packet
        snr: Signal to noise ratio of the received packet
    """
    def __init__(self, seq_nr: SequenceNr, message: bytes, error_count: int, snr: int):
        self.seq_nr = seq_nr
        self.message = message
        self.error_count = error_count
        self.snr = snr
