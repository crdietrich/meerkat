"""Wrapper Library for controlling I2C devices connected to CircuitPython.
Tested with Adafruit Trinket M0"""

import busio
import board


class WrapI2C:
    def __init__(self, bus_n, bus_addr, frequency=100000):
        """Set the I2C communications to the worker device specified by
        the address

        Parameters
        ----------
        bus_n : dict, i2c bus connected to worker devices
        bus_addr : hex, address of worker device on i2c bus
        frequency : int, frequency of i2c bus.  Note MicroPython arg is 'frequencey'
            whereas PyCom term is 'baudrate'
        """
        self.bus_scl = bus_n['scl']
        self.bus_sda = bus_n['sda']
        self.bus = busio.I2C(scl=self.bus_scl, sda=self.bus_sda, frequency=frequency)
        self.bus_n = bus_n
        self.bus_addr = bus_addr

    def scan(self):
        """Scan I2C bus for devices

        Returns
        -------
        list of addresses found, in hex notation
        """
        #
        #
        while not self.bus.try_lock():
            pass
        scan = [hex(a) for a in self.bus.scan()]
        self.bus.unlock()
        return scan

    ### 1 byte = 8 bits ###

    def read_byte(self):
        """Read one byte from worker device

        Returns
        -------
        int, 8 bits of data
        """
        #
        #
        #
        return self.read_n_bytes(n=1)

    def write_byte(self, data):
        """Write one byte to worker device.  Same as write_n_bytes.

        Parameters
        ----------
        data : int, 8 bits of data
        """
        self.write_n_bytes(data)

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
        response = bytearray(n)
        while not self.bus.try_lock():
            pass
        self.bus.readfrom_into(self.bus_addr, response)
        self.bus.unlock()
        return response

    def write_n_bytes(self, data):
        """Write bytes (n total) to worker device

        Parameters
        ----------
        data : iterable of bytes
        """
        while not self.bus.try_lock():
            pass
        self.bus.writeto(self.bus_addr, bytes(data), stop=True)
        self.bus.unlock()

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
        response = bytearray(n)
        while not self.bus.try_lock():
            pass
        self.bus.writeto_then_readfrom(self.bus_addr, bytes(reg_addr), response)
        self.bus.unlock()
        return response

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
        return self.read_register_nbit(reg_addr, 1)

    def write_register_8bit(self, reg_addr, data):
        """Write a 16 bit register.  Breaks 16 bit data into list of
        8 bit values.

        Parameters
        ----------
        reg_addr : int, register internal to the worker device
        data : int, 8 bit value to write
        """
        buff = bytearray(2)
        buff[0] = reg_addr
        buff[1] = data
        self.write_n_bytes(buff)

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
        response = self.read_register_nbit(reg_addr, 2)
        x, y = response
        return (x << 8) | y

    def write_register_16bit(self, reg_addr, data):
        """Write a 16 bit register.  Breaks 16 bit data into list of
        8 bit values.

        Parameters
        ----------
        reg_addr : int, register internal to the worker device
        data : int, 16 bit value to write
        """
        buff = bytearray(3)
        buff[0] = reg_addr
        buff[1] = data >> 8
        buff[2] = data & 0xFF
        self.write_n_bytes(buff)
