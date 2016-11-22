"""ADS1x15 I2C ADC for Micropython/Meerkat
Author: Colin Dietrich 2016

TODO: set instance/chip attributes, regular polling method
"""

from pyb import I2C
from meerkat.base import REG


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

def config_old(verbose=False):
    i2c.send(0x01, 0x48)
    r = i2c.recv(2, 0x48)
    # function code, byte count, msb, lsb
    #v = combine(r[2], r[3])
    if verbose:
        print('ADS replied:', r)
        #print('ADS firmware: v', v)
    return r

def conversion_old():
    i2c.send(0x00, 0x48)
    r = i2c.recv(2, 0x48)
    # function code, byte count, msb, lsb
    #v = combine(r[2], r[3])
    print('ADS replied:', r)
    return r

def base_read(addr):
    i2c.send(addr, 0x48)
    _r = i2c.recv(2, 0x48)
    return _r
    
    
def conversion():
    return base_read(0x0)
    
def config():
    return base_read(0x1)
    
def lo():
    return base_read(0x2)
    
def hi():
    return base_read(0x3)
    

    
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
        self.apply_bits(base=0, bits=_conv[x])
        
    def set_comp_latching(self, x):
        """Set whether the ALERT/RDY pin latches or clears when conversions
        are within the margins of the upper and lower thresholds
        
        Only available in ADS1114 and ADS1115, default is 0 = non-latching
        
        Parameters
        ----------
        x : str, 'on' or 'off'
        """
        
        _conv = {'on': 1, 'off': 0}
        self.config.apply(2, _conv[x])
        
    def set_comp_polarity(self, x):
        """Set polarity of ALERT/RDY pin when active.
        
        No function in ADS1113.
        
        Parameters
        ----------
        x : str, 'high' or 'low'
        """
        
        _conv = {'low': 0, 'high': 1}
        self.config.apply(3, _conv[x])
        
    def set_comp_mode(self, x):
        """Set comparator mode
        
        ADS1114 and ADS1115 only
        
        x : str, 'trad' or 'window'
        """
        
        _conv = {'trad': 0, 'window': 1}
        self.config.apply(4, _conv[x])
        
    def set_data_rate(self, x):
        """Set data rate of sampling
        
        Parameters
        ----------
        x : str, samples per second.
            Allowed values: '8', '16', '32', '64',
            '128', '250', '475', '850'
        """
        
        _conv = {'8': '000', '16': '001', '32': '010', '64': '011',
            '128': '100', '250': '101', '475': '110', '850': '111'}
        self.apply_bits(base=5, bits=_conv[x])
        
    def set_mode(self, x):
        """Set operating mode to either single or continuous.
        
        Parameters
        ----------
        x: str, either 'single' (default) or 'continuous'
        """
        
        _conv = {'continuous': 0, 'single': 1}
        self.config.apply(8, _conv[x])
        
    def set_pga(self, x):
        """Set programmable gain amplifier range.
        
        Parameters
        ----------
        x : str, +/- voltage range value.  Supported values:
            '6.144', '4.096', '2.048', '1.024', '0.512', '0.256'
        """
        
        _conv = {'6.144': '000', '4.096': '001', '2.048': '010',
                 '1.024': '011', '0.512': '100', '0.256': '101'}
        self.apply_bits(base=9, bits=_conv[x])
        
    def set_mux(self, x):
        """Set multiplexer pin pair, ADS1115 only.
        
        Parameters
        ----------
        x : str, positive and negative pin combination.  Based on:
            AIN pins '1', '2', '3', '4' and Ground pin 'G'
            i.e. for AIN_pos = AIN0 and AIN_neg = Ground, x = '1G'
        """
        
        _conv = {'01': '000', '03': '001', '13': '010', '23': '011',
                 '0G': '100', '1G': '101', '2G': '110', '3G': '111'}
        self.apply_bits(base=12, bits=_conv[x])
        
    def get_status(self):
        """Get chip operational status
        
        Returns
        -------
        str, either 'busy or 'idle' defined as: 
            'busy' = device is performing an ADC conversion
            'idle' = device is not currently performing an ADC conversion
        """
        
        _reg = self.get_bits(15, 1)
        _conv = {'0': 'busy', '1': 'idle'}
        return _conv[_reg]
        
    def single_shot(self):
        """Write bit to begin single conversion when in Power-down single-shot mode.
        Bit clears on completion of ADC conversion, read conversion register
        to retrieve ADC result.
        """
        self.mask_true(15)
        
        
class BASE():
    def __init__(self, i2c_bus):
    
        self.i2c = i2c_bus
    
        self.i2c_address = 0x48
        self.pointer_register = 0x00

        self.register = REGISTERS()
        
    def _read(self, register):
        self.i2c.send(register, self.i2c_address)
        r = self.i2c.recv(2, self.i2c_address)
        # function code, byte count, msb, lsb
        #v = combine(r[2], r[3])
        return r
    
    def _write(self, register):
        self.i2c.send(register, addres)
    
    def config_get(self):
        return self.i2c.mem_read(2, self.i2c_address, 1)
    """
    def config_set(self):
        pass
    """
    
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