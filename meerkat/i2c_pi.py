"""Wrap i2c methods in a universal way
2019 Colin Dietrich
"""

from meerkat import i2c_quickwire

class WrapI2C:
    def __init__(self, bus, bus_addr):
        """Set the I2C communications to the worker device specified by 
		the address
        
        Parameters
        ----------
        bus : int, i2c bus connected to worker devices
        bus_addr : hex, address of worker device on i2c bus
        """
        self.bus = i2c_quickwire.I2CMaster(n=bus)
        self.bus_addr = bus_addr

    def read_byte(self):
        """Read one byte from worker device
        
        Returns
        -------
        int, 8 bits of data
        """
        
        return self.bus.get(self.bus_addr, 1)[0]
        
    def write_byte(self, data):
        """Write one byte to worker device
        
        Parameters
        ----------
        data : int, 8 bits of data
        """
        self.bus.write_bytes(self.bus_addr, data)
        
    def read_register_16bit(self, reg_addr):
        """Get the values from one registry
        
        Parameters
        ----------
        reg_addr : int, registry internal to the worker device to read

        Returns
        -------
        16 bit value of registry
        """

        self.bus.write_bytes(self.bus_addr, reg_addr)
        value = self.bus.get(self.bus_addr, 2)[0]
        return int.from_bytes(value, byteorder='big')

    def write_register_16bit(self, reg_addr, data):
        """Write a 16 bit register.  Breaks 16 bit data into list of 
		8 bit values.
        
        Parameters
        ----------
        reg_addr : int, register internal to the worker device
        data : int, 16 bit value to write
        
        """
        self.bus.write_bytes(self.bus_addr, reg_addr, data >> 8, data & 0xff)
        
    def write_n_bytes(self, *data):
        """Write bytes (n total) to worker device
        
        Parameters
        ----------
        *data : iterable of bytes
        """
        
        self.bus.write_bytes(self.bus_addr, *data)
        
    def read_n_bytes(self, n):
        """Write bytes (n total) to worker device
        
        Parameters
        ----------
        n : int, number of bytes to read
        
        Returns
        -------
        iterable of bytes
        """
        
        return self.bus.get(self.bus_addr, n)
