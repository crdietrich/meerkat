"""Atlas Scientific I2C Drivers for Raspberry PI & MicroPython"""


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

        # information about this device
        self.device = DeviceData('Atlas_Base')
        self.device.description = ('')
        self.device.urls = 'www.atlas-scientific.com'
        self.device.active = None
        self.device.error = None
        self.device.bus = repr(self.bus)
        self.device.manufacturer = 'Atlas Scientific'
        self.device.version_hw = '1.0'
        self.device.version_sw = '1.0'
        self.device.accuracy = None
        self.device.precision = 'Varies'
        self.device.calibration_date = None

        """
        # data recording method
        if output == 'csv':
            self.writer = CSVWriter('Atlas_Base', time_format='std_time_ms')

        elif output == 'json':
            self.writer = JSONWriter('Atlas_Base', time_format='std_time_ms')
        else:
            pass  # holder for another writer or change in default
        self.writer.header = ['description', 'sample_n', 'not_set']
        self.writer.device = self.device.values()
        """

        # data recording information
        self.sample_id = None

        # data recording method
        self.writer_output = output
        self.csv_writer = CSVWriter("Atlas_Base", time_format='std_time_ms')
        self.csv_writer.device = self.device.__dict__
        self.csv_writer.header = ['description', 'sample_n', 'not_set']

        self.json_writer = JSONWriter("Atlas_Base", time_format='std_time_ms')
        self.json_writer.device = self.device.__dict__
        self.json_writer.header = self.csv_writer.header

    def query(self, command, n=31, delay=None, verbose=False):
        """Write a command to the i2c device and read the reply,
        delay between reply based on command value.

        Byte codes:

            First byte repsonse codes
                  0x1 = successful request
                  0x2 = syntax error
                0x254 = still processing, not ready
                0x255 = no data to send
            Filler byte
                  0x0 = filler (usually at the end of a reply)

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
            print("Sent:", command)

        self.bus.write_n_bytes(*[byte_command])

        if delay is not None:
            time.sleep(delay/1000)

        if n != 0:
            reply = self.bus.read_n_bytes(n=n)

            reply_mapper = {0: 'Filler',
                            1: 'Success',
                            254: 'Still processing',
                            255: 'No data'}

            if verbose:
                # print the response code that is in position 0 of reply
                reply_0 = reply[0]
                print("Reply:", reply_mapper[reply_0])

            # filter out response codes and filler bytes
            reply_bytes = bytearray([])
            for reply_n in reply:
                if reply_n not in [0x0, 0x1, 0x2, 0x254, 0x255]:
                    reply_bytes.append(reply_n)
            reply_bytes = bytes(reply_bytes)
            reply_bytes = reply_bytes.decode('utf-8')

            if verbose:
                print("Formatted and trimmed reply:", reply_bytes)

            return reply_bytes

    def led_on(self):
        """Turn on status LED until another character is set"""
        self.query(b'L,1', n=0)

    def led_off(self):
        """Turn off status LED"""
        self.query(b'L,0', n=0)

    def find_start(self):
        """Blink white LED until another character is set"""
        self.query(b'Find', n=0)

    def find_stop(self):
        """Stop white LED from blinking"""
        self.query(0x01, n=0)

    def info(self):
        """Get device information

        Returns
        -------
        device: str, device type
        firmware : str, firmware version
        """

        _r = self.query(b'i', n=15, delay=350)
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

    def get(self, description='no_description', n=1, delay=0):
        """Get formatted output, assumes subclass has method 'measure'

        Parameters
        ----------
        description : char, description of data sample collected
        n : int, number of samples to record in this burst
        delay : float, seconds to delay between samples if n > 1

        Returns
        -------
        data : list, data that will be saved to disk with self.write containing:
            description : str
            c : float, sensor measurement
        """

        data_list = []
        for m in range(n):
            measure = self.measure()
            if isinstance(measure, float):
                measure = [measure]
            data = [description, m] + measure
            data_list.append(data)
            if n == 1:
                return data_list[0]
            time.sleep(max(self.long_delay, delay))
        return data_list

    def publish(self, description='NA', n=1, delay=0):
        """Output relay status data in JSON.

        Parameters
        ----------
        description : str, description of data sample collected
        n : int, number of samples to record in this burst
        delay : float, seconds to delay between samples if n > 1

        Returns
        -------
        str, formatted in JSON with keys:
            description: str, description of sample under test
            measurement : float, measurement made
        """
        data_list = []
        for m in range(n):
            measure = self.measure()
            if isinstance(measure, float):
                measure = [measure]
            data_list.append(self.json_writer.publish([description, m] + measure))
            if n == 1:
                return data_list[0]
            time.sleep(max(self.long_delay, delay))
        return data_list

    def write(self, description='NA', n=1, delay=0):
        """Format output and save to file, formatted as either .csv or .json.

        Parameters
        ----------
        description : str, description of data sample collected
        n : int, number of samples to record in this burst
        delay : float, seconds to delay between samples if n > 1

        Returns
        -------
        None, writes to disk the following data:
            description : str, description of sample
            sample_n : int, sample number in this burst
            voltage, float, Volts measured at the shunt resistor
            current : float, Amps of current accross the shunt resistor
        """
        wr = {"csv": self.csv_writer,
              "json": self.json_writer}[self.writer_output]
        for m in range(n):
            measure = self.measure()
            if ((isinstance(measure, float)) or 
                (isinstance(measure, int)) or 
                (isinstance(measure, str))):
                    measure = [measure]
            wr.write([description, m] + measure)
            time.sleep(max(self.long_delay, delay))

class pH(Atlas):
    def __init__(self, bus_n, bus_addr=0x63, output='csv'):
        super(pH, self).__init__(bus_n, bus_addr, output)

        # information about this device
        self.device.name = 'Atlas_pH'
        self.device.description = ('')
        self.device.urls = 'www.atlas-scientific.com/ph.html'
        self.device.active = None
        self.device.error = None
        self.device.bus = repr(self.bus)
        self.device.manufacturer = 'Atlas Scientific'
        self.device.version_hw = '1.0'
        self.device.version_sw = '1.0'
        self.device.accuracy = None
        self.device.precision = 'Varies'
        self.device.calibration_date = None

        self.csv_writer.name = "Atlas_pH"
        self.csv_writer.header = ['description', 'sample_n', 'pH']
        self.json_writer.header = self.json_writer.header
        self.json_writer.header = self.csv_writer.header

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
        float : measurement to three decimal places
        """

        _r = self.query(b'R', n=7, delay=950, verbose=verbose)
        _r = float(_r)
        return _r

class Oxygen(Atlas):
    def __init__(self):
        pass

class Conductivity(Atlas):
    def __init__(self, bus_n, bus_addr=0x64, output='csv'):
        super(Conductivity, self).__init__(bus_n, bus_addr, output)


        self.measure_mapper = {'EC': 'conductivity',
                               'TDS': 'total_dissolved_solids',
                               'S': 'salinity',
                               'SG': 'specific_gravity'}

        # information about this device
        self.device.name = 'Atlas_Conductivity'
        self.device.description = ('Water conductivity')
        self.device.urls = 'www.atlas-scientific.com/conductivity.html'
        self.device.active = None
        self.device.error = None
        self.device.bus = repr(self.bus)
        self.device.manufacturer = 'Atlas Scientific'
        self.device.version_hw = '1.0'
        self.device.version_sw = '1.0'
        self.device.units = 'uS/cm'  # this assumes it's in conductivity mode!
        self.device.accuracy = '+/-2%'
        self.device.precision = '0.07-500000 uS/cm'
        self.device.calibration_date = None

        # metadata information
        self.csv_writer.name = self.json_writer.name = "Atlas_Conductivity"

        # update the output header
        _o = self.output_get()

    def cal_set_dry(self):
        """Execute dry calibration.  Manual says delay 600ms,
        delay set here to 650ms.

        Parameters
        ----------
        n : int, calibration value
        """
        _r = self.query(b"CAL,dry", n=0, delay=650)

    def cal_set_one(self, n):
        """Single point calibration.  Manual says delay 600ms,
        delay set here to 650ms.

        Parameters
        ----------
        n : int, calibration value
        """
        _r = self.query(bytes("CAL,{}".format(n), encoding='utf-8'),
                        n=0,
                        delay=650)

    def cal_set_low(self, n):
        """Low point of two point calibration.  Manual says delay 600ms,
        delay set here to 650ms.

        Parameters
        ----------
        n : int, calibration value
        """
        _r = self.query(bytes("CAL,low,{}".format(n), encoding='utf-8'),
                        n=0,
                        delay=650)

    def cal_set_high(self, n):
        """High point of two point calibration.  Manual says delay 600ms,
        delay set here to 950ms.

        Parameters
        ----------
        n : int, calibration value
        """
        _r = self.query(bytes("CAL,high,{}".format(n), encoding='utf-8'),
                        n=0,
                        delay=650)

    def cal_clear(self):
        """Clear calibration points (dry, one, low, high)"""

        _r = self.query(bytes("CAL,clear", encoding='utf-8'),
                        n=0,
                        delay=0)

    def cal_get(self, verbose=False):
        """Get calibration status:
            0 = no calibration
            1 = 1 point calibration
            2 = 2 point calibration

        Parameters
        ----------
        verbose : bool, print debug statements

        Returns
        -------
        int, number of calibration points
        """

        _n = self.query(b'Cal,?', n=7, delay=950, verbose=verbose)
        _n = _n.split(",")
        _n = int(_n[1])
        return _n

    def set_probe_type(self, k, verbose=False):
        """Set the probe type.

        Parameters
        ----------
        k : float, K value for probe being used

        """

        _r = self.query(bytes("K,{}".format(k), encoding='utf-8'), n=0)

    def get_probe_type(self, verbose=False):
        """Return the probe type.

        Returns
        -------
        k : float, K value for probe being used

        """

        _r = self.query(bytes("K,?", encoding='utf-8'), n=10, delay=350)
        _r = _r.split(",")
        k = float(_r[1])
        return k

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
        _r = _r.split(',')
        temp = float(_r[1])
        return temp

    def output_conductivity_on(self):
        """Turn on conductivity output"""

        _r = self.query(b"O,EC,1", n=0)

    def output_conductivity_off(self):
        """Turn off conductivity output"""

        _r = self.query(b"O,EC,0", n=0)

    def output_TDS_on(self):
        """Turn on TDS output"""

        _r = self.query(b"O,TDS,1", n=0)

    def output_TDS_off(self):
        """Turn off TDS output"""

        _r = self.query(b"O,TDS,0", n=0)

    def output_salinity_on(self):
        """Turn on salinity output"""

        _r = self.query(b"O,S,1", n=0)

    def output_salinity_off(self):
        """Turn off salinity output"""

        _r = self.query(b"O,S,0", n=0)

    def output_specific_gravity_on(self):
        """Turn on specific gravity output"""

        _r = self.query(b"O,SG,1", n=0)

    def output_specific_gravity_off(self):
        """Turn off specific gravity  output"""

        _r = self.query(b"O,SG,0", n=0)

    def output_get(self):
        """Get status for all output formats: EC, TDS, S, SG

        Returns
        -------
        list : each output format displayed or 'no output' if all disabled
        """

        _r = self.query(b'O,?', n=20, delay=350)
        _r = _r.split(',')[1:]

        """
        for k in self.measure_mapper.keys():
            print(k)

        for m in _r:
            print("|", m, "|")
            try:
                print(self.measure_mapper[m.strip()])
            except:
                for i in m:
                    print('='*5)
                    print(i)
                    print("-"*5)
        """
        _measure_types = [self.measure_mapper[m.strip()] for m in _r]
        self.csv_writer.header = ['description', 'sample_n'] + _measure_types
        self.json_writer.header = self.csv_writer.header

        return _r

    def measure(self, verbose=False):
        """Take a Conductivity measurement

        Parameters
        ----------
        verbose : bool, print debug statements

        Returns
        -------
        str : conductivity, total solids, salinity, specific gravity
            measurement, depending on state as
        """

        _r = self.query(b'R', n=40, delay=650, verbose=verbose)
        _r = [m for m in _r.split(',')]
        return _r
