class TxStats:
    """Stats of a message sent over the radio
    Attributes:
        packet_count: Number of packets sent
        tx_count: Number of performed transmissions
        snr: Average signal to noise ratio of the received ACKs
    """
    def __init__(self, packet_count: int, tx_count: int, snr: int):
        self.packet_count = packet_count
        self.tx_count = tx_count
        self.snr = snr

    def loss_count(self):
        """Number of packets lost during message transmissions"""
        return self.tx_count - self.packet_count
