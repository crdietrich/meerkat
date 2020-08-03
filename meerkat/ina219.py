"""TI INA219 current measurement driver for Raspberry PI & MicroPython"""

from meerkat import base, tools
from meerkat.data import CSVWriter, JSONWriter


class INA219:
    def __init__(self, bus_n, bus_addr=0x40, output='csv'):
        """Initialize worker device on i2c bus.

        Parameters
        ----------
        bus_n : int, i2c bus number on Controller
        bus_addr : int, i2c bus number of this Worker device
        """

        # i2c bus
        self.bus = base.I2C(bus_n=bus_n, bus_addr=bus_addr)

        self.reg_config = None
        self.reg_shunt_voltage = None
        self.reg_bus_voltage = None
        self.reg_power = None
        self.reg_calibration = None

        self.reg_map = {'config':        0x00, 
                        'shunt_voltage': 0x01,
                        'bus_voltage':   0x02, 
                        'power':         0x03,
                        'current':       0x04, 
                        'calibration':   0x05}

        # bus voltage range
        self.bv_reg_to_bv = {0: 16, 1:32}
        
        # programable gain amplifier
        self.pga_reg_to_gain = {0:1, 1:2, 2:4, 3:8}
        self.pga_gain_to_reg = {1:0, 2:1, 4:2, 8:3}
        self.pga_reg_str_range = {1: "+/- 40 mV",
                                  2: "+/- 80 mV",
                                  4: "+/- 160 mV",
                                  8: "+/- 320 mV"}

        # print debug statements
        self.verbose = False

        # information about this device
        self.device = base.DeviceData('INA219')
        self.device.description = ('Texas Instruments Bidirectional Current' +
                                   ' Monitor')
        self.device.urls = 'www.ti.com/product/ADS1115'
        self.device.active = None
        self.device.error = None
        self.device.bus = repr(self.bus)
        self.device.manufacturer = 'Texas Instruments'
        self.device.version_hw = '1.0'
        self.device.version_sw = '1.0'
        self.device.accuracy = None
        self.device.precision = '12bit'
        self.device.calibration_date = None

        # chip defaults on power up or reset command
        self.device.bus_voltage_range = self.bv_reg_to_bv[1]
        self.device.gain = self.pga_reg_to_gain[0b11]
        self.device.gain_string = self.pga_reg_str_range[self.device.gain]

        self.device.bus_adc_resolution = 12
        self.device.bus_adc_averaging = None

        self.device.shunt_adc_resolution = 12
        self.device.shunt_adc_averaging = None

        self.device.mode = 7
        self.mode_to_str = {0: "power down",
                            1: "shunt voltage, triggered",
                            2: "bus voltage, triggered",
                            3: "shunt and bus voltages, triggered",
                            4: "ADC off (disabled)",
                            5: "shunt voltage, continuous",
                            6: "bus voltage, continuous",
                            7: "shunt and bus voltages, continuous"}
        self.device.mode_description = self.mode_to_str[self.device.mode]

        # Adafruit INA219 breakout board as a 0.1 ohm 1% 2W resistor
        self.device.r_shunt = 0.1

        # data recording information
        self.sample_id = None
        
        # data recording method
        self.writer_output = output
        self.csv_writer = CSVWriter("INA219", time_format='std_time_ms')
        self.csv_writer.device = self.device.__dict__
        self.csv_writer.header = ['description', 'sample_n', 'voltage', 'current']
        
        self.json_writer = JSONWriter("INA219", time_format='std_time_ms')
        self.json_writer.device = self.device.__dict__
        self.json_writer.header = ['description', 'sample_n', 'voltage', 'current']

        # intialized configuration values
        self.get_config()

    def read_register(self, reg_name):
        """Get the values from one registry

        Allowed register names:
            'config'
            'shunt_voltage'
            'bus_voltage'
            'power'
            'current'
            'calibration'

        Parameters
        ----------
        reg_name : str, name of registry to read

        Returns
        -------
        16 bit registry value
        """

        reg_addr = self.reg_map[reg_name]
        return self.bus.read_register_16bit(reg_addr)

    def get_config(self):
        r = self.read_register('config')
        self.reg_config = r
        self.device.bus_voltage_range = self.bv_reg_to_bv[(r >> 13) & 0b1]
        self.device.gain = self.pga_reg_to_gain[(r >> 11) & 0b11]
        
        if self.verbose:
            print("Bus Voltage Range:", 
                  self.device.bus_voltage_range, "V")
            print("PGA Range: {}x or {}".format(self.device.gain, 
                  self.pga_reg_str_range[self.device.gain]))
            print("Configuration Register:")
            tools.bprint(r)
        return r

    def get_shunt_voltage(self):
        """Read the shunt voltage register where LSB = 10uV

        Note: datasheet calculations result in mV, see section 8.5.1
        
        Returns
        -------
        float : shunt voltage in volts (not millivolts)
        """
        return self.read_register('shunt_voltage') * 0.00001

    def get_bus_voltage(self):
        """Read the bus voltage register where LSB = 4mV.
        
        Note: Right most 3 bits of bus voltage register are 0, CNVR, OVF
              32 volt range => 0 to 32 VDC
              16 volt range => 0 to 16 VDC
        
        Returns
        -------
        float : bus voltage in volts (not millivolts)
        """
        r = self.read_register('bus_voltage')
        return (r >> 3)  * 4.0 * 0.001

    def get_power(self):
        r = self.read_register('power')
        return r

    def get_current(self):
        r = self.read_register('current')
        return r

    def get_calibration(self):
        r = self.read_register('calibration')
        return r

    def write_register(self, reg_name, data):
        """Write a 16 bits of data to register

        Allowed register names:
            'config'
            'shunt_voltage'
            'bus_voltage'
            'power'
            'current'
            'calibration'

        Parameters
        ----------
        reg_name : str, name of registry to read
        data : int, 16 bit value to write to register
        """

        reg_addr = self.reg_map[reg_name]
        if self.verbose:
            print("Writing to '{}' registry # {}".format(reg_name, reg_addr))
            tools.bprint(data)
        self.bus.write_register_16bit(reg_addr, data)

    def write_config(self, data):
        self.write_register('config', data)

    def write_calibration(self, data):
        self.write_register('calibration', data)

    def reset(self):
        self.write_config(self.reg_config | 0b1000000000000000)

    def set_bus_voltage_range(self, v=32):
        reg_value = {16: base.bit_clear(13, self.reg_config),
                     32: base.bit_set(13, self.reg_config)}[v]
        self.reg_config = reg_value
        self.device.bus_voltage_range = v
        self.write_config(reg_value)

    def set_pga_range(self, gain=8):
        mask = 0b1110011111111111  #                 PGA  10
        reg_value = {1:   (self.reg_config & mask) | 0b0000000000000000,
                     2:   (self.reg_config & mask) | 0b0000100000000000,
                     4:   (self.reg_config & mask) | 0b0001000000000000,
                     8:   (self.reg_config & mask) | 0b0001100000000000}[gain]
        self.reg_config = reg_value
        self.device.gain = gain
        self.device.gain_string = self.pga_reg_str_range[self.gain]
        self.write_config(reg_value)

    def set_bus_adc_resolution(self, bits=12):
        """Generate config register for setting ADC resolution"""
        mask = 0b1111100001111111  #                 BADC   4321
        reg_value = {9:   (self.reg_config & mask) | 0b0000000000000000,
                     10:  (self.reg_config & mask) | 0b0000000010000000,
                     11:  (self.reg_config & mask) | 0b0000000100000000,
                     12:  (self.reg_config & mask) | 0b0000000110000000}[bits]
        self.reg_config = reg_value
        self.device.bus_adc_resolution = bits
        self.device.bus_adc_averaging = None
        self.write_config(reg_value)

    def set_bus_adc_samples(self, n=128):
        """Generate config register for setting ADC sample averaging"""
        mask = 0b1111100001111111  #                 BADC   4321
        reg_value = {2:   (self.reg_config & mask) | 0b0000010010000000,
                     4:   (self.reg_config & mask) | 0b0000010100000000,
                     8:   (self.reg_config & mask) | 0b0000010110000000,
                     16:  (self.reg_config & mask) | 0b0000011000000000,
                     32:  (self.reg_config & mask) | 0b0000011010000000,
                     64:  (self.reg_config & mask) | 0b0000011100000000,
                     128: (self.reg_config & mask) | 0b0000011110000000}[n]
        self.reg_config = reg_value
        self.device.bus_adc_resolution = None
        self.device.bus_adc_averaging = n
        self.write_config(reg_value)

    def set_shunt_adc_resolution(self, bits=12):
        """Generate config register for setting ADC resolution"""
        mask = 0b1111111110000111  #                 SADC       4321
        reg_value = {9:   (self.reg_config & mask) | 0b0000000000000000,
                     10:  (self.reg_config & mask) | 0b0000000000001000,
                     11:  (self.reg_config & mask) | 0b0000000000010000,
                     12:  (self.reg_config & mask) | 0b0000000000011000}[bits]
        self.reg_config = reg_value
        self.device.shunt_adc_resolution = bits
        self.device.shunt_adc_averaging = None
        self.write_config(reg_value)

    def set_shunt_adc_samples(self, n=128):
        mask = 0b1111111110000111  #                 SADC       4321
        reg_value = {2:   (self.reg_config & mask) | 0b0000000001001000,
                     4:   (self.reg_config & mask) | 0b0000000001010000,
                     8:   (self.reg_config & mask) | 0b0000000001011000,
                     16:  (self.reg_config & mask) | 0b0000000001100000,
                     32:  (self.reg_config & mask) | 0b0000000001101000,
                     64:  (self.reg_config & mask) | 0b0000000001110000,
                     128: (self.reg_config & mask) | 0b0000000001111000}[n]
        self.reg_config = reg_value
        self.device.adc_resolution = None
        self.device.adc_averaging = n
        self.write_config(reg_value)

    def set_mode(self, n=7):
        mask = 0b1111111111111000  #                 MODE           321
        reg_value = {0:   (self.reg_config & mask) | 0b0000000000000000,
                     1:   (self.reg_config & mask) | 0b0000000000000001,
                     2:   (self.reg_config & mask) | 0b0000000000000010,
                     3:   (self.reg_config & mask) | 0b0000000000000011,
                     4:   (self.reg_config & mask) | 0b0000000000000100,
                     5:   (self.reg_config & mask) | 0b0000000000000110,
                     6:   (self.reg_config & mask) | 0b0000000000000111}[n]
        self.reg_config = reg_value
        self.device.mode = n
        self.device.mode_description = self.mode_to_str[n]
        self.write_config(reg_value)

    def set_calibration(self, cal_value):
        """Set the calibration register, see datasheet for details

        cal_value : int, register value to write
        """
        self.reg_calibration = cal_value
        self.write_calibration(cal_value)

    def get_current_simple(self):
        """Calculate the current from single shot measurements"""
        return self.get_shunt_voltage() / self.device.r_shunt

    def get(self, description='NA', n=1, delay=None):
        """Get formatted output.

        Parameters
        ----------
        description : str, description of data sample collected
        n : int, number of samples to record in this burst
        delay : float, seconds to delay between samples if n > 1
        
        Returns
        -------
        data : list, data that will be saved to disk with self.write containing:
            description: str, description of sample under test
            sample_n : int, sample number in this burst
            voltage, float, Volts measured at the shunt resistor
            current : float, Amps of current accross the shunt resistor
        """
        data_list = []
        for m in range(1, n+1):
            data_list.append([description, m,
                              self.get_bus_voltage(),
                              self.get_current_simple()])
            if n == 1:
                return data_list[0]
            if delay is not None:
                time.sleep(delay)
        return data_list

    def publish(self, description='NA', n=1, delay=None):
        """Output relay status data in JSON.

        Parameters
        ----------
        description : str, description of data sample collected
        n : int, number of samples to record in this burst
        delay : float, seconds to delay between samples if n > 1

        Returns
        -------
        str, formatted in JSON with keys:
            description: str, description of sample under test
            sample_n : int, sample number in this burst
            voltage, float, Volts measured at the shunt resistor
            current : float, Amps of current accross the shunt resistor
        """
        data_list = []
        for m in range(n):
            data_list.append(self.json_writer.publish([description, m, 
                                                       self.get_bus_voltage(),
                                                       self.get_current_simple()]))
            if n == 1:
                return data_list[0]
            if delay is not None:
                time.sleep(delay)
        return data_list
    
    def write(self, description='NA', n=1, delay=None):
        """Format output and save to file, formatted as either .csv or .json.

        Parameters
        ----------
        description : str, description of data sample collected
        n : int, number of samples to record in this burst
        delay : float, seconds to delay between samples if n > 1

        Returns
        -------
        None, writes to disk the following data:
            description : str, description of sample
            sample_n : int, sample number in this burst
            voltage, float, Volts measured at the shunt resistor
            current : float, Amps of current accross the shunt resistor
        """ 
        wr = {"csv": self.csv_writer,
              "json": self.json_writer}[self.writer_output]
        for m in range(n):
            wr.write([description, m,
                      self.get_bus_voltage(),
                      self.get_current_simple()])
            if delay is not None:
                time.sleep(delay)
