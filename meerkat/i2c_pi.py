"""Wrapper Library for controlling I2C devices connected to Raspberry Pi (Linux)
Tested with Raspberry Pi 4"""

from meerkat import i2c_quickwire


class WrapI2C:
    def __init__(self, bus_n, bus_addr):
        """Set the I2C communications to the worker device specified by
        the address

        Parameters
        ----------
        bus_n : int, i2c bus connected to worker devices
        bus_addr : hex, address of worker device on i2c bus
        #
        #
        """
        self.bus = i2c_quickwire.I2CMaster(n=bus_n)
        self.bus_addr = bus_addr

    def scan(self):
        """Scan I2C bus for devices

        Returns
        -------
        list of addresses found, in hex notation
        """
        import subprocess
        bash_command = "i2cdetect -y 1"
        process = subprocess.Popen(bash_command.split(), stdout=subprocess.PIPE)
        output, error = process.communicate()
        return ["0x"+a.decode() for a in output.split()[16:] if (b":" not in a) and (a != b"--")]

    ### 1 byte = 8 bits ###

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

    ### nbytes ###

    def read_n_bytes(self, n, flip_MSB=True):
        """Read bytes (n total) from worker device, handle MSB flip behavior
        on Raspberry Pi.  Tested on Pi3 B v1.2 and Pi4 4GB.
        Atlas Sci source pointed to this solution.

        Parameters
        ----------
        n : int, number of bytes to read
        flip_MSB : bool, flip the Most Significant Bit (MSB)

        Returns
        -------
        iterable of bytes
        """
        values = self.bus.get(self.bus_addr, n)[0]
        return values
    
        #if flip_MSB:
        #    return bytes(bytearray(c & ~0x80 for c in values[1:] if c != 0))
        #else:
        #    return values

    def write_n_bytes(self, data):
        """Write bytes (n total) to worker device.

        Parameters
        ----------
        *data : iterable of bytes
        """
        self.bus.write_bytes(self.bus_addr, *data)

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
        value = self.read_register_nbit(reg_addr, 1)
        return int.from_bytes(value, byteorder='big')

    def write_register_8bit(self, reg_addr, data):
        """Write a 16 bit register.  Breaks 16 bit data into list of
        8 bit values.

        Parameters
        ----------
        reg_addr : int, register internal to the worker device
        data : int, 8 bit value to write
        """
        #
        #
        #
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
        value = self.read_register_nbit(reg_addr, 2)
        return int.from_bytes(value, byteorder='big')

    def write_register_16bit(self, reg_addr, data):
        """Write a 16 bit register.  Breaks 16 bit data into list of
        8 bit values.

        Parameters
        ----------
        reg_addr : int, register internal to the worker device
        data : int, 16 bit value to write
        """
        #
        #
        #
        self.bus.write_bytes(self.bus_addr, reg_addr, data >> 8, data & 0xff)

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
        self.bus.write_bytes(self.bus_addr, reg_addr)
        return self.bus.get(self.bus_addr, n)[0]
