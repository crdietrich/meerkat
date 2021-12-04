"""MCP4728 Digitial to Analog Converter (DAC) for Raspberry Pi & MicroPython

Colin Dietrich, 2021
"""


from meerkat.base import I2C, time
from meerkat.data import Meta, CSVWriter, JSONWriter


class MCP4728(object):
    def __init__(self, bus_n, bus_addr=0x18, output='csv', name='mcp4728'):
        """Initialize worker device on i2c bus.

        Parameters
        ----------
        bus_n : int, i2c bus number on Controller
        bus_addr : int, i2c bus number of this Worker device
        """
    
        # i2c bus
        self.bus = I2C(bus_n=bus_n, bus_addr=bus_addr)

        # register values and defaults
        self.reg_map = {'default_addr'     : 0x60,
                        'ch_a_multi_eprom' : 0x50,
                        'call_address'     : 0x00,
                        'call_reset'       : 0x06,
                        'call_wakeup'      : 0x09,
                        'software_update'  : 0x08
                        }


    def reset(self):
        """Reset similar to power-on reset. See section 5.4.1."""
        self.bus.write_n_bytes(data=[0x00, 0x06])

    def wake(self):
        """Reset power-down bits. See section 5.4.2"""
        self.bus.write_n_bytes(data=[0x00, 0x09]) 
        
    def software_update(self):
        """Update all DAC analog outputs. See section 5.4.3"""
        self.bus.write_n_bytes(data=[0x00, 0x08]) 

    def read_address(self):
        """Return the I2C address. See section 5.4.4"""
        self.bus.write_n_bytes(data=[0x00, 0x0C])
        return self.bus.readbyte()

    
