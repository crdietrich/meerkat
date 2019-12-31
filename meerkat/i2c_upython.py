"""A wrapper API for I2C methods for MicroPython

Copyright (c) 2019 Colin Dietrich
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
        frequency : int, frequency of i2c bus.  Note MicroPython arg is 'frequencey'
            whereas PyCom term is 'baudrate'
        """
        self.bus = I2C(bus_n, I2C.MASTER, baudrate=frequency)
        self.bus_addr = bus_addr

    def scan(self):
        """Scan I2C bus for devices

        Returns
        -------
        list of addresses found, in hex notation
        """
        #
        #
        #
        #
        return [hex(a) for a in self.bus.scan()]

    ### 1 byte = 8 bits ###

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

    ### nbytes ###

    def read_n_bytes(self, n):
        """Read bytes (n total) from worker device.
        #
        #

        Parameters
        ----------
        n : int, number of bytes to read
        #

        Returns
        -------
        iterable of bytes
        """
        return self.bus.readfrom(self.bus_addr, n)
        #
        #
        #
        #

    def write_n_bytes(self, data):
        """Write bytes (n total) to worker device

        Parameters
        ----------
        data : iterable of bytes
        """
        self.bus.writeto(self.bus_addr, data)

    ### 8bit Register ###

    def read_register_8bit(self, reg_addr):
        """Get the values from one registry

        Parameters
        ----------
        reg_addr : int, registry internal to the worker device to read

        Returns
        -------
        16 bit value of registry
        """
        value = self.bus.readfrom_mem(self.bus_addr, reg_addr, 1)
        return value

    def write_register_8bit(self, reg_addr, data):
        """Write a 16 bit register.  Breaks 16 bit data into list of
        8 bit values.

        Parameters
        ----------
        reg_addr : int, register internal to the worker device
        data : int, 8 bit value to write
        """
        self.bus.write_bytes(self.bus_addr, reg_addr, data)

    ### 16bit Register ###

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

    ### nbit Register ###

    def read_register_nbit(self, reg_addr, n):
        """Get the values from one registry

        Parameters
        ----------
        reg_addr : int, registry internal to the worker device to read
        n : int, number of bits to read

        Returns
        -------
        n bit values
        """
        #
        return self.bus.readfrom_mem(self.bus_addr, reg_addr, n)
