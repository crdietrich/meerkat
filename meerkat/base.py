# -*- coding: utf-8 -*-
"""Meerkat device methods"""
__author__ = "Colin Dietrich"
__copyright__ = "2018"
__license__ = "MIT"

try:
    import ujson as json
except ImportError:
    import json


try:
    import pyb  # pyboard import
    rtc = pyb.RTC()
    _struct_time = rtc.now

except ImportError:

    try:
        import machine  # CircuitPython import
        rtc = machine.RTC()
        _struct_time = rtc.now
    except ImportError:
        try:
            from datetime import datetime  # CPython 3.7


            def _struct_time():
                t = datetime.now()
                return t.year, t.month, t.day, t.hour, t.minute, t.second, t.microsecond
        except ImportError:
            raise


iso_time_fmt = '%Y-%m-%dT%H:%M:%S.%f%z'
std_time_fmt = '%Y-%m-%d %H:%M:%S.%f%z'
file_time_fmt = '%Y_%m_%d_%H_%M_%S_%f'


def generate_UUID():
    # placeholder for UUID    
    return 'non-compliant-UUID'


def scan_I2C(i2c_bus):
    found_address = i2c_bus.scan()
    print('Found I2C devices at:', found_address)


def bit_get(idx, value):
    """Get bit at index idx in value

    Parameters
    ----------
    idx : int, bit index to set
        (binary notation: MSB left, LSB right - not Python indexing!)
    value : bool, value of bit
    """
    return value & (1 << idx) != 0


def bit_set(idx, value):
    """Set bit at index idx in value to 1

    Parameters
    ----------
    idx : int, bit index to set
        (binary notation: MSB left, LSB right - not Python indexing!)
    value : value to change bit
    """
    return value | (1 << idx)


def bit_clear(idx, value):
    """Set bit at index idx in value to 0

    Parameters
    ----------
    idx : int, bit index to set
        (binary notation: MSB left, LSB right - not Python indexing!)
    value : value to change bit
    """
    return value & ~(1 << idx)


def bit_toggle(value, bit, boolean):
    """Toggle bit in value to boolean
    
    Parameters
    ----------
    value : 16 bit int, value to change bit
    bit : int, bit index to set
        (binary notation: MSB left, LSB right - not Python indexing!)
    boolean : boolean, direction to toggle bit
    
    Returns
    -------
    value with toggled bit
    """
    
    if boolean is True:
        return bit_set(value, bit)
    elif boolean is False:
        return bit_clear(value, bit)


def twos_comp_to_dec(value, bits):
    """Convert Two's Compliment format to decimal"""
    if (value & (1 << (bits - 1))) != 0:
        value = value - (1 << bits)
    return value


class TimePiece(object):

    def __init__(self, str_format):

        self.str_format = str_format  # one of 'iso' or 'std'
        if self.str_format == 'iso':
            self.str_format_spec = iso_time_fmt
        else:
            self.str_format_spec = std_time_fmt

    def __repr__(self):
        return str(self.__dict__)

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True)

    @staticmethod
    def get_time(str_format='{:02d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}'):
        t = _struct_time()
        st = str_format
        return st.format(t[0], t[1], t[2], t[3], t[4], t[5])

    def get_ftime(self):
        """Get filename with timestamp, accurate to the second
        """

        str_format = '{:02d}_{:02d}_{:02d}_{:02d}_{:02d}_{:02d}'
        return self.get_time(str_format)

    def get_iso_time(self):
        str_format = '{:02d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}'
        return self.get_time(str_format)

    @staticmethod
    def get_time_ms():
        """Cross plateform timestamp in milliseconds

        Returns
        -------
        """
        t = _struct_time()
        st = '{:02d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}.{:06}'
        return st.format(t[0], t[1], t[2], t[3], t[4], t[5], t[6])


class I2C2(object):
    """Generic I2C Bus standardized API"""
    
    def __init__(self, i2c_bus):
        if hasattr(i2c_bus, 'readfrom_mem'):
            self.mem_read = i2c_bus.readfrom_mem
        else:
            self.mem_read = i2c_bus.mem_read
        
        if hasattr(i2c_bus, 'writeto_mem'):
            self.mem_write = i2c_bus.writeto_mem
        else:
            self.mem_write = i2c_bus.mem_write
        self.scan = i2c_bus.scan
        

class DeviceData(object):
    """Base class for device driver metadata"""
    def __init__(self, device_name):
        
        self.name = device_name
        self.description = None
        self.urls = None
        self.manufacturer = None
        self.version_hw = None
        self.version_sw = None
        self.accuracy = None
        self.precision = None

        self.bus = None
        self.state = None  # TODO: clarify what these mean
        self.active = None #
        self.error = None
        self.dtype = None
        self.calibration_date = None

    def __repr__(self):
        return str(self.__dict__)

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True)


class DeviceCalibration(object):
    """Base class for device calibration"""

    def __init__(self):

        self.name = None
        self.description = None
        self.urls = None
        self.manufacturer = None
        self.version = None
        self.dtype = None
        self.date = None

    def __repr__(self):
        return str(self.__dict__)

    def to_json(self):
        """Convert all calibration information to a JSON string"""
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True)

    def from_json(self, json_str):
        """Read a JSON string of calibration information and as set attributes
        """

        self.__dict__ = json.loads(json_str)

    def to_file(self, filepath):
        """Write calibration information to a file in JSON.
        """
        with open(filepath, 'w') as f:
            f.write(self.to_json())

    def from_file(self, filepath):
        """Read JSON calibration information from file.
        all data must be JSON on 1st line.
        """
        with open(filepath, 'r') as f:
            self.from_json(f.readline())


class TestDevice(object):
    """Non-hardware test class"""
    def __init__(self, output=None):

        # TODO: make safe for MicroPython, leave here for now in Conda
        from collections import deque
        from math import sin, pi

        from meerkat.data import CSVWriter, JSONWriter

        # data bus placeholder
        self.bus = None
        self.bus_addr = None

        # what kind of data output to file
        self.output = output

        # types of verbose printing
        self.verbose = False
        self.verbose_data = False

        # thread safe deque for sharing and plotting
        self.q_maxlen = 300
        self.q = deque(maxlen=self.q_maxlen)
        self.q_prefill_zeros = False

        # realtime/stream options
        self.go = False
        self.unlimited = False
        self.max_samples = 1000

        # information about this device
        self.device = DeviceData('Software Test')
        self.device.description = 'Dummy data for software testing'
        self.device.urls = None
        self.device.manufacturer = None
        self.device.version_hw = None
        self.device.version_sw = None
        self.device.accuracy = None
        self.device.precision = None
        self.device.bus = None
        self.device.state = 'Test Not Running'
        self.device.active = False
        self.device.error = None
        self.device.dtype = None
        self.device.calibration_date = None

        # data writer placeholder
        self.writer = None

        if self.output is not None:
            if self.output == 'csv':
                self.writer = CSVWriter('Software Test')
            elif self.output == 'JSON':
                self.writer = JSONWriter('Software Test')
            self.writer.header = ['index', 'degrees', 'amplitude']
            self.writer.device = self.device.__dict__

        # example data of one 360 degree, -1 to 1 sine wave
        self._deg = [n for n in range(360)]
        self._amp = [sin(d * (pi/180.0)) for d in self._deg]
        self._test_data = list(zip(self._deg, self._amp))

    @staticmethod
    def _cycle(iterable):
        """Copied from Python 3.7 itertools.cycle example"""
        saved = []
        for element in iterable:
            yield element
            saved.append(element)
        while saved:
            for element in saved:
                yield element

    def run(self, delay=0, index='count'):
        """Run data collection"""

        # TODO: make safe for MicroPython, leave here for now in Conda
        from time import sleep, time, ctime

        # used in non-unlimited acquisition
        count = 0

        self.q.clear()

        if self.q_prefill_zeros:
            for _ in range(self.q_maxlen):
                self.q.append((0, 0))

        if index == 'time':
            def get_index():
                return time()
        elif index == 'ctime':
            def get_index():
                return ctime()
        else:
            def get_index():
                return count

        for d, a in self._cycle(self._test_data):

            if not self.go:
                if self.verbose:
                    print('Test Stopped')
                break

            self.device.state = 'Test run() method'

            i = get_index()

            data = [i, d, a]

            if self.output is not None:
                self.writer.write(data)

            q_out = self.writer.stream(data)
            self.q.append(q_out)

            if self.verbose_data:
                print(q_out)

            if not self.unlimited:
                count += 1
                if count == self.max_samples:
                    self.go = False

            sleep(delay)
