class SequenceNr:
    """A sequence number for a network connection
    Attributes:
        nr: Current sequence number
        n_bytes: Number of bytes used for the sequence number
    """
    def __init__(self, initial_value: int = 0):
        self.nr = initial_value
        self.n_bytes = 1

    def __str__(self):
        return self.as_hex()

    def __eq__(self, other):
        if (isinstance(other, SequenceNr)):
            return other.nr == self.nr
        else:
            return NotImplemented

    def increase(self):
        self.set(self.nr + 1)

    def set(self, nr: int):
        # Can convert to a bitwise operation if speed is needed:
        self.nr = nr % (256**self.n_bytes)

    def as_hex(self) -> str:
        """Get the current sequence number as a zero-padded hexadecimal"""
        return "{:X}".format(self.nr).zfill(self.n_bytes * 2)

    def from_hex(hex_code: str):
        try:
            return SequenceNr(int(hex_code, 16))
        except ValueError:
            print(f"Error setting sequence number from hex code '{hex_code}'\n")
            return SequenceNr(0)

    def from_bytes(b: bytes):
        return SequenceNr.from_hex(b.hex())

    def as_bytes(self) -> bytes:
        """Get the current sequence number as a byte sequence"""
        return bytes.fromhex(self.as_hex())
