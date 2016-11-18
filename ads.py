"""ADS1x15 I2C ADC for Micropython/Meerkat
Author: Colin Dietrich 2016

TODO: set instance/chip attributes, regular polling method
"""

from pyb import I2C
from base import REG


i2c = I2C(1, I2C.MASTER, baudrate=100000)

def scan_I2C():
    found_address = i2c.scan()
    print('Found I2C devices at:', found_address)

# Each portion of command is 16 bits = 2 bytes
# from firmware version tutorial in application note

device_address = 0x48

def combine(msb, lsb):
    return (msb << 8) | (lsb >> 8)

# this works
def config(verbose=False):
    i2c.send(0x01, 0x48)
    r = i2c.recv(2, 0x48)
    # function code, byte count, msb, lsb
    #v = combine(r[2], r[3])
    if verbose:
        print('ADS replied:', r)
        #print('ADS firmware: v', v)
    return r

def read():
    i2c.send(0x00, 0x48)
    r = i2c.recv(2, 0x48)
    # function code, byte count, msb, lsb
    #v = combine(r[2], r[3])
    print('ADS replied:', r)
    return r

    
class REGISTERS():
    def __init__(self):
    
        
        self.conversion_addr     = 0x00
        self.config_addr         = 0x01
        self.low_threshold_addr  = 0x02
        self.high_threshold_addr = 0x03
        
        self.config = REG(16)
        
        self.comp_que = 3  # 0b11
        self.comp_que_bits = [0,1]
        
    def set_comp_que(self, x):
        """Disable or set the number of conversions before a ALERT/RDY pin
        is set high
        
        Parameters
        ----------
        x : str, number of conversions '1', '2', '4' or 'off'        
        """
        
        _conv = {'1': '00', '2': '01', '3': '02', 'off': '11'}
        bits = _conv[x]
        for b in bits:
            self.config.apply(b)
        
    
class BASE():
    def __init__(self, i2c_bus):
    
        self.i2c = i2c_bus
    
        self.i2c_address = 0x48
        self.pointer_register = 0x00

        self.register = REGISTERS()
        
        # questionable it needed
        self.os_single = 0x8000
        self.mux_offset = 12

    def read(self, register):
        self.i2c.send(register, self.i2c_address)
        r = self.i2c.recv(2, self.i2c_address)
        # function code, byte count, msb, lsb
        #v = combine(r[2], r[3])
        return r
    
    def config_get(self):
        r = self.read(self.register.config)
        return r
    
    def config_set(self):
        pass

class OS():
    """Operational State"""
    def __init__(self):
        self.state = None
        
class GAIN():
    """Programmable Gain Amplifier"""
    def __init__(self):
        self.x2_3   = 0x0000
        self.x1     = 0x0200
        self.x2     = 0x0400
        self.x4     = 0x0600
        self.x8     = 0x0800
        self.x16    = 0x0A00


class MODE():
    def __init__(self):
        self.state = 0x00

class RATE():
    """Data Rate, in samples per second (SPS)"""
    def __init__(self):
        self.sps_8 =    0x00
        self.sps_16 =   0x01
        self.sps_32 =   0x02
        self.sps_64 =   0x03
        self.sps_128 =  0x04  # default
        self.sps_250 =  0x05
        self.sps_475 =  0x06
        self.sps_880 =  0x07
        
class TEMP():
    def __init__(self):
        self.temp