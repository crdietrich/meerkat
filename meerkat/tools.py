"""Tools for I2C devices
2019 Colin Dietrich"""

def toI2C(n):
    """Print read and write address bytes formatted as
    they will be transmitted over the I2C bus"""
    print("{} 0x{:02x} I2C Address ".format(n, n))
    print("==================")
    wb = n << 1
    print("{} 0x{:02x} Address Write".format(wb, wb))
    rb = (n << 1) | 0b000001
    print("{} 0x{:02x} Address Read".format(rb, rb))

def bprint(v, n=16):
    """Print binary value with index numbers below in two rows
    Example register 14 = 1
                          4
    """
    print("HEX value:", hex(v))
    b = bin(v)[2:]
    print(b.zfill(n))
    m = [str(x).zfill(2) for x in reversed(range(n))]
    print("".join([x[0] for x in m]))
    print("".join([x[1] for x in m]))
