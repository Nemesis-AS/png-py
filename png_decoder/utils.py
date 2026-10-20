import struct


def bytes_to_int(buffer: bytes) -> int:
    return struct.unpack(">I", buffer)[0]


def bytes_to_short(buffer: bytes) -> int:
    return struct.unpack(">H", buffer)[0]


def scale_sample(sample: int, bit_depth: int) -> int:
    match bit_depth:
        case 16:
            return sample >> 8
        case 8:
            return sample
        case _:
            return (sample * 255) // ((1 << bit_depth) - 1)


def paeth_filter(a: int, b: int, c: int) -> int:
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
