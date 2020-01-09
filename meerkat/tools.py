"""Tools for Raspberry Pi & MicroPython and I2C devices"""

def toI2C(n):
    """Print read and write address bytes formatted as
    they will be transmitted over the I2C bus"""
    print("{} 0x{:02x} I2C Address ".format(n, n))
    print("==================")
    wb = n << 1
    print("{} 0x{:02x} Address Write".format(wb, wb))
    rb = (n << 1) | 0b000001
    print("{} 0x{:02x} Address Read".format(rb, rb))

def bprint(v, n=16, indexes=True, verbose=True):
    """Print binary value with index numbers below in two rows
    Example register 14 = 1
                          4
    """
    if verbose:
        print("HEX value:", hex(v))
        print("Binary value:")
    b = bin(v)[2:]
    print(b.zfill(n))
    if indexes:
        m = [str(x).zfill(2) for x in reversed(range(n))]
        print("".join([x[0] for x in m]))
        print("".join([x[1] for x in m]))

# for MicroPython memory measurement, see
# https://forum.micropython.org/viewtopic.php?t=3499

def ufree_disk():
    """In MicroPython report how much on disk memory is free"""
    import os
    s = os.statvfs('//')
    return ('{0} MB'.format((s[0]*s[3])/1048576))

def ufree(full=False):
    """In MicroPython report how much RAM memory is free and allocated"""
    import gc
    import os
    F = gc.mem_free()
    A = gc.mem_alloc()
    T = F+A
    P = '{0:.2f}%'.format(F/T*100)
    if not full: return P
    else : return ('Total:{0} Free:{1} ({2})'.format(T,F,P))
