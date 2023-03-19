"""Tools for Raspberry Pi & MicroPython and I2C devices

To scan the I2C bus,
On Raspberry Pi:
    $ i2cdetect -y 1
On MicroPython:
>>> from machine import I2C
>>> i2c = I2C(0, I2C.MASTER)
>>> i2c.scan()

On CircuitPython:
>>> import board
then
>>> i2c = board.I2C()
or if it's a STEMMA connector:
>>> i2c = board.STEMMA_I2C()
then scan with
>>> i2c.scan()
"""

def i2c_scan(bus_n=0, **kwargs):
    try: 
        from machine import I2C
        i2c = I2C(bus_n, I2C.MASTER)
        return i2c.scan()
    except:
        pass

    try:
        from machine import i2c
        i2c = I2C(bus_n, **kwargs)
        return i2c.scan()
    except:
        pass


    def _circuit_python_scan(i2c_instance):
        while not i2c_instance.try_lock():
            pass

        try:
            while True:
                print(
                    "I2C addresses found:",
                    [hex(device_address) for device_address in i2c_instance.scan()],
                )
                time.sleep(2)

        finally:  # unlock the i2c bus when ctrl-c'ing out of the loop
            i2c_instance.unlock()

    try:
        from board import I2C
        _circuit_python_scan(I2C())
    except:
        pass

    try:
        from board import STEMMA_I2C
        _circuit_python_scan(STEMMA_I2C())
    except:
        pass

def toI2C(n):
    """Print read and write address bytes formatted as
    they will be transmitted over the I2C bus"""
    print("{} 0x{:02x} I2C Address ".format(n, n))
    print("==================")
    wb = n << 1
    print("{} 0x{:02x} Address Write".format(wb, wb))
    rb = (n << 1) | 0b000001
    print("{} 0x{:02x} Address Read".format(rb, rb))

def left_fill(s, n, x="0"):
    """Cross platform string left fill method, defaults to zero filling.

    Parameters
    ----------
    s : str, string to left pad
    n : int, number of total places to pad to
    x : str, optional, character to fill, defaults to "0"
    """
    sl = len(s)
    zn = n - sl
    if zn > 0:
        return zn*"0" + s
    else:
        return s

def bprint(v, n=16, indexes=True, verbose=True):
    """Print binary value, optionally with index numbers below in two rows
    Example register 14 = 1
                          4

    Parameters
    ----------
    v : int or hex, value to string print
    b : int, number of bytes in representation
    indexes : bool, print indexes below binary string representation
    verbose : bool, print hex and int representationss
    """
    if verbose:
        print("HEX value:", hex(v))
        print("Integer value:", int(v))
        print("Binary value & indexes:")
    b = bin(v)[2:]
    print(left_fill(b, n))
    if indexes:
        m = [left_fill(str(x), 2) for x in reversed(range(n))]
        print("".join([x[0] for x in m]))
        print("".join([x[1] for x in m]))

# for MicroPython memory measurement, see
# https://forum.micropython.org/viewtopic.php?t=3499

def ufree_disk():
    """In MicroPython report how much on disk memory is free"""
    import os
    # note: this would work on PyCom devices but not implemented
    fs_stat = os.statvfs('//')
    fs_size = fs_stat[0] * fs_stat[2]
    fs_free = fs_stat[0] * fs_stat[3]
    fs_per = fs_free / fs_size
    return("Total: {:,} Free: {:,} ({0:.2f}%)".format(fs_size, fs_free, fs_per))


def ufree(verbose=False):
    """In MicroPython report how much RAM memory is free and allocated"""
    import gc
    import os
    F = gc.mem_free()
    A = gc.mem_alloc()
    T = F+A
    P = '{0:.2f}%'.format(F/T*100)
    if not verbose:
        return P
    return ('Total: {} Free: {} ({})'.format(T ,F, P))

def clean_files(ftype, remove=False):
    """Remove files from the current directory

    Parameters
    ----------
    ftype : str, file extension or unique string in filename to find
    remove : bool, remove files if True, return list of files if False
    """
    import os
    files = os.listdir()
    found_files = [f for f in files if ftype in f]
    if remove:
        for ff in found_files:
            os.remove(ff)
            print("Removed {}".format(ff))
    else:
        return found_files

def crc(line):
    """Calculate the cyclic redundancy check (CRC) for a string

    Parameters
    ----------
    line : str, characters to calculate crc
    Returns
    -------
    crc : str, in hex notation
    """
    crc = ord(line[0:1])
    for n in range(1, len(line)-1):
        crc = crc ^ ord(line[n:n+1])
    return '%X' % crc

def dev_clean():
    """Clean out files in current directory created during development"""
    clean_files("csv", True)
    clean_files("jsontxt", True)

def ls():
    import os
    return os.listdir()
