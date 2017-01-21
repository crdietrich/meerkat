"""ADS1x15 I2C ADC for Micropython/Meerkat
Author: Colin Dietrich 2016
"""
import ustruct
from meerkat.base import twos_complement


class Core:
    def __init__(self, i2c_bus, i2c_addr=0x48):
    
        # instance of MicroPython board specific i2c bus
        self.i2c = i2c_bus
    
        # i2c bus address of device, default is 0x48
        self.i2c_addr = i2c_addr

        # register values and defaults
        self.conversion = 40000  # higher than any conversion result
        self.config = 0x8583     # config, lo and hi values on repower
        self.lo_thresh = 0x8000
        self.hi_thresh = 0x7fff

        # config register attributes and chip defaults
        self.comp_que = 0b11
        self.comp_lat = 0b0
        self.comp_pol = 0b0
        self.comp_mode = 0b0
        self.dr = 0b100
        self.mode = 0b1
        self.pga = 0b010
        self.mux = 0b000
        self.os = None

        # converters for config register attributes
        self.pga_float = [6.144, 4.096, 2.048, 1.024, 0.512, 0.256]
        self.pga_str = [str(_n) for _n in self.pga_float]
        self.pga_binary = [0b000, 0b001, 0b010, 0b011, 0b100, 0b101]
        self.pga_bin_to_str = dict(zip(self.pga_binary, self.pga_str))
        self.pga_bin_to_float = dict(zip(self.pga_binary, self.pga_float))
        self.pga_str_to_bin = dict(zip(self.pga_str, self.pga_binary))

        # as pga, these are TODO
        self.op_bin_to_str = {0: 'busy', 1: 'idle'}
        self.comp_que_bin_to_str = {0b00: '1', 0b01: '2', 0b10: '3', 0b11: 'off'}
        self.comp_lat_bin_to_str = {'on': 1, 'off': 0}
        self.comp_str_to_bin = {'low': 0, 'high': 1}
        self.comp_mode_str_to_bin = {'trad': 0, 'window': 1}
        self.dr_int_to_bin = {'8': '000', '16': '001', '32': '010', '64': '011',
            '128': '100', '250': '101', '475': '110', '850': '111'}
        self.mode_str_to_bin = {'continuous': 0b0, 'single': 0b1}
        self.mux_str_to_bin = {'01': '000', '03': '001', '13': '010', '23': '011',
                 '0G': '100', '1G': '101', '2G': '110', '3G': '111'}

    def read_register(self, reg_addr):
        """Get the values from one registry
        Parameters
        ----------
        reg_addr : hex, address of registry to read

        Returns
        -------
        16 bit registry value
        """

        self.i2c.send(reg_addr, addr=self.i2c_addr)  # send register request (i.e. write 1 144)
        _r = self.i2c.recv(2, addr=self.i2c_addr)    # read two bytes (i.e. read two bytes from 145)
        _r = ustruct.unpack('>H', _r)[0]             # convert to single 16 bit value
        return _r

    def get_conversion(self):
        """Read the ADC conversion register at address 0x00
        Default value from chip is 0
        """
        self.conversion = self.read_register(0x0)

    def single_shot(self):
        """Write 0x1 to bit 15 of the configuration register to initialize
        a single shot conversion.  The configuration register must be read at
        least once to get the current configuration, otherwise the chip default is used.
        Chip clears bit on completion of ADC conversion.
        """
        _s = bytearray([1, self.config & 0xff, (self.config >> 8) & 0xff])
        self.i2c.send(_s, addr=self.i2c_addr)
        self.get_conversion()

    def voltage(self):
        """Calculate the voltage measured by the chip based on conversion register
        and configuration register values
        """
        self.single_shot()
        _x = twos_complement(self.conversion, 16)
        _y = _x * (self.pga_bin_to_float[self.pga] / 2**14)
        print('voltage =', _y)

    def get_config(self):
        """Read the configuration register at address 0x01
        Default value from chip is 0x8583 = 34179 = '0b1000010110000110'
        Specific states extracted with other methods
        """
        self.config = self.read_register(0x01)

    def get_lo(self):
        """Read the low threshold register at address 0x02
        Default value from chip is 0x8000 = 32768 = '0b1000000000000000' = 128 MSB + 0 LSB
        """
        return self.read_register(0x02)

    def get_hi(self):
        """Read the high threshold register at address 0x03
        Default value from chip is 0x7FFF = 32767 = '0b111111111111111'
        """
        return self.read_register(0x03)

    def config_comp_que(self):
        """Comparator queue and disable"""
        self.comp_que = self.config & 0b11

    def config_comp_lat(self):
        """Latching comparator"""
        self.comp_lat = (self.config >> 2) & 0b1

    def config_comp_pol(self):
        """Comparator polarity"""
        self.comp_pol = (self.config >> 3) & 0b1

    def config_comp_mode(self):
        """Comparator mode"""
        self.comp_mode = (self.config >> 4) & 0b1

    def config_dr(self):
        """"Data rate"""
        self.dr = (self.config >> 5) & 0b111

    def config_mode(self):
        """Operating mode"""
        self.mode = (self.config >> 8) & 0b1

    def config_pga(self):
        """"Programmable gain amplifier"""
        self.pga = (self.config >> 9) & 0b111

    def config_mux(self):
        """Multiplexer"""
        self.mux = (self.config >> 12) & 0b111

    def config_os(self):
        """Operational status / Single-shot conversion start"""
        self.os = self.config >> 15

    def update_attributes(self):
        self.config_comp_que()
        self.config_comp_lat()
        self.config_comp_pol()
        self.config_comp_mode()
        self.config_dr()
        self.config_mode()
        self.config_pga()
        self.config_mux()
        self.config_os()

    def print_attributes(self):
        print('ADS11x5 Configuration Attributes')
        print('--------------------------------')
        print('comp que:', self.comp_que)
        print('comp lat:', self.comp_lat)
        print('comp_pol', self.comp_pol)
        print('comp_mode', self.comp_mode)
        print('dr:', self.dr)
        print('mode:', self.mode)
        print('pga range: +/-', self.pga_bin_to_str[self.pga], 'volts')
        print('mux:', self.mux)
        print('os:', self.os)

    def set_comp_que(self, x):
        """Disable or set the number of conversions before a ALERT/RDY pin
        is set high

        Parameters
        ----------
        x : str, number of conversions '1', '2', '4' or 'off'
        """
        pass

    def set_comp_latching(self, x):
        """Set whether the ALERT/RDY pin latches or clears when conversions
        are within the margins of the upper and lower thresholds

        Only available in ADS1114 and ADS1115, default is 0 = non-latching

        Parameters
        ----------
        x : str, 'on' or 'off'
        """
        pass

    def set_comp_polarity(self, x):
        """Set polarity of ALERT/RDY pin when active.

        No function in ADS1113.

        Parameters
        ----------
        x : str, 'high' or 'low'
        """
        pass

    def set_comp_mode(self, x):
        """Set comparator mode

        ADS1114 and ADS1115 only

        x : str, 'trad' or 'window'
        """
        pass

    def set_data_rate(self, x):
        """Set data rate of sampling

        Parameters
        ----------
        x : str, samples per second.
            Allowed values: '8', '16', '32', '64',
            '128', '250', '475', '850'
        """
        pass

    def set_mode(self, x):
        """Set operating mode to either single or continuous.

        Parameters
        ----------
        x: str, either 'single' (default) or 'continuous'
        """
        pass

    def set_pga(self, x):
        """Set programmable gain amplifier range.
        
        Parameters
        ----------
        x : str, +/- voltage range value.  Supported values:
            '6.144', '4.096', '2.048', '1.024', '0.512', '0.256'
        """
        pass
        
    def set_mux(self, x):
        """Set multiplexer pin pair, ADS1115 only.
        
        Parameters
        ----------
        x : str, positive and negative pin combination.  Based on:
            AIN pins '1', '2', '3', '4' and Ground pin 'G'
            i.e. for AIN_pos = AIN0 and AIN_neg = Ground, x = '1G'
        """
        pass

    def set_config(self):
        """Set the configuration register"""
        pass
