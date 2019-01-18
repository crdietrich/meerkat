"""Atlas Scientific I2C Sensors

2018 Colin Dietrich
MIT License"""

import io
import fcntl
import time


class Atlas:
    """Base class for Atlas Scientific sensors"""

    long_timeout    = 1.5 # the timeout needed to query readings and calibrations
    short_timeout   = 0.3 # timeout for regular commands
    default_bus     = 1   # the default i2c bus newer pis, older ones used 0

    def __init__(self, bus, i2c_addr):

        self.file_read = io.open("/dev/i2c-"+str(bus), "rb", buffering = 0)
        self.file_write = io.open("/dev/i2c-"+str(bus), "wb", buffering = 0)

        # initializes I2C to either a user specified or default address
        self.set_i2c_address(i2c_addr)

        self.name = None

    def get_name(self):
        """For terminal printing and identification, move to subclass?"""
        names = {"DO": "Dissolved Oxygen", "ORP": "Oxidation Reduction",
                 "EC": "Conductivity", "pH": "pH", }

        while self.name is None:
            try:
                q = self.query("I")
                info = string.split(q[1], ",")[1]
                self.name = names[info]
            except IndexError:
                pass
            except KeyError:
                pass


    def set_i2c_address(self, bus_addr):
        """Set the I2C communications slave address. The commands for I2C dev 
        using the ioctl functions are specified in the i2c-dev.h file 
        from i2c-tools.
        
        Parameters
        ----------
        bus_addr : int or hex number
        """
        I2C_SLAVE = 0x703
        fcntl.ioctl(self.file_read, I2C_SLAVE, bus_addr)
        fcntl.ioctl(self.file_write, I2C_SLAVE, bus_addr)

    def write(self, b):
        """Write to the i2c bus
        
        Parameters
        ----------
        b : bytes, values to write to i2c device
        """
        self.file_write.write(b)
        
    def _read(self, n=31):
        """Read from the i2c bus.  Will continue to read even if device has nothing
        more to send, extra bytes will be zeros.
        
        Parameters
        ----------
        n : int, number of bytes to read
        """
        return self.file_read.read(n)

    def read(self, n=31, verbose=False):
        """Read a specified number of bytes from I2C, then parses and displays the result

        Parameters
        ----------
        num_of_bytes : int, number of bytes of data to read

        Returns
        -------
        (bool, str) : Success/Error, values read from sensor
        """

        r = self.file_read.read(n)
        if verbose:
            print("Bytes reply:", r)
        
        # 1 == successful request
        if (r[0] == 1):
            # change MSB to 0 to handle pi behavior
            r_str = "".join([chr(x & ~0x80) for x in r[1:] if x != 0])
            return True, r_str
        #   2 = syntax error
        # 254 = still processing, not ready
        # 255 = no data to send
        else:
            return False, "Error " + str(r[0])

    def query(self, command, n=31, verbose=False):
        """Write a command to the i2c device and read the reply, delay between reply
        based on command value.
        
        Parameters
        ----------
        command : str, command to execute on the device
        n : int, number of bytes to read
        verbose : bool, print debug statements
        
        Returns
        -------
        str : response from device, may include commas and require further parsing
        """
        
        if type(command) == str:
            byte_command = bytes(command, 'utf-8')
        else:
            byte_command = command
            command = command.decode('utf-8')

        if verbose:
            print("Bytes sent:", command)

        self.write(byte_command)
        
        if command.upper().startswith("R"):
            time.sleep(self.long_timeout)
        elif command.upper().startswith("CAL"):
            time.sleep(4)
        else:
            time.sleep(self.short_timeout)

        return self.read(n=n, verbose=verbose)

    def _command(self, command, value=None, verbose=False):
        if value is None:
            b = bytes(command, 'utf-8')
        else:
            b = bytes("{},{:.2f}".format(command, value), 'utf-8')
        c, v = self.query(b)
        if verbose:
            print(c, v)
        return c

    def info(self, verbose=False):
        """Get device information

        Parameters
        ----------
        verbose : bool, print debug statements

        Returns
        -------
        str : device type and firmware version delimited with a comma
        """
        c, v = self._command("i", verbose=verbose)
        if c:
            v = v.split(",")
            return ",".join(v[1:])
        else:
            return v

    def status(self, verbose=False):
        c, v = self.query('Status', verbose=verbose)
        if c:        
            v = v.split(",")
            restart_code = {'P': 'powered off', 'S': 'software reset',
                            'B': 'brown out', 'W': 'watchdog',
                            'U': 'unknown'}[v[1]]
            return restart_code, v[2]
        else:
            return v

    def plock_status(self, verbose=False):
        c, v = self.query('Plock,?', verbose=verbose)
        if c:
            return v

    def plock_on(self):
        pass

    def plock_off(self):
        pass

    def close(self):
        """Close both io file objects bound to the i2c bus"""
        self.file_read.close()
        self.file_write.close()


class pH(Atlas):
    def __init__(self, bus, i2c_addr):
        super(pH, self).__init__(bus, i2c_addr)
        
    def start_find(self):
        """Blink white LED until another character is set"""
        self.write(b'Find')

    def stop_find(self):
        """Stop white LED from blinking"""
        self.write(b'Stop')

    def cal_set_low(self, value, verbose=False):
        c = self._command('CAL,low', value, verbose=verbose)
        return c        

    def cal_set_mid(self, value, verbose=False):
        c = self._command('CAL,mid', value, verbose=verbose)
        return c

    def cal_set_high(self, value, verbose=False):
        c = self._command('CAL,high', value, verbose=verbose)
        return c

    def cal_clear(self, verbose=False):
        c = self._command(b'CAL,clear', verbose=verbose)
        return c

    def cal_get(self, verbose=False):
        """Get calibration status:
            0 = no calibration
            1 = 1 point calibration
            2 = 2 point calibration
            3 = 3 point calibration

        Parameters
        ----------
        verbose : bool, print debug statements
        """
        
        c, v = self.query("Cal,?", verbose=verbose)
        if c:
            v = v.split(",")
            return v[1]
        else:
            return v

    def cal_slope(self, verbose=False):
        """Return the calibration error relative to acid and base ideals

        Returns
        -------
        a : float, precentage delta from ideal fit
        b : float, precentage delta from ideal fit
        """
        c, v = self.query("Slope,?", verbose=verbose)
        if c:
            v = v.split(",")
            return v[2], v[3]
        else:
            return v

    def temp_set(self, t, verbose=False):
        """Set the temperature for compensation calculations

        Parameters
        ----------
        t : float, temperature in degrees C accurate to 2 decimal places
        verbose: bool, print debug statements
        
        Returns
        -------
        boolean, command success
        """

        c = self._command('T', t, verbose=verbose)
        return c

    def temp_get(self, verbose=False):
        """Get temperature currently set for compensation calculations

        Parameters
        ----------
        verbose: bool, print debug statements
        
        Returns
        -------
        float, temperature in degrees C accurate to 2 decimal places
        """

        c, v = self.query("T,?", verbose=verbose)
        if c:
            v = v.split(",")
            return v[1]
        else:
            return v

    def measure(self, verbose=False):
        """Make a measurement

        Parameters
        ----------
        verbose : bool, print debug statements

        Returns
        -------
        str : measurement to three decimal places
        """
        
        c, v = self.query("R", verbose=verbose)
        if c:
            return v

class Oxygen(Atlas):
    def __init__(self):
        pass

class Conductivity(Atlas):
    def __init__(self):
        pass

