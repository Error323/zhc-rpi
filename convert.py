def u16(x):
    """
    Converts 2 bytes to unsigned int
    @param x, the 2 bytes
    """
    return x


def s16(x):
    """
    Converts 2 bytes to signed int
    @param x, the 2 bytes
    """
    if x&0x8000:
        return -(0x10000 - x)
    else:
        return x


def f88(x):
    """
    Converts fixed point 8.8 to float
    @param x, the 2 bytes
    """
    if x&0x8000:
        return round(-(0x10000 - x) / 256.0, 2)
    else:
        return round(x / 256.0, 2)
