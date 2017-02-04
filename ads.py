"""ADS1x15 I2C ADC for Micropython/Meerkat
Author: Colin Dietrich 2016
"""

import ustruct
from meerkat.base import twos_complement, bit_set, bit_clear, bit_toggle


class Core:
    def __init__(self, i2c_bus, i2c_addr=0x48):

        # attributes for rpel use
        self.twos_complement = twos_complement
        self.bit_set = bit_set
        self.bit_clear = bit_clear
        self.bit_toggle = bit_toggle
        
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

        # voltage measurement
        self.pga_float = 2.048
        self.volts = 0

        # attribute converters for print
        self.comp_que_bin_to_str = {0b00: 'Assert after 1', 
                                    0b01: 'Assert after 2',
                                    0b10: 'Assert after 3',
                                    0b11: 'Disabled'}
                                    
        self.comp_lat_bin_to_str = {0: 'Non-latching', 1: 'Latching'}
        self.comp_pol_int_to_str = {0: 'Low', 1: 'High'}
        self.comp_mode_bin_to_str = {0: 'Traditional', 1: 'Window'}
        self.dr_int_to_sps = {0: 8, 1: 16, 2:32, 3:64, 4:128, 5:250, 6:475, 7:850}
        self.mode_int_to_str = {0: 'Continuous', 1: 'Single Shot'}
        self.mux_int_to_str = {0: 'p:0 n:1', 1: 'p:0 n:3', 2: 'p:1 n:3', 3: 'p:2 n:3',
                               4: 'p:0 n:g', 5: 'p:1 n:g', 6: 'p:2 n:g', 7: 'p:3 n:g'}
        
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
        Default value on power up from chip is 0
        """
        self.conversion = self.read_register(0x0)

    def single_shot(self):
        """Write 0x1 to bit 15 of the configuration register to initialize
        a single shot conversion.  The configuration register must be read at
        least once to get the current configuration, otherwise the chip default is used.
        Chip clears bit on completion of ADC conversion.
        """
        _s = bytearray([1, (self.config >> 8) & 0xff, self.config & 0xff])
        self.i2c.send(_s, addr=self.i2c_addr)
        self.get_conversion()

    def voltage(self):
        """Calculate the voltage measured by the chip based on conversion register
        and configuration register values
        TODO: return or set attribute?
        """
        self.single_shot()
        _x = twos_complement(self.conversion, 16)
        _y = _x * (self.pga_float / 2**15)
        self.volts = _y
        return self.volts
        
    def test(self):
        self.print_attributes()
        self.voltage()
        print('voltage measured:', self.volts)

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
        self.update_attributes()
        print('ADS11x5 Configuration Attributes')
        print('--------------------------------')
        print('PGA Range: +/-', self.pga_float, 'Volts')
        print('Mode:', self.mode_int_to_str[self.mode])
        print('Data Rate:', self.dr_int_to_sps[self.dr], 'SPS')
        print('Input Multiplexer:', self.mux_int_to_str[self.mux])
        print('Comparator:')
        print(' Queue:', self.comp_que_bin_to_str[self.comp_que])
        print(' Latching:', self.comp_lat_bin_to_str[self.comp_lat])
        print(' Polarity: Active', self.comp_pol_int_to_str[self.comp_pol])
        print(' Mode:', self.comp_mode_bin_to_str[self.comp_mode])
        
    def set_pga(self, x):
        """Set programmable gain amplifier range.
        
        Parameters
        ----------
        x : str, +/- voltage range value.  Supported values:
            '6.144', '4.096', '2.048', '1.024', '0.512', '0.256'
        """
        
        _bit = [11, 10, 9]
        _pga = {'6.144': '000', '4.096': '001', '2.048': '010', 
                '1.024': '011', '0.512': '100', '0.256': '101'}[x]
        _pga = [{'0': False, '1':True}[_] for _ in _pga]
        
        for _n in [0, 1, 2]:
            self.config = bit_toggle(self.config, _bit[_n], _pga[_n])
            
        self.pga_float = float(x)
                
    def set_mux(self, x):
        """Set multiplexer pin pair, ADS1115 only.
        
        Parameters
        ----------
        x : str, positive and negative pin combination.  Based on:
            AIN pins '1', '2', '3', '4' and Ground pin 'G'
            i.e. for AIN_pos = AIN0 and AIN_neg = Ground, x = '1G'
        """
        _reg = [14, 13, 12]
        _mux = {'01': '000', '03': '001', '13': '010', '23': '011',
                 '0G': '100', '1G': '101', '2G': '110', '3G': '111'}[x]
        _mux = [{'0': False, '1':True}[_] for _ in _mux]
        
        for _n in [0, 1, 2]:
            self.config = bit_toggle(self.config, _reg[_n], _mux[_n])
        
    def set_comp_que(self, x):
        """Disable or set the number of conversions before a ALERT/RDY pin
        is set high
        
        Parameters
        ----------
        x : str, number of conversions '1', '2', '4' or 'off'
        """
        _reg = [1, 0]
        _que = {'1': '00', '2': '01', '3': '10', 'off': '11'}[x]
        _que = [{'0': False, '1':True}[_] for _ in _que]
        
        for _n in [0, 1]:
            self.config = bit_toggle(self.config, _reg[_n], _que[_n])
        
    def set_comp_latching(self, x):
        """Set whether the ALERT/RDY pin latches or clears when conversions
        are within the margins of the upper and lower thresholds

        Only available in ADS1114 and ADS1115, default is 0 = non-latching

        Parameters
        ----------
        x : str, 'on' or 'off'
        """
        self.bit_toggle(self.config, 2,
                        {'off': False, 'on': True}[x])

    def set_comp_polarity(self, x):
        """Set polarity of ALERT/RDY pin when active.
        No function in ADS1113, changes bit 3

        Parameters
        ----------
        x : str, 'high' or 'low'
        """
        self.bit_toggle(self.config, 3,
                        {'low': False, 'high': True}[x])

    def set_comp_mode(self, x):
        """Set comparator mode
        ADS1114 and ADS1115 only, changes bit 4

        x : str, 'trad' or 'window'
        """
        self.bit_toggle(self.config, 4,
                        {'trad': False, 'window': True}[x])

    def set_data_rate(self, x):
        """Set data rate of sampling
        Changes bits [7:5]
        
        Parameters
        ----------
        x : int, samples per second.
            Allowed values: 8, 16, 32, 64,
            128, 250, 475, 850
        """
        _reg = [7, 6, 5]
        _sps = {8: '000', 16: '001', 32: '010', 64: '011',
                128: '100', 250: '101', 475: '110', 860: '111'}[x]
        _sps = [{'0': False, '1':True}[_] for _ in _sps]
        
        for _n in [0, 1, 2]:
            self.config = bit_toggle(self.config, _reg[_n], _sps[_n])
        
    def set_mode(self, x):
        """Set operating mode to either single or continuous.
        
        Parameters
        ----------
        x: str, either 'single' or 'continuous'
        """
        self.bit_toggle(self.config, 8,
                        {'continuous': False, 'single': True}[x])
        
    def set_os(self):
        """Set the operational status
        As this has only one use in write mode, sets bit 15 to True.
        Chip will automatically clear it.  Bit 15 = True is also the
        power on default - it should be sufficient to read the configuration
        register once and use that bit position for all read commands.
        """
        self.bit_toggle(self.config, 15, True)
