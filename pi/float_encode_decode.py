import struct


def encode_float(f: float) -> bytes:
    """Encode a float as a byte"""
    return struct.pack("f", f)


def decode_float(b: bytes, decimal_points=3) -> float:
    """Decode encoded bytes into a float
    If an error occurs, returns 0
    """
    try:
        return round(struct.unpack("f", b)[0], decimal_points)
    except struct.error as e:
        print("Error decoding float '{}': {}".format(b, e))
        return 0
