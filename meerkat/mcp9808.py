"""MCP9808 Temperature Sensor Driver for Raspberry PI & MicroPython"""

from meerkat.base import I2C, time
from meerkat.data import Meta, CSVWriter, JSONWriter

# chip register address
REG_CONFIG             = 0x01
REG_UPPER_TEMP         = 0x02
REG_LOWER_TEMP         = 0x03
REG_CRIT_TEMP          = 0x04
REG_AMBIENT_TEMP       = 0x05
REG_MANUF_ID           = 0x06
REG_DEVICE_ID          = 0x07

# Configuration register values
REG_CONFIG_SHUTDOWN    = 0x0100
REG_CONFIG_CRITLOCKED  = 0x0080
REG_CONFIG_WINLOCKED   = 0x0040
REG_CONFIG_INTCLR      = 0x0020
REG_CONFIG_ALERTSTAT   = 0x0010
REG_CONFIG_ALERTCTRL   = 0x0008
REG_CONFIG_ALERTSEL    = 0x0002
REG_CONFIG_ALERTPOL    = 0x0002
REG_CONFIG_ALERTMODE   = 0x0001


class MCP9808(object):
    def __init__(self, bus_n, bus_addr=0x18, output='csv', name='mcp9808'):
        """Initialize worker device on i2c bus.

        Parameters
        ----------
        bus_n : int, i2c bus number on Controller
        bus_addr : int, i2c bus number of this Worker device
        """

        # i2c bus
        self.bus = I2C(bus_n=bus_n, bus_addr=bus_addr)

        # register values and defaults
        # TODO: do the constant values need to be specified?
        self.reg_map = {'config': REG_CONFIG,
                        'upper_temp': REG_UPPER_TEMP,
                        'lower_temp': REG_LOWER_TEMP,
                        'crit_temp': REG_CRIT_TEMP,
                        'ambient': REG_AMBIENT_TEMP,
                        'manufacturer': REG_MANUF_ID,
                        'device_id': REG_DEVICE_ID}

        self.alert_critial = None
        self.alert_upper = None
        self.alert_lower = None

        self.manufacturer_id = None
        self.device_id = None
        self.revision = None
        
        # information about this device
        self.metadata = Meta(name=name)
        self.metadata.description = 'Microchip Tech digital temperature sensor'
        self.metadata.urls = 'https://www.microchip.com/datasheet/MCP9808'
        self.metadata.manufacturer = 'Adafruit Industries & Microchip Tech'
        
        self.metadata.header    = ['description', 'sample_n', 'temp_C']
        self.metadata.dtype     = ['str', 'int', 'float']
        self.metadata.units     = [None, 'count', 'degrees Celcius']
        self.metadata.accuracy  = [None, 1, '+/- 0.25 typical'] 
        self.metadata.precision = [None, 1, '0.0625 max']
        
        self.metadata.bus_n = bus_n
        self.metadata.bus_addr = hex(bus_addr)

        # data recording method
        self.writer_output = output
        self.csv_writer = CSVWriter(metadata=self.metadata, time_source='std_time_ms')
        self.json_writer = JSONWriter(metadata=self.metadata, time_source='std_time_ms')
        
    def set_pointer(self, reg_name):
        """Set the pointer register address

        Allowed address names:
            'config'
            'upper_temp'
            'lower_temp'
            'crit_temp'
            'ambient'
            'manufacturer'
            'device_id'

        Parameters
        ----------
        reg_name : str, register address
        """
        reg_addr = self.reg_map[reg_name]

        self.bus.write_byte(reg_addr)

    def read_register_16bit(self, reg_name):
        """Get the values from one registry

        Allowed register names:
            'config'
            'upper_temp'
            'lower_temp'
            'crit_temp'
            'ambient'
            'manufacturer'
            'device_id'

        Parameters
        ----------
        reg_name : str, name of registry to read

        Returns
        -------
        upper byte
        lower byte
        """

        reg_addr = self.reg_map[reg_name]
        ulb = self.bus.read_register_16bit(reg_addr)
        ub = ulb >> 8
        lb = ulb & 0xff
        return ub, lb

    def get_status(self):
        self.get_config()
        self.get_upper_temp()
        self.get_lower_temp()
        self.get_critical_temp()
        self.get_manufacturer()
        self.get_device_id()

    def print_status(self):
        self.get_status()
        print('Configuration Register: {}'.format(None))
        print('Upper Temperature: {}'.format(None))
        print('Lower Temperature: {}'.format(None))
        print('Critical Temperature: {}'.format(None))
        print('Manufacturer: {}'.format(self.manufacturer_id))
        print('Device ID: {}'.format(self.device_id))
        print('Device Revision: {}'.format(self.revision))

    def get_config(self):  #TODO: parse bytes and add docstrings
        ub, lb = self.read_register_16bit('config')

    def get_upper_temp(self):
        ub, lb = self.read_register_16bit('upper_temp')

    def get_lower_temp(self):
        ub, lb = self.read_register_16bit('lower_temp')

    def get_critical_temp(self):
        ub, lb = self.read_register_16bit('crit_temp')

    def get_manufacturer(self):
        ub, lb = self.read_register_16bit('manufacturer')
        self.manufacturer_id = (ub << 8) | lb

    def get_device_id(self):
        (self.device_id,
         self.revision) = self.read_register_16bit('device_id')

    def get_temp(self):
        """Get temperature in degrees Celcius with 13 bit accuracy

        Returns
        -------
        float, temperature in degrees Celcius
        """

        ub, lb = self.read_register_16bit('ambient')

        self.alert_critial = (ub & 0x80) == 0x80
        self.alert_upper = (ub & 0x40) == 0x40
        self.alert_lower = (ub & 0x20) == 0x20

        ub = ub & 0x1F

        if (ub & 0x10) == 0x10:
            ub = ub & 0x10
            return 256 - (ub * 2**4) + (lb * 2**-4)
        else:
            return (ub * 2**4) + (lb * 2**-4)

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
            data_list.append([description, m, self.get_temp()])
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
            data_list.append(self.json_writer.publish([description, m, self.get_temp()]))
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
            wr.write([description, m, self.get_temp()])
            if delay is not None:
                time.sleep(delay)
