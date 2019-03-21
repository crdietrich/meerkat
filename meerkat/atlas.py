"""Atlas Scientific I2C Sensors

2018 Colin Dietrich
MIT License"""


from meerkat.base import I2C, DeviceData, time 
from meerkat.data import CSVWriter, JSONWriter


def scan(bus_n):
    """Scan I2C bus for devices

    Parameters
    ----------
    bus_n : int, I2C bus to scan
    """
    
    device_descriptions = [[0x61, "DO", "Dissolved Oxygen"], 
                           [0x62, "ORP", "Oxidation Reduction"],
                           [0x63, "pH", "pH"],
                           [0x64, "EC", "Conductivity"]]
    
    for bus_addr, code, description in devices:
        try:
            dev = Atlas(bus_n=bus_n, bus_addr=bus_addr)
            device, firmware = dev.info()
            print("{} found at: {}".format(description, bus_addr))
        except:
            pass

class Atlas:
    """Base class for Atlas Scientific sensors"""


    def __init__(self, bus_n, bus_addr, output='csv'):
        """Initialize worker device on i2c bus.

        Parameters
        ----------
        bus_n : int, i2c bus number on Controller
        bus_addr : int, i2c bus number of this Worker device        
        """

        # i2c bus
        self.bus = I2C(bus_n=bus_n, bus_addr=bus_addr)


        # time to wait for conversions to finish
        self.short_delay   = 0.3  # seconds for regular commands
        self.long_delay    = 1.5  # seconds for readings
        self.cal_delay     = 3.0  # seconds for calibrations

        # device name, pH, conductivity, etc
        self.name = None


    def read(self, n=31, verbose=False):
        """Read a specified number of bytes from I2C, then parse the result

        Parameters
        ----------
        n : int, number of bytes of data to read
        flip_MSB : bool, flip MSB of bytes
        verbose : bool, print debug statements

        Returns
        -------
        (bool, str) : Success/Error, values read from sensor
        """

        r = self.bus.read_n_bytes(n)
        return r

    def query(self, command, n=31, delay=None, verbose=False):
        """Write a command to the i2c device and read the reply, 
        delay between reply based on command value.
        
        Parameters
        ----------
        command : str, command to execute on the device
        n : int, number of bytes to read
        delay : float, number of milliseconds to delay before reading response
        verbose : bool, print debug statements
        
        Returns
        -------
        str : response, may require further parsing
        """
        
        if verbose:        
            print("Input Type: ", type(command))

        if (type(command) == int) or (type(command) == bytes):
            byte_command = command
        else:
            byte_command = [ord(x) for x in command]

        if verbose:
            print("Bytes sent:", command)

        self.bus.write_n_bytes(*byte_command)
        
        if delay is not None:
            time.sleep(delay/1000)

        if n != 0:
            return self.bus.read_n_bytes(n=n)

    def info(self):
        """Get device information

        Returns
        -------
        device: str, device type 
        firmware : str, firmware version
        """

        _r = self.query(b'i', n=15, delay=350)
        _r = _r.decode('utf-8')
        _, device, firmware = _r.split(",")
        return device, firmware

    def status(self):
        """Get device status

        Returns
        -------
        restart code : str, one character meaning
            P = power off
            S = software reset
            B = brown out
            W = watchdog
            U = unknown
        vcc : float, supply voltage of input to device
        """
        _r = self.query(b'Status', n=15, delay=350)
        _r = _r.decode('utf-8')
        _, restart_code, vcc = _r.split(",")
        return restart_code, float(vcc)

    def sleep(self):
        """Put device to sleep.  Any byte sent wakes."""
        _r = self.query(b'Sleep', n=0)
    
    def wake(self):
        """Wake device from sleep state"""
        _r = self.query(0x01, n=0)

    def plock_status(self):
        """Get protocol lock status"""
        _r = self.query(b'Plock,?', n=9, delay=350, verbose=verbose)
        _r = _r.decode('utf-8')
        _, plock_state = _r.split(",")
        return int(plock_state)

    def plock_on(self):
        """Lock device into I2C mode"""
        _r = self.query(b'Plock,1', n=0)

    def plock_off(self):
        """Unlock device from I2C mode"""
        _r = self.query(b'Plock,0', n=0)

    def reset(self):
        """Completely reset device.  Clears calibration, sets LED on and 
        enables reponse codes"""
        _r = self.query(b'Factory', n=0)

    def change_i2c_bus_address(self, n):
        """Change the device I2C bus address - device will not be accessible
        until contacted at new I2C address.  Response is device reboot.

        Parameters
        ----------
        n : int, I2C address, can be any number 1-127 inclusive
        """
        _r = self.query(bytes("I2C,{}".format(n), encoding='utf-8'), n=0)


class pH(Atlas):
    def __init__(self, bus_n, bus_addr=0x63):
        super(pH, self).__init__(bus_n, bus_addr)
        
    def start_find(self):
        """Blink white LED until another character is set"""
        self.query(b'Find', n=0)

    def stop_find(self):
        """Stop white LED from blinking"""
        self.query(b'Stop', n=0)

    def cal_set_mid(self, n):
        """Single point calibration at midpoint.  Manual says delay 900ms,
        delay set here to 950ms.

        Parameters
        ----------
        n : float, calibration value to 2 decimal places
        """
        _r = self.query(bytes("CAL,mid,{:.2f}".format(n), encoding='utf-8'), 
                        n=0,
                        delay=950)

    def cal_set_low(self, n):
        """Single point calibration at lowpoint.  Manual says delay 900ms,
        delay set here to 950ms.

        Parameters
        ----------
        n : float, calibration value to 2 decimal places
        """
        _r = self.query(bytes("CAL,low,{:.2f}".format(n), encoding='utf-8'), 
                        n=0,
                        delay=950)

    def cal_set_high(self, n):
        """Single point calibration at highpoint.  Manual says delay 900ms,
        delay set here to 950ms.

        Parameters
        ----------
        n : float, calibration value to 2 decimal places
        """
        _r = self.query(bytes("CAL,high,{:.2f}".format(n), encoding='utf-8'), 
                        n=0,
                        delay=950)

    def cal_clear(self):
        """Clear calibration points (mid, low, high)"""

        _r = self.query(bytes("CAL,clear", encoding='utf-8'), 
                        n=0,
                        delay=0)

    def cal_get(self, verbose=False):
        """Get calibration status:
            0 = no calibration
            1 = 1 point calibration
            2 = 2 point calibration
            3 = 3 point calibration

        Parameters
        ----------
        verbose : bool, print debug statements

        Returns
        -------
        int, number of calibration points
        """
        
        _r = self.query(b'Cal,?', n=7, delay=950, verbose=verbose)
        _r = _r.decode('utf-8') 
        _r = _r.split(",")
        return int(_r[1])
        return _r

    def cal_slope(self, verbose=False):
        """Return the calibration error relative to acid and base ideals

        Returns
        -------
        a : float, precentage delta from ideal fit
        b : float, precentage delta from ideal fit
        """
        _r = self.query(b'Slope,?', n=24, delay=350, verbose=verbose)
        _r = _r.decode('utf-8')
        _r = _r.split(",")
        acid_cal = float(_r[1])
        base_cal = float(_r[2])
        return acid_cal, base_cal

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
        _r = self.query(bytes("T,{:.2f}".format(t), encoding='utf-8'), 
                        n=0,
                        verbose=verbose)

    def temp_get(self, verbose=False):
        """Get temperature currently set for compensation calculations

        Parameters
        ----------
        verbose: bool, print debug statements
        
        Returns
        -------
        float, temperature in degrees C accurate to 2 decimal places
        """

        _r = self.query(b'T,?', n=9, delay=350, verbose=verbose)
        _r = _r.decode('utf-8')
        _r = _r.split(',')
        temp = float(_r[1])        
        return temp
        
    def measure(self, verbose=False):
        """Take a pH measurement

        Parameters
        ----------
        verbose : bool, print debug statements

        Returns
        -------
        str : measurement to three decimal places
        """
        
        _r = self.query(b'R', n=7, delay=950, verbose=verbose)
        _r = _r.decode('utf-8')
        _r = float(_r)
        return _r

class Oxygen(Atlas):
    def __init__(self):
        pass

class Conductivity(Atlas):
    def __init__(self):
        pass

#if verbose:
#    print("Bytes reply:", r)

# 1 == successful request
#if (r[0] == 1):
#    return True, r
#   2 = syntax error
# 254 = still processing, not ready
# 255 = no data to send
#else:
#    return False, "Error " + str(r[0])

#restart_code = {'P': 'powered off', 'S': 'software reset',
#                            'B': 'brown out', 'W': 'watchdog',
#                            'U': 'unknown'}
