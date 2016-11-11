"""ADS1x15 I2C ADC for Micropython/Meerkat
Author: Colin Dietrich 2016

TODO: set instance/chip attributes, regular polling method
"""

from pyb import I2C
i2c = I2C(1, I2C.MASTER, baudrate=10000)

def scan_I2C():
    found_address = i2c.scan()
    print('Found I2C devices at:', found_address)

# Each portion of command is 16 bits = 2 bytes
# from firmware version tutorial in application note

device_address = 0x48

def combine(msb, lsb):
    return (msb << 8) | (lsb >> 8)

# this works
def test(verbose=False):
    i2c.send(0x01, 0x48)
    r = i2c.recv(2, 0x48)
    # function code, byte count, msb, lsb
    #v = combine(r[2], r[3])
    if verbose:
        print('ADS replied:', r)
        print('ADS firmware: v', v)
    return v


class BASE():
    def __init__(self):
        self.default_i2c_address = 0x48
        self.pointer_register = 0x00

        # questionable it needed
        self.os_single = 0x8000
        self.mux_offset = 12

class REGISTERS():
    def __init__(self):
        self.conversion     = 0x00
        self.config         = 0x01
        self.low_threshold  = 0x02
        self.high_threshold = 0x03

class OS():
    """Operational State"""
    def __init__(self):
        self.state = None
        
class GAIN():
    """Programmable Gain Amplifier"""
    def __init__(self, i2c_bus):
        
        self.i2c = i2c_bus
        self.state  = None
        self.x2_3   = self.v6_144 = 0x0000  # +/- 6.144 v
        self.x1     = self.v4_096 = 0x0200  # +/- 4.096 v
        self.x2     = self.v2_048 = 0x0400  # +/- 2.048 v = default
        self.x4     = self.v1_024 = 0x0600  # +/- 1.024 v
        self.x8     = self.v0_512 = 0x0800  # +/- 0.512 v
        self.x16    = self.v0_256 = 0x0A00  # +/- 0.256 v

    def set(self):
        self.i2c.send()
                    
        

class MODE():
    def __init__(self):
        self.state = 0x00

class RATE():
    """Data Rate, in samples per second (SPS)
        Different between models, move attributes to chip specific class"""
    def __init__(self):
        self.sps_8 =    0x00
        self.sps_16 =   0x01
        self.sps_32 =   0x02
        self.sps_64 =   0x03
        self.sps_128 =  0x04  # default
        self.sps_250 =  0x05
        self.sps_475 =  0x06
        self.sps_880 =  0x07
        
class GAIN():
    def __init__(self):
        self.temp