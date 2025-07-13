import struct


def bytes_to_int(buffer: bytes) -> int:
    return struct.unpack(">I", buffer)[0]


def paeth_filter(a, b, c):
    p = a + b - c
    pa = abs(p - a)
    pb = abs(p - b)
    pc = abs(p - c)

    if pa <= pb and pa <= pc:
        return a
    elif pb <= pc:
        return b
    else:
        return c
