"""Meerkat Device Driver Template
2019 Colin Dietrich

Minimal attributes and methods for a device driver.
tl;dr instance base.DeviceData, add a Writer, self.get and self.write methods
"""

from meerkat import base, tools
from meerkat.data import CSVWriter, JSONWriter

class ExampleDevice:
    def __init__(self, bus_n, bus_addr=0x00, output='csv'):
        """Initialize worker device on i2c bus.

        Parameters
        ----------
        bus_n : int, i2c bus number on Controller
        bus_addr : int, i2c bus number of this Worker device
        """

        # i2c bus
        self.bus = base.I2C(bus_n=bus_n, bus_addr=bus_addr)

        # print debug statements
        self.verbose = False

        # information about this device
        self.device = base.DeviceData('ExampleDevice')
        self.device.description = ('Just an example, replace')
        self.device.urls = 'www.example.com'
        self.device.active = None
        self.device.error = None
        self.device.bus = repr(self.bus)
        self.device.manufacturer = 'None'
        self.device.version_hw = '1.0'
        self.device.version_sw = '1.0'
        self.device.accuracy = None
        self.device.precision = 'replace'
        self.device.calibration_date = None

        # add device specific attributes
        self.device.other_attributes = None

        # data recording method
        if output == 'csv':
            self.writer = CSVWriter('ExampleDevice', time_source='std_time_ms')
        elif output == 'json':
            self.writer = JSONWriter('ExampleDevice', time_source='std_time_ms')
        else: 
            pass  # holder for another writer or change in default  
        # set writer header for device's output format, ADS1115 shown example
        self.writer.header = ['description', 'sample_n', 'voltage', 'current']
        self.writer.device = self.device.values()

        # data recording information
        self.sample_id = None

        # intialized configuration values
        self.get_config()

    # device specific methods...
    # ...
    # ...

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
            sample_n : int, sample number in this burst
            measurement, float, whatever values the device outputs
        """
        data_list = []
        for m in range(1,n+1):
            data_list.append([description, m, # data aquistion class methods
                             ])
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
            measurement, float, whatever values the device outputs
        """
        for m in range(1,n+1):        
            self.writer.write([description, m, # data aquistion class methods
                             ])
