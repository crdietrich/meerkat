"""Wrapper Library for controlling I2C devices connected to MicroPython.
Tested with Adafruit Py Qt S2 Espressif
Note: CircuitPython wraps busio.I2C with board.I2c and board.STEMMA_I2C
https://docs.circuitpython.org/en/latest/shared-bindings/busio/index.html#busio.I2C
https://docs.circuitpython.org/projects/busdevice/en/latest/index.html
"""

from board import I2C
from board import STEMMA_I2C


class WrapI2CBase:
    def __init__(self):
        """Set the I2C communications to the Target device specified by
        the address

        Parameters
        ----------
        bus_n : int, i2c bus connected to Target devices
        bus_addr : hex, address of Target device on i2c bus
        frequency : int, frequency of i2c bus.  Note MicroPython arg is 'frequencey'
            whereas PyCom term is 'baudrate'
        """
        self.bus      = None
        self.bus_addr = None

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

    def read_n_bytes(self, n):
        """Read bytes (n total) from Target device.
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
        """
        buff = bytearray()
        while not self.bus.try_lock():
            time.sleep(0)
        self.bus.readfrom(self.bus_addr, buff, 0, n)
        self.bus.unlock()
        return buff
        """

        buff = bytearray(n)
        while not self.bus.try_lock():
            time.sleep(0)
        self.bus.readfrom_into(self.bus_addr, buff)
        self.bus.unlock()
        return buff
        
    def write_n_bytes(self, data):
        """Write bytes (n total) to Target device

        Parameters
        ----------
        data : iterable of bytes
        """
        buff = bytearray(data)
        while not self.bus.try_lock():
            time.sleep(0)
        self.bus.writeto(self.bus_addr, buff)
        self.bus.unlock()
        
    ### 8bit Register ###

    def read_register_8bit(self, reg_addr):
        """Get the values from one registry

        Parameters
        ----------
        reg_addr : int, registry internal to the Target device to read

        Returns
        -------
        16 bit value of registry
        """
        buff = bytearray(1)
        while not self.bus.try_lock():
            time.sleep(0)
        self.bus.writeto_then_readfrom(self.bus_addr, bytes([reg_addr]), buff)
        self.bus.unlock()
        return buff[0]

    def write_register_8bit(self, reg_addr, data):
        """Write a 16 bit register.  Breaks 16 bit data into list of
        8 bit values.

        Parameters
        ----------
        reg_addr : int, register internal to the Target device
        data : int, 8 bit value to write
        """
        while not self.bus.try_lock():
            time.sleep(0)
        self.bus.writeto(self.bus_addr, bytearray([reg_addr, data]))
        self.bus.unlock()
        
    ### 16bit Register ###

    def read_register_16bit(self, reg_addr):
        """Get the values from one registry

        Parameters
        ----------
        reg_addr : int, registry internal to the Target device to read

        Returns
        -------
        16 bit value of registry
        """

        x, y = self.read_register_nbyte(reg_addr, 2)
        return (x << 8) | y

    def write_register_16bit(self, reg_addr, data):
        """Write a 16 bit register.  Breaks 16 bit data into list of
        8 bit values.

        Parameters
        ----------
        reg_addr : int, register internal to the Target device
        data : int, 16 bit value to write
        """
        buff = bytearray(3)
        buff[0] = reg_addr
        buff[1] = data >> 8
        buff[2] = data & 0xFF
        while not self.bus.try_lock():
            time.sleep(0)
        self.bus.writeto(self.bus_addr, buff, 0, len(buff))
        self.bus.unlock()

    ### nbit Register ###

    def read_register_nbyte(self, reg_addr, n):
        """Get the values from one registry

        Parameters
        ----------
        reg_addr : int, registry internal to the Target device to read
        n : int, number of bits to read

        Returns
        -------
        n bit values
        """

        self.write_n_bytes(reg_addr)
        while not self.bus.try_lock():
            time.sleep(0)
        buff = bytearray(n)
        self.bus.writeto_then_readfrom(self.bus_addr, bytes([reg_addr]), buff) #, 0, 1, 0, len(buff))
        self.bus.unlock()
        return buff


class WrapI2C(WrapI2CBase):

    def __init__(self):
        super().__init__()
        self.bus = I2C()


class WrapSTEMMA_I2C(WrapI2CBase):

    def __init__(self):
        super().__init__()
        self.bus = STEMMA_I2C()
