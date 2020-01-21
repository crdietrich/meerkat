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

def dev_clean():
    """Clean out files in current directory created during development"""
    clean_files("csv", True)
    clean_files("jsontxt", True)

def ls():
    import os
    return os.listdir()
