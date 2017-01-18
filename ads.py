"""ADS1x15 I2C ADC for Micropython/Meerkat
Author: Colin Dietrich 2016
"""
import ustruct

from meerkat.base import REG


class Core():
    def __init__(self, i2c_bus, i2c_addr=0x48):
    
        # instance of MicroPython board specific i2c bus
        self.i2c = i2c_bus
    
        # i2c bus address of device, default is 0x48
        self.i2c_addr = i2c_addr
        self.i2c_addr_write = i2c_addr
        self.i2c_addr_read = i2c_addr + 0x01
        
        # self.conversion_addr     = 0x00
        # self.config_addr         = 0x01
        # self.low_threshold_addr  = 0x02
        # self.high_threshold_addr = 0x03
        
        self.config = REG(16)
        self.comp_que = None
        
        self.pga = None
        
        
    def combine(self, b):
        return ustruct.unpack('>H', b)[0]
    
    def base_read(self, reg_addr, i2c_addr=None):
        if i2c_addr is None:
            i2c_addr = self.i2c_addr
        self.i2c.send(reg_addr, i2c_addr)
        _r = self.i2c.recv(2, i2c_addr)
        _r = ustruct.unpack('<H', _r)[0]
        # alternative method, but not MicroPython board portable
        # _r2 = self.i2c.mem_read(2, i2c_addr, reg_addr)
        return _r  # , _r2
    
    def set_config(self):
        
        self.i2c.send()
    
    def get_conversion(self):
        """Read the ADC conversion register""" 
        return self.base_read(0x0)
        
    def get_config(self):
        """Read the configuration register
        
        default is 0x8583 = '0b1000010110000110'
        """
        # _a = self.base_read(0x01)
        # self.config.value = self.config.clean(_a)
        # return self.config.value
        _a = self.base_read(0x01)
        # _a = self.combine(_a)
        self.config.value = _a
        return _a
        
    def get_lo(self):
        """Read the low threshold register
        
        default = 0x8000 = '0b1000000000000000'
        """
        return self.base_read(0x02)
        
    def get_hi(self):
        """Read the high threshold register
        
        default = 0x7FFF = '0b111111111111111'
        """
        return self.base_read(0x03)

    def get_comp_que(self):
        
        _conv = {'00': '1', '01': '2', '02': '3', '11': 'off'}
        
        self.comp_que = _conv[bin(self.config.value)[2:][-2:]]
        
        print(self.comp_que)
        
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
        self.config.apply_bits(base=9, bits=_conv[x])
        
    def get_pga(self):
        """Get the programmable gain amplifier range.
        """
        _conv = {'000': '6.144', '001': '4.096', '010': '2.048',
                 '011': '1.024', '100': '0.512', '101': '0.256'}
        
        
        _bv = bin(self.config.value)
        print("_bv>> ", _bv)
        _sv = _bv[2:][-12:-9]
        print('_sv>> ', _sv)
        self.pga = _conv[_sv]
        print('pga>> ', self.pga)
        print(self.pga)
        
        
        
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
        command = self.config.value ^ self.config.mask[15]
        #self.mask_true(15)
        return command
        
        
class BASE_OLD():
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
    