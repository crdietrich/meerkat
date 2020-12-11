"""MCP23008 8bit I/O Expander I2C Driver for Raspberry PI & MicroPython
https://jap.hu/electronic/relay_module_i2c.html
https://www.microchip.com/wwwproducts/en/MCP23008
"""

from meerkat.base import I2C, time
from meerkat.data import Meta, CSVWriter, JSONWriter

from meerkat import tools

class MCP23008:
    
    def __init__(self, bus_n, bus_addr=0x20, output='csv'):
        """Initialize worker device on i2c bus.

        Parameters
        ----------
        bus_n : int, i2c bus number on Controller
        bus_addr : int, i2c bus number of this Worker device
        output : str, output data format, either 'csv' (default) or 'json'
        """

        # i2c bus
        self.bus = I2C(bus_n=bus_n, bus_addr=bus_addr)
        
        # set direction of I/O to output for all pins
        self.bus.write_register_8bit(reg_addr=0x00, data=0)
        
        self.reg_olat = None
        
        # information about this device
        self.metadata = Meta('MCP23008')
        self.metadata.description = '8 channel I2C relay board by Peter Jakab'
        self.metadata.urls = 'https://jap.hu/electronic/relay_module_i2c.html'
        self.metadata.manufacturer = 'Peter Jakab'
        
        self.metadata.header    = ['description', 'sample_n', 'relay_state']
        self.metadata.dtype     = ['str', 'int', 'str']
        self.metadata.accuracy  = None
        self.metadata.precision = None
        
        self.metadata.bus_n = bus_n
        self.metadata.bus_addr = bus_addr
        
        self.writer_output = output
        self.csv_writer = CSVWriter(metadata=self.metadata, time_format='std_time_ms')
        self.json_writer = JSONWriter(metadata=self.metadata, time_format='std_time_ms')
        
    def get_all_channels(self):
        """Get all channel states, as a single 8 bit value. Each bit 
        represents one channel where 0 = On, 1 = Off.
        
        Returns
        -------
        state : int, 8 bits
        """
        self.reg_olat = self.bus.read_register_8bit(reg_addr=0x0A)
        time.sleep(0.01)
        return self.reg_olat
        
    def set_all_channels(self, state):
        """Set all channel state, as a single 8 bit value. Each bit 
        represents one channel where 0 = On, 1 = Off.
        
        Parameters
        ----------
        state : int, 8 bits
        """
        self.bus.write_register_8bit(reg_addr=0x0A, data=state)
        
    def set_channel(self, channel, state):
        """Set a single channel On, Off or Toggle it
        
        Parameters
        ----------
        channel : int, 1-8 for the channel to change
        state : int, where
            0 = On
            1 = Off
            2 = Toggle from last state
        """
        
        assert (channel > 0) & (channel < 9)
        
        bitvalue = ( 1 << (channel - 1) )
        
        self.get_all_channels()

        if state == 0:
            self.reg_olat &= (~bitvalue)
        elif state == 1:
            self.reg_olat |= bitvalue
        elif state == 2:
            self.reg_olat ^= bitvalue

        self.set_all_channels(state=self.reg_olat)
    
    def publish(self, description='NA'):
        """Get relay state and output in JSON, plus metadata at intervals 
        set by self.metadata_interval

        Parameters
        ----------
        description : char, description of data sample collected, default='NA'

        Returns
        -------
        description : str
        n : sample number in this burst
        state : str, binary boolean state for each channel where
            0 = On
            1 = Off
        """
        m = 0
        state = self.get_all_channels()
        state = tools.left_fill(s=bin(state)[2:], n=8, x="0")
        return self.json_writer.publish([description, m, state])
        
    def write(self, description='NA'):
        """Get ADC output and save to file, formatted as either .csv or .json.

        Parameters
        ----------
        description : str, description of data sample collected
        n : int, number of samples to record in this burst
        delay : float, seconds to delay between samples if n > 1

        Returns
        -------
        None, writes to disk the following data:
            description : str
            n : sample number in this burst
            state : str, binary boolean state for each channel where
                0 = On
                1 = Off
        """ 
        wr = {"csv": self.csv_writer,
              "json": self.json_writer}[self.writer_output]
        m=1
        state = self.get_all_channels()
        state = "0b" + tools.left_fill(s=bin(state)[2:], n=8, x="0")
        wr.write([description, m, state])
