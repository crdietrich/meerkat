"""MCP9808 Temperature Sensor for Micropython/Python
Author: Colin Dietrich 2018
"""

from meerkat.base import DeviceData
from meerkat.data import CSVWriter, JSONWriter

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
    def __init__(self, bus, i2c_addr=0x18, output='csv'):
    
        # i2c bus
        self.bus = bus
        self.bus_addr = i2c_addr

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
        self.device = DeviceData('MCP9808')
        self.device.description = ('+/-0.5 degrees Celcius ' +
            'maximum accuracy digital temperature sensor')
        self.device.urls = 'https://www.microchip.com/datasheet/MCP9808'
        self.device.active = None
        self.device.error = None
        self.device.bus = repr(bus)
        self.device.manufacturer = 'Microchip'
        self.device.version_hw = '0.1'
        self.device.version_sw = '0.1'
        self.device.accuracy = '+/-0.25 (typical) C'
        self.device.precision = '0.0625 C maximum'
        self.device.units = 'Degrees Celcius'
        self.device.calibration_date = None

        # data recording information
        self.sample_id = None

        # data recording method
        if output == 'csv':
            self.writer = CSVWriter('MCP9808')
            self.writer.device = self.device.__dict__
            self.writer.header = ['sample_id', 'temperature_C']

        elif output == 'json':
            self.writer = JSONWriter('MCP9808')

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

        self.bus.write_byte(self.bus_addr, reg_addr)

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
        ub, lb = self.bus.read_i2c_block_data(self.bus_addr, reg_addr, 2)
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

    def get(self, sid=None):
        """Get formatted output.
        
        Parameters
        ----------
        sid : char, defalut=None, sample id to identify data sample collected
        
        Returns
        -------
        data : list, data that will be saved to disk with self.write containing:
            sid : str, sample id
            v : float, temperature (C) measurement"""
        
        return [sid, self.get_temp()]

    def write(self, sid=None):
        """Format output and save to file.
        
        Parameters
        ----------
        sid : char, defalut=None, sample id to identify data sample collected
        
        Returns
        -------
        None, writes to disk the following:
            data : list, data that will be saved to disk containing
                sid : str, sample id
                v : float, temperature (C) measurement"""
        
        # data values will be converted to string by write method
        self.writer.write(self.get_temp(sid=sid))
        

