"""MPU-6050 Gyroscope/Accelerometer I2C Driver for Raspberry PI & MicroPython

Made by: MrTijn/Tijndagamer
Forked 01/02/2019 from https://github.com/Tijndagamer/mpu6050
and merged into meerkat by: Colin Dietrich / crdietrich

The MIT License (MIT)

Copyright (c) 2015, 2016, 2017, 2018 Martijn (MrTijn), 2019 Colin Dietrich
and contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from meerkat.base import I2C, DeviceData
from meerkat.data import CSVWriter, JSONWriter


class mpu6050:

    # Global Variables
    GRAVITIY_MS2 = 9.80665

    # State Variables
    accel_range = None
    gyro_range = None

    # Scale Modifiers
    ACCEL_SCALE_MODIFIER_2G = 16384.0
    ACCEL_SCALE_MODIFIER_4G = 8192.0
    ACCEL_SCALE_MODIFIER_8G = 4096.0
    ACCEL_SCALE_MODIFIER_16G = 2048.0

    GYRO_SCALE_MODIFIER_250DEG = 131.0
    GYRO_SCALE_MODIFIER_500DEG = 65.5
    GYRO_SCALE_MODIFIER_1000DEG = 32.8
    GYRO_SCALE_MODIFIER_2000DEG = 16.4

    # Pre-defined ranges
    ACCEL_RANGE_2G = 0x00
    ACCEL_RANGE_4G = 0x08
    ACCEL_RANGE_8G = 0x10
    ACCEL_RANGE_16G = 0x18

    GYRO_RANGE_250DEG = 0x00
    GYRO_RANGE_500DEG = 0x08
    GYRO_RANGE_1000DEG = 0x10
    GYRO_RANGE_2000DEG = 0x18

    # MPU-6050 Registers
    PWR_MGMT_1 = 0x6B
    PWR_MGMT_2 = 0x6C

    ACCEL_XOUT0 = 0x3B
    ACCEL_YOUT0 = 0x3D
    ACCEL_ZOUT0 = 0x3F

    TEMP_OUT0 = 0x41

    GYRO_XOUT0 = 0x43
    GYRO_YOUT0 = 0x45
    GYRO_ZOUT0 = 0x47

    ACCEL_CONFIG = 0x1C
    GYRO_CONFIG = 0x1B

    def __init__(self, bus_n, bus_addr=0x68, output='csv'):

        # i2c bus
        self.bus = I2C(bus_n=bus_n, bus_addr=bus_addr)

        # Wake up the MPU-6050 since it starts in sleep mode
        # by toggling bit6 from 1 to 0, see pg 40 of RM-MPU-6000A-00 v4.2
        self.bus.write_register_8bit(self.PWR_MGMT_1, 0x00)
        
        # information about this device
        self.device = DeviceData('MPU-6050')
        self.device.description = ('TDK InvenSense Gyro & Accelerometer')
        self.device.urls = 'https://www.invensense.com/products/motion-tracking/6-axis/mpu-6050/'
        self.device.active = None
        self.device.error = None
        self.device.bus = repr(self.bus)
        self.device.manufacturer = 'TDK'
        self.device.version_hw = '0.1'
        self.device.version_sw = '0.1'
        self.device.gyro_accuracy = '+/-3%, +/-2% cross axis'
        self.device.gyro_precision = '16bit'
        self.device.gyro_noise = '0.05 deg/s-rms'
        self.device.accel_accuracy = '+/-0.5%, +/-2 cross axis'
        self.device.accel_precision = '16bit'
        self.device.accel_noise = 'PSD 400 ug / Hz**1/2'
        self.device.calibration_date = None

        '''
        # data recording method
        if output == 'csv':
            self.writer = CSVWriter('MPU-6050', time_format='std_time_ms')
            self.writer.header = ['description', 'sample_n', 'arange', 'grange',
                                  'ax', 'ay', 'az', 'gx', 'gy', 'gz', 'temp_C']
        elif output == 'json':
            self.writer = JSONWriter('MPU-6050', time_format='std_time_ms')
        else:
            pass  # holder for another writer or change in default
        self.writer.device = self.device.values()
        '''
        
        # data recording information
        self.sample_id = None

        # data recording method
        self.writer_output = output
        self.csv_writer = CSVWriter("MPU-6050", time_format='std_time_ms')
        self.csv_writer.device = self.device.__dict__
        self.csv_writer.header = ['description', 'sample_n',
                                  'ax', 'ay', 'az', 'gx', 'gy', 'gz']
        
        self.json_writer = JSONWriter("MCP9808", time_format='std_time_ms')
        self.json_writer.device = self.device.__dict__
        self.json_writer.header = self.csv_writer.header
        
    # I2C communication methods

    def read_i2c_word(self, register):
        """Read two i2c registers and combine them.

        register -- the first register to read from.
        Returns the combined read results.
        """

        value = self.bus.read_register_16bit(register)

        if value >= 0x8000:
            return -((65535 - value) + 1)
        else:
            return value

    # MPU-6050 Methods

    def get_temp(self):
        """Reads the temperature from the onboard temperature sensor of the MPU-6050.

        Returns the temperature in degrees Celcius.
        """
        raw_temp = self.read_i2c_word(self.TEMP_OUT0)

        # Get the actual temperature using the formule given in the
        # MPU-6050 Register Map and Descriptions revision 4.2, page 30
        actual_temp = (raw_temp / 340.0) + 36.53

        return actual_temp

    def set_accel_range(self, accel_range):
        """Sets the range of the accelerometer to range.

        accel_range -- the range to set the accelerometer to. Using a
        pre-defined range is advised.
        """

        self.accel_range = accel_range

        # First change it to 0x00 to make sure we write the correct value later
        self.bus.write_register_16bit(self.ACCEL_CONFIG, 0x00)

        # Write the new range to the ACCEL_CONFIG register
        self.bus.write_register_16bit(self.ACCEL_CONFIG, accel_range)

    def read_accel_range(self, raw = False):
        """Reads the range the accelerometer is set to.

        If raw is True, it will return the raw value from the ACCEL_CONFIG
        register
        If raw is False, it will return an integer: -1, 2, 4, 8 or 16. When it
        returns -1 something went wrong.
        """
        raw_data = self.bus.read_register_16bit(self.ACCEL_CONFIG)

        if raw is True:
            return raw_data
        elif raw is False:
            if raw_data == self.ACCEL_RANGE_2G:
                return 2
            elif raw_data == self.ACCEL_RANGE_4G:
                return 4
            elif raw_data == self.ACCEL_RANGE_8G:
                return 8
            elif raw_data == self.ACCEL_RANGE_16G:
                return 16
            else:
                return -1

    def get_accel(self, g = False):
        """Gets and returns the X, Y and Z values from the accelerometer.

        If g is True, it will return the data in g
        If g is False, it will return the data in m/s^2
        Returns a dictionary with the measurement results.
        """

        x = self.bus.read_register_16bit(self.ACCEL_XOUT0)
        y = self.bus.read_register_16bit(self.ACCEL_YOUT0)
        z = self.bus.read_register_16bit(self.ACCEL_ZOUT0)

        accel_scale_modifier = None
        accel_range = self.read_accel_range(True)

        if accel_range == self.ACCEL_RANGE_2G:
            accel_scale_modifier = self.ACCEL_SCALE_MODIFIER_2G
        elif accel_range == self.ACCEL_RANGE_4G:
            accel_scale_modifier = self.ACCEL_SCALE_MODIFIER_4G
        elif accel_range == self.ACCEL_RANGE_8G:
            accel_scale_modifier = self.ACCEL_SCALE_MODIFIER_8G
        elif accel_range == self.ACCEL_RANGE_16G:
            accel_scale_modifier = self.ACCEL_SCALE_MODIFIER_16G
        else:
            print("Unkown range - accel_scale_modifier set to self.ACCEL_SCALE_MODIFIER_2G")
            accel_scale_modifier = self.ACCEL_SCALE_MODIFIER_2G

        x = x / accel_scale_modifier
        y = y / accel_scale_modifier
        z = z / accel_scale_modifier

        if g is True:
            return {'x': x, 'y': y, 'z': z}
        elif g is False:
            x = x * self.GRAVITIY_MS2
            y = y * self.GRAVITIY_MS2
            z = z * self.GRAVITIY_MS2
            return x, y, z

    def set_gyro_range(self, gyro_range):
        """Sets the range of the gyroscope to range.

        gyro_range -- the range to set the gyroscope to. Using a pre-defined
        range is advised.
        """

        self.gyro_range = gyro_range

        # First change it to 0x00 to make sure we write the correct value later
        self.bus.write_register_16bit(self.GYRO_CONFIG, 0x00)

        # Write the new range to the ACCEL_CONFIG register
        self.bus.write_register_16bit(self.GYRO_CONFIG, gyro_range)

    def read_gyro_range(self, raw = False):
        """Reads the range the gyroscope is set to.

        If raw is True, it will return the raw value from the GYRO_CONFIG
        register.
        If raw is False, it will return 250, 500, 1000, 2000 or -1. If the
        returned value is equal to -1 something went wrong.
        """

        raw_data = self.bus.read_register_16bit(self.GYRO_CONFIG)

        if raw is True:
            return raw_data
        elif raw is False:
            if raw_data == self.GYRO_RANGE_250DEG:
                return 250
            elif raw_data == self.GYRO_RANGE_500DEG:
                return 500
            elif raw_data == self.GYRO_RANGE_1000DEG:
                return 1000
            elif raw_data == self.GYRO_RANGE_2000DEG:
                return 2000
            else:
                return -1

    def get_gyro(self):
        """Gets and returns the X, Y and Z values from the gyroscope.

        Returns the read values in a dictionary.
        """
        x = self.read_i2c_word(self.GYRO_XOUT0)
        y = self.read_i2c_word(self.GYRO_YOUT0)
        z = self.read_i2c_word(self.GYRO_ZOUT0)

        gyro_scale_modifier = None
        gyro_range = self.read_gyro_range(True)

        if gyro_range == self.GYRO_RANGE_250DEG:
            gyro_scale_modifier = self.GYRO_SCALE_MODIFIER_250DEG
        elif gyro_range == self.GYRO_RANGE_500DEG:
            gyro_scale_modifier = self.GYRO_SCALE_MODIFIER_500DEG
        elif gyro_range == self.GYRO_RANGE_1000DEG:
            gyro_scale_modifier = self.GYRO_SCALE_MODIFIER_1000DEG
        elif gyro_range == self.GYRO_RANGE_2000DEG:
            gyro_scale_modifier = self.GYRO_SCALE_MODIFIER_2000DEG
        else:
            print("Unkown range - gyro_scale_modifier set to self.GYRO_SCALE_MODIFIER_250DEG")
            gyro_scale_modifier = self.GYRO_SCALE_MODIFIER_250DEG

        x = x / gyro_scale_modifier
        y = y / gyro_scale_modifier
        z = z / gyro_scale_modifier

        return x, y, z

    def get_all(self):
        """Reads and returns all the available data."""
        temp  = self.get_temp()
        accel = self.get_accel()
        gyro  = self.get_gyro()

        return [temp] + list(accel) + list(gyro)

    def get(self, description='NA', n=1, delay=None):
        """Get formatted output.

        Parameters
        ----------
        description : char, description of data sample collected
        n : int, number of samples to record in this burst
        delay : float, seconds to delay between samples if n > 1

        Returns
        -------
        data : list, data containing:
            description: str, description of sample under test
            temperature : float, temperature in degrees Celcius
            delay : float, seconds to delay between samples if n > 1
        """
        data_list = []
        for m in range(1, n+1):
            data_list.append([description, m] + 
                             list(self.get_accel()) + 
                             list(self.get_gyro()))
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
            temperature : float, temperature in degrees Celcius
        """
        data_list = []
        for m in range(n):
            data_list.append(self.json_writer.publish([description, m] + 
                             list(self.get_accel()) + 
                             list(self.get_gyro())))
            if n == 1:
                return data_list[0]
            if delay is not None:
                time.sleep(delay)
        return data_list

    def write(self, description='NA', n=1, delay=None):
        """Format output and save to file, formatted as either
        .csv or .json.

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
            temperature : float, temperature in degrees Celcius
        """
        wr = {"csv": self.csv_writer,
              "json": self.json_writer}[self.writer_output]
        for m in range(n):
            wr.write([description, m] + 
                     list(self.get_accel()) + 
                     list(self.get_gyro()))
            if delay is not None:
                time.sleep(delay)
