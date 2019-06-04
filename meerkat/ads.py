"""ADS1x15 I2C ADC for Micropython/Meerkat
Author: Colin Dietrich 2017
"""

from meerkat.base import I2C, DeviceData, twos_comp_to_dec, time
from meerkat.data import CSVWriter, JSONWriter


# config bit masks
BIT_OS        = 32767
BIT_MUX       = 36863
BIT_PGA       = 61951
BIT_MODE      = 256
BIT_DR        = 224
BIT_COMP_MODE = 16
BIT_COMP_POL  = 8
BIT_COMP_LAT  = 4
BIT_COMP_QUE  = 3


class ADS1115(object):
    def __init__(self, bus_n, bus_addr=0x48, output='csv'):
        """Initialize worker device on i2c bus.

        Parameters
        ----------
        bus_n : int, i2c bus number on Controller
        bus_addr : int, i2c bus number of this Worker device        
        """

        # i2c bus
        self.bus = I2C(bus_n=bus_n, bus_addr=bus_addr)

        # time to wait for conversion to finish
        self.delay = 0.009  # units = seconds

        # register values and defaults
        self.conversion_value = 40000   # higher than any conversion result
        self.config_value     = None    # 0x8583 default
        self.lo_thres_value   = None    # 0x8000 default
        self.hi_thres_value   = None    # 0x7fff default

        self.reg_map = {'conversion': 0b00,
                        'config'    : 0b01,
                        'lo_thresh' : 0b10,
                        'hi_thresh' : 0b11}

        # config register attributes and chip defaults
        self.comp_que_value  = 0b11
        self.comp_lat_value  = 0b0
        self.comp_pol_value  = 0b0
        self.comp_mode_value = 0b0
        self.dr_value        = 0b100
        self.mode_value      = 0b1
        self.pga_value       = 0b010
        self.mux_value       = 0b000
        self.os_value        = 0b0

        # voltage measurement
        self.pga_float = -999
        self.volts = -999

        # attribute converters
        self.str_mux = {'01': 0b000, '03': 0b001, '13': 0b010, '23': 0b011,
                        '0G': 0b100, '1G': 0b101, '2G': 0b110, '3G': 0b111}
        self.bin_mux = {v: k for k, v in self.str_mux.items()}

        self.str_pga = {'6.144': 0b000, '4.096': 0b001, '2.048': 0b010, 
                        '1.024': 0b011, '0.512': 0b100, '0.256': 0b101}
        self.bin_pga = {v: float(k) for k, v in self.str_pga.items()}
        self.str_mode = {'continuous': 0b0, 'single': 0b1}
        self.bin_mode = {v: k for k, v in self.str_mode.items()}
        self.str_data_rate = {8: 0b000, 16: 0b001, 32: 0b010, 64: 0b011,
                              128: 0b100, 250: 0b101, 475: 0b110, 860: 0b111}
        self.bin_data_rate = {v: k for k, v in self.str_data_rate.items()}
        self.str_comp_mode = {'trad': 0b0, 'window': 0b1}
        self.bin_comp_mode = {v: k for k, v in self.str_comp_mode.items()}
        self.str_comp_pol = {'1': 0b00, '2': 0b01, '3': 0b10, 'off': 0b11}
        self.bin_comp_pol = {v: k for k, v in self.str_comp_pol.items()}
        self.str_comp_lat = {'off': 0b0, 'on': 0b1}
        self.bin_comp_lat = {v: k for k, v in self.str_comp_lat.items()}
        self.str_comp_que = {'1': 0b00, '2': 0b01, '3': 0b10, 'off': 0b11}
        self.bin_comp_que = {v: k for k, v in self.str_comp_que.items()}

        # information about this device
        self.device = DeviceData('ADS1115')
        self.device.description = ('Texas Instruments 16-bit 860SPS' +
                                   ' 4-Ch Delta-Sigma ADC with PGA')
        self.device.urls = 'www.ti.com/product/ADS1115'
        self.device.active = None
        self.device.error = None
        self.device.bus = repr(self.bus)
        self.device.manufacturer = 'Texas Instruments'
        self.device.version_hw = '1.0'
        self.device.version_sw = '1.0'
        self.device.accuracy = None
        self.device.precision = '16bit'
        self.device.calibration_date = None

        # current settings of this device
        self.device.pga_gain = self.pga_float

        # data recording method
        if output == 'csv':
            self.writer = CSVWriter('ADS1115', time_format='std_time_ms')
            self.writer.header = ['description', 'sample_n', 'mux', 'voltage']
        elif output == 'json':
            self.writer = JSONWriter('ADS1115', time_format='std_time_ms')
        else: 
            pass  # holder for another writer or change in default  
        self.writer.device = self.device.values()

        # data recording information
        self.sample_id = None

        # initialize class attributes from device registry
        self.get_config()

    def set_pointer(self, reg_name):
        """Set the pointer register address
        
        Allowed register names:
            'conversion'
            'config'
            'lo_thres'
            'hi_thresh'

        Parameters
        ----------
        reg_name : str, register address
        """
        reg_addr = self.reg_map[reg_name]

        self.bus.write_byte(reg_addr)

    def read_register_16bit(self, reg_name):
        """Get the values from one registry

        Allowed register names:
            'conversion'
            'config'
            'lo_thres'
            'hi_thresh'
        
        Parameters
        ----------
        reg_name : str, name of registry to read

        Returns
        -------
        16 bit registry value
        """

        reg_addr = self.reg_map[reg_name]
        return self.bus.read_register_16bit(reg_addr)

    def write_register_16bit(self, reg_name, data):
        """Write a 16 bits of data to register
        
        Allowed register names:
            'conversion'
            'config'
            'lo_thres'
            'hi_thresh'

        Parameters
        ----------
        reg_name : str, name of registry to read
        data : int, 16 bit value to write to register
        """

        reg_addr = self.reg_map[reg_name]
        self.bus.write_register_16bit(reg_addr, data)
        return True

    def set_config(self):
        self.write_register_16bit('config', self.config_value)
        return True

    def get_conversion(self):
        """Read the ADC conversion register at address 0x00
        Default value on power up from chip is 0
        """

        self.conversion_value = self.read_register_16bit('conversion')
        return self.conversion_value

    def get_config(self):
        """Read the configuration register at address 0x01
        Default value from chip is 0x8583 = 34179 = '0b1000010110000110'
        Specific states extracted with other methods
        """

        self.config_value = self.read_register_16bit('config')
        self.update_attributes()

    def update_attributes(self):
        """Update all attributes
        TODO: add more detail
        """
        # Comparator queue and disable
        self.comp_que_value = self.config_value & 0b11
        # Latching comparator
        self.comp_lat_value = (self.config_value >> 2) & 0b1
        # Comparator polarity
        self.comp_pol_value = (self.config_value >> 3) & 0b1
        # Comparator mode
        self.comp_mode_value = (self.config_value >> 4) & 0b1
        # Data rate
        self.dr_value = (self.config_value >> 5) & 0b111
        # Operating mode
        self.mode_value = (self.config_value >> 8) & 0b1
        # Programmable gain amplifier
        self.pga_value = (self.config_value >> 9) & 0b111
        self.pga_float = self.bin_pga[self.pga_value]
        # Multiplexer
        self.mux_value = (self.config_value >> 12) & 0b111
        # Operational status / Single-shot conversion start
        self.os_value = self.config_value >> 15

    def get_lo(self):
        """Read the low threshold register at address 0x02
        Default value from chip is 0x8000
        """

        self.lo_thres_value = self.read_register_16bit('lo_thresh')
        return self.lo_thres_value

    def get_hi(self):
        """Read the high threshold register at address 0x03
        Default value from chip is 0x7FFF
        """

        self.hi_thres_value = self.read_register_16bit('hi_thresh')
        return self.hi_thres_value

    def os(self):
        """Set the operational status
        As this has only one use in write mode, sets bit 15 to True.
        Chip will automatically clear it.  Bit 15 = True is also the
        power on default - it should be sufficient to read the configuration
        register once and use that bit position for all read commands.
        """
        self.config_value = (self.config_value & BIT_OS) | (0b1 << 15)
        self.set_config()
        self.os_value = self.config_value >> 15

    def mux(self, x):
        """Set multiplexer pin pair, ADS1115 only.
        
        Parameters
        ----------
        x : str, positive and negative pin combination.  Based on:
            AIN pins '0', '1', '2', '3' and Ground pin 'G'
            i.e. for AIN_pos = AIN0 and AIN_neg = Ground, x = '0G'
        """

        self.config_value = ((self.config_value & BIT_MUX)
                             | (self.str_mux[x] << 12))
        self.set_config()
        time.sleep(self.delay)
        self.mux_value = (self.config_value >> 12) & 0b111

    def pga(self, x):
        """Set programmable gain amplifier range.
        
        Parameters
        ----------
        x : str, +/- voltage range value.  Supported values:
            '6.144', '4.096', '2.048', '1.024', '0.512', '0.256'
        """

        self.config_value = ((self.config_value & BIT_PGA)
                             | (self.str_pga[x] << 9))
        self.set_config()
        time.sleep(self.delay)  # needs at least 7 ms to complete
        self.pga_value = (self.config_value >> 9) & 0b111
        self.pga_float = self.bin_pga[self.pga_value]

    def mode(self, x):
        """Set operating mode to either single or continuous.
        
        Parameters
        ----------
        x: str, either 'single' or 'continuous'
        """

        self.config_value = ((self.config_value & BIT_MODE)
                             | (self.str_mode[x] << 8))
        self.set_config()
        time.sleep(self.delay)
        self.mode_value = (self.config_value >> 8) & 0b1

    def data_rate(self, x):
        """Set data rate of sampling
        Changes bits [7:5]
        
        Parameters
        ----------
        x : int, samples per second.
            Allowed values: 8, 16, 32, 64,
            128, 250, 475, 860
        """

        self.config_value = ((self.config_value & BIT_DR)
                             | (self.str_data_rate[x] << 5))
        self.set_config()
        self.dr_value = (self.config_value >> 5) & 0b111

    def comp_mode(self, x):
        """Set comparator mode
        ADS1114 and ADS1115 only, changes bit 4

        x : str, 'trad' or 'window'
        """
        
        self.config_value = ((self.config_value & BIT_COMP_MODE)
                             | (self.str_comp_mode[x] << 4))
        self.set_config()
        self.comp_mode_value = (self.config_value >> 4) & 0b1

    def comp_polarity(self, x):
        """Set polarity of ALERT/RDY pin when active.
        No function in ADS1113, changes bit 3

        Parameters
        ----------
        x : str, 'high' or 'low'
        """

        self.config_value = ((self.config_value & BIT_COMP_POL)
                             | (self.str_comp_pol[x] << 3))
        self.set_config()
        self.comp_pol_value = (self.config_value >> 3) & 0b1

    def comp_latching(self, x):
        """Set whether the ALERT/RDY pin latches or clears when conversions
        are within the margins of the upper and lower thresholds

        Only available in ADS1114 and ADS1115, default is 0 = non-latching

        Parameters
        ----------
        x : str, 'on' or 'off'
        """

        self.config_value = ((self.config_value & BIT_COMP_LAT)
                             | (self.str_comp_lat[x] << 2))
        self.set_config()
        self.comp_lat_value = (self.config_value >> 2) & 0b1

    def comp_que(self, x):
        """Disable or set the number of conversions before a ALERT/RDY pin
        is set high
        
        Parameters
        ----------
        x : str, number of conversions '1', '2', '4' or 'off'
        """

        self.config_value = ((self.config_value & BIT_COMP_QUE)
                             | (self.str_comp_lat[x] << 0))
        self.set_config()
        self.comp_que_value = self.config_value & 0b11

    def single_shot(self):
        """Write 0x1 to bit 15 of the configuration register to initialize
        a single shot conversion.  The configuration register must be read at
        least once to get the current configuration, otherwise the chip default is used.
        Chip clears bit on completion of ADC conversion.
        """

        self.os()
        time.sleep(self.delay)
        self.get_conversion()

    def voltage(self):
        """Calculate the voltage measured by the chip based on conversion
        register and configuration register values
        """

        if self.mode_value == 1:
            self.single_shot()
        else:
            self.get_conversion()
        _x = twos_comp_to_dec(self.conversion_value, 16)
        self.volts = _x * (self.pga_float / 2**15)
        return self.volts

    def print_attributes(self):
        """Print to console current attributes"""
        print('ADS11x5 Configuration Attributes')
        print('--------------------------------')
        print('Config Register:', self.config_value,
              hex(self.config_value), bin(self.config_value))
        print('PGA Range: +/-', self.pga_float, 'Volts')
        print('Mode:', self.bin_mode[self.mode_value])
        print('Data Rate:', self.bin_data_rate[self.dr_value], 'SPS')
        print('Input Multiplexer:', self.bin_mux[self.mux_value])
        print('Comparator:')
        print(' Queue:', self.bin_comp_que[self.comp_que_value])
        print(' Latching:', self.bin_comp_lat[self.comp_lat_value])
        print(' Polarity: Active', self.bin_comp_pol[self.comp_pol_value])
        print(' Mode:', self.bin_comp_mode[self.comp_mode_value])

    def get(self, description='no_description', n=1):
        """Get formatted output.
        
        Parameters
        ----------
        description : char, description of data sample collected
        n : int, number of samples to record in this burst
        
        Returns
        -------
        data : list, data that will be saved to disk with self.write containing:
            description : str
            v : float, voltage measurement
        """
        data_list = []
        for m in range(1,n+1):
            data_list.append([description, m, self.mux_value, self.voltage()])
            if n == 1:
                return data_list[0]        
        return data_list

    def write(self, description='no_description', n=1):
        """Format output and save to file, formatted as either .csv or .json.
        
        Parameters
        ----------
        description : char, description of data sample collected
        n : int, number of samples to record in this burst

        Returns
        -------
        None, writes to disk the following data: 
            description : str, description of sample
            sample_n : int, sample number in this burst
            mux : str, multiplexer input used
            voltage : float, voltage measurement
        """
        self.writer.header = ['description', 'sample_n', 'mux', 'voltage']
        for m in range(1,n+1):        
            self.writer.write([description, m, self.mux_value, self.voltage()])
