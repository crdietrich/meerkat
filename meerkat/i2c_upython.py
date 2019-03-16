"""Wrap i2c methods for MicroPython
2019 Colin Dietrich
"""

from machine import I2C


class WrapI2C:
    def __init__(self, bus_n, bus_addr, frequency=400000):
        """Set the I2C communications to the worker device specified by
        the address

        Parameters
        ----------
        bus_n : int, i2c bus connected to worker devices
        bus_addr : hex, address of worker device on i2c bus
        """

        self.bus = I2C(bus_n, I2C.MASTER, freq=frequency)
        self.bus_addr = bus_addr

    def read_byte(self):
        """Read one byte from worker device

        Returns
        -------
        int, 8 bits of data
        """

        return self.bus.readfrom(self.bus_addr, 1)

    def write_byte(self, data):
        """Write one byte to worker device.  Same as write_n_bytes.

        Parameters
        ----------
        data : int, 8 bits of data
        """
        self.bus.writeto(self.bus_addr, data)

    def read_register_16bit(self, reg_addr):
        """Get the values from one registry

        Parameters
        ----------
        reg_addr : int, registry internal to the worker device to read

        Returns
        -------
        16 bit value of registry
        """

        x, y = self.bus.readfrom_mem(self.bus_addr, reg_addr, 2)
        return (x << 8) | y

    def write_register_16bit(self, reg_addr, data):
        """Write a 16 bit register.  Breaks 16 bit data into list of
        8 bit values.

        Parameters
        ----------
        reg_addr : int, register internal to the worker device
        data : int, 16 bit value to write

        """

        buff = bytearray(2)
        buff[0] = data >> 8
        buff[1] = data & 0xFF

        self.bus.writeto_mem(self.bus_addr, reg_addr, buff)

    def write_n_bytes(self, data):
        """Write bytes (n total) to worker device

        Parameters
        ----------
        data : iterable of bytes
        """

        self.bus.writeto(self.bus_addr, data)

    def read_n_bytes(self, n):
        """Write bytes (n total) to worker device

        Parameters
        ----------
        n : int, number of bytes to read

        Returns
        -------
        iterable of bytes
        """

        return self.bus.readfrom(self.bus_addr, n)
