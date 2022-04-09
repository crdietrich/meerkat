"""EMC2101 Fan Speed Driver for Raspberry PI & MicroPython

Manufacturer Information

Breakout Board and CircuitPython Driver this work derives from:

"""

from meerkat.base import I2C, time, struct
from meerkat.data import Meta, CSVWriter, JSONWriter


class EMC2101:
    def __init__(self, bus_n, bus_addr=0x4c, output='csv', sensor_id='emc2101'):
        """Initialize worker device on i2c bus.

        Parameters
        ----------
        bus_n : int, i2c bus number on Controller
        bus_addr : int, i2c bus number of this Worker device
        output : str, writer output format, either 'csv' or 'json'
        sensor_id : str, sensor id, 'emc2101' by default
        """

        # i2c bus
        self.bus = I2C(bus_n=bus_n, bus_addr=bus_addr)

        # memory mapped from 8 bit register locations


        # information about this device
        self.metadata = Meta(name=sensor_id)
        self.metadata.description = 'Bosch Humidity, Pressure, Temperature, VOC Sensor'
        self.metadata.urls = 'https://www.bosch-sensortec.com/products/environmental-sensors/gas-sensors-bme680/'
        self.metadata.manufacturer = 'Bosch Sensortec'

        self.metadata.header    = ['system_id', 'sensor_id', 'description', 'sample_n', 'T',       'P',            'RH',       'g_res',  'g_val', 'heat_stab']
        self.metadata.dtype     = ['str',       'str',       'str',         'int',      'float',   'float',        'float',    'float',  'bool',  'bool']
        self.metadata.units     = ['NA',        'NA',        'NA',          'count',    'Celcius', 'hectopascals', 'percent',  'ohms',    'NA',   'NA', ]
        self.metadata.accuracy  = ['NA',        'NA',        'NA',          '1',         '+/-1.0',  '+/-0.12',      '+/-3',     '+/-15%', 'NA',   'NA']
        self.metadata.precision = ['NA',        'NA',        'NA',          '1',         '0.1',     '0.18',         '0.008',    '0.08',   'NA',   'NA']
        self.metadata.bus_n = bus_n
        self.metadata.bus_addr = hex(bus_addr)

        # data recording information
        self.system_id = None
        self.sensor_id = sensor_id
        
        self.writer_output = output
        self.csv_writer   = CSVWriter(metadata=self.metadata, time_source='std_time_ms')
        self.json_writer = JSONWriter(metadata=self.metadata, time_source='std_time_ms')

        # device specific configuration
        self._conversion_rates = {
            '1/16' : 0b0000,
            '1/8'  : 0b0001,
            '1/4'  : 0b0010,
            '1/2'  : 0b0011,
            '1'    : 0b0100,
            '2'    : 0b0101,
            '4'    : 0b0110,
            '8'    : 0b0111,
            '16'   : 0b1000,
            '32'   : 0b1001
            }

        self.convesion_rate = '16'  # default
        
    def _placeholder_write_byte(self):
        """4.2 Write Byte
        Write one byte to the device"""
        self.bus.write_n_bytes([0xB6])
        
        
    def internal_temperature(self):
        temp_int = self.bus.read_register_8bit(0x00)
        return temp_int
    
    def external_temperature(self):
        temp_ext_msb = self.bus.read_register_8bit(0x01)
        temp_ext_lsb = self.bus.read_register_8bit(0x10)
        temp_ext = ((temp_ext_msb << 8) + temp_ext_lsb) >> 5
        return temp_ext
        
    def status(self):
        """Get the operational state of the device.
        See Section 6.4"""
        status = self.bus.read_register_8bit(0x02)
        
        # temporary return
        return str(bin(status))
    
    def config_get(self):
        """Get configuration of basic functionality of device
        Note: Register address 0x03 and 0x09 mirror the register data
        """
        config = self.bus.read_register_8bit(0x03)
        
        # temporary return
        return str(bin(config))
        
    def conversion_rate_get(self):
        """Get the rate of ADC conversions per second"""
        conv_rate = self.bus.read_register_8bit(0x04)
        _cr_mapper = {v:k for k,v in self._conversion_rates.items()}
        conv_rate = _cr_mapper[conv_rate & 0b1111]
        
        # temporary return
        #return str(bin(conv_rate))
        return conv_rate
    
    def tach_get(self):
        """
        The TACH monitor counts the number of clock pulses that occur between five edges of the TACH
        signal. The monitor assumes that the tachometer signal is always valid (such as generated from a 4-
        wire fan or a direct drive fan) and that the tachometer signal generates 2 TACH pulses per fan
        revolution"""
        
        tach_lsb = self.bus.read_register_8bit(0x46)
        tach_msb = self.bus.read_register_8bit(0x47)
        print(tach_lsb, tach_msb)
        tach = (tach_msb << 8) + tach_lsb
        #tach = float(tach)
        tach >> 2
        return tach
    
    def rpm_get(self):
        tach = self.tach_get()
        rpm = 5400000.0 / tach
        return rpm
    
    def conversion_rate_set(self, rate):
        _reg_code = self._conversion_rates[rate]
        self.bus.write_register_8bit(0x04, _reg_code)
    
    
    def get(self, description='NA', n=1, verbose=False):
        """Get one sample of data

        Parameters
        ----------
        description : str, description of data sample collected
        n : int, number of samples to record in this burst
        verbose : bool, print debug statements

        Returns
        -------

        """
        return [self.system_id, self.sensor_id, description, n] + d + [self._gas_valid, self._heat_stab]

    def publish(self, description='NA', verbose=False):
        """Get one sample of data in JSON.

        Parameters
        ----------
        description : str, description of data sample collected
        verbose : bool, print debug statements

        Returns
        -------
        """
        data = self.get(description=description, verbose=verbose)
        json_data = self.json_writer.publish(data)
        return json_data


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
            description: str, description of sample under test
            sample_n : int, sample number in this burst
        """
        wr = {"csv": self.csv_writer,
              "json": self.json_writer}[self.writer_output]
        for m in range(n):
            data = self.get(description=description)
            wr.write(data)
            if delay is not None:
                time.sleep(delay)
