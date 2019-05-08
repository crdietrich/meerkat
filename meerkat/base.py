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
    import utime as time
except ImportError:
    import time

try:
    from meerkat import i2c_upython
    I2C = i2c_upython.WrapI2C
except ImportError:
    from meerkat import i2c_pi
    I2C = i2c_pi.WrapI2C


def generate_UUID():
    # placeholder for UUID
    return 'non-compliant-UUID'


def scan_I2C(i2c_bus):
    found_address = i2c_bus.scan()
    print('Found I2C devices at:', found_address)

def bprint(v, n=16):
    """Print binary value with index numbers below in two rows
    Example register 14 = 1
                          4
    """
    b = bin(v)[2:]
    print(b.zfill(n))
    m = [str(x).zfill(2) for x in reversed(range(n))]
    print("".join([x[0] for x in m]))
    print("".join([x[1] for x in m]))

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


class Base:
    """Common methods for classes"""

    def __repr__(self):
        return str(self.values())

    def values(self):
        """Get all class attributes from __dict__ attribute
        except those prefixed with underscore ('_')

        Returns
        -------
        dict, of (attribute: value) pairs
        """
        d = {}
        for k, v in self.__dict__.items():
            if k[0] != '_':
                d[k] = v
        return d

    def to_json(self, indent=None):
        """Return all class objects from __dict__ except
        those prefixed with underscore ('_')

        Returns
        -------
        str, JSON formatted (attribute: value) pairs
        """
        return json.dumps(self, default=lambda o: o.values(),
                          sort_keys=True, indent=indent)


class TimeFormats(Base):
    """Time format descriptions for strftime conversion to datetime objects"""
    def __init__(self):
        self.std_time =    '%Y-%m-%d %H:%M:%S'
        self.std_time_ms = '%Y-%m-%d %H:%M:%S.%f'
        self.iso_time =    '%Y-%m-%dT%H:%M:%S.%f%z'
        self.file_time =   '%Y_%m_%d_%H_%M_%S_%f'


class TimePiece(Base):
    """Formatting methods for creating strftime compliant timestamps"""
    def __init__(self, time_format='std_time'):
        super().__init__()
        try:
            import pyb  # pyboard import
            rtc = pyb.RTC()
            self._struct_time = rtc.now
        except ImportError:
            try:
                import machine  # CircuitPython / Pycom import
                rtc = machine.RTC()
                self._struct_time = rtc.now
            except ImportError:
                try:
                    from datetime import datetime  # CPython 3.7

                    def _struct_time():
                        t = datetime.now()
                        return (t.year, t.month, t.day, t.hour,
                                t.minute, t.second, t.microsecond)

                    self._struct_time = _struct_time
                except ImportError:
                    raise

        #self.formats_available = TimeFormats()

        self.formats_available = {'std_time': '%Y-%m-%d %H:%M:%S',
                                  'std_time_ms': '%Y-%m-%d %H:%M:%S.%f',
                                  'iso_time': '%Y-%m-%dT%H:%M:%S.%f%z',
                                  'file_time': '%Y_%m_%d_%H_%M_%S_%f'}

        self.format = time_format        
        self.strfmtime = self.formats_available[time_format]

    def get_time(self):
        """Get the time in a specific format.  For creating a reproducible
        format citation based on the attributes of the TimeFormats class.

        Returns
        -------
        str, formatted current time based on input argument
        """
        _formats = {'std_time': self.std_time, 'std_time_ms': self.std_time_ms,
                    'iso_time': self.iso_time, 'file_time': self.file_time}
        _method = _formats[self.format]
        return _method()

    def std_time(self, str_format='{:02d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}'):
        """Get time in stardard format '%Y-%m-%d %H:%M:%S' and accurate
        to the second
        """
        t = self._struct_time()
        st = str_format
        return st.format(t[0], t[1], t[2], t[3], t[4], t[5])

    def file_time(self):
        """Get time in a format compatible with filenames,
        '%Y_%m_%d_%H_%M_%S_%f' and accurate to the second
        """
        str_format = '{:02d}_{:02d}_{:02d}_{:02d}_{:02d}_{:02d}'
        return self.std_time(str_format)

    def iso_time(self):
        """Get time in ISO 8601 format '%Y-%m-%dT%H:%M:%SZ' and
        accurate to the second.  Note: assumes system clock is UTC.
        """
        str_format = '{:02d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}Z'
        return self.std_time(str_format)

    def std_time_ms(self):
        """Get time in standard format '%Y-%m-%d %H:%M:%S.%f' and accurate
        to the microsecond
        """
        t = self._struct_time()
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


class DeviceData(Base):
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
        self.active = None
        self.error = None
        self.dtype = None
        self.calibration_date = None


class DeviceCalibration(Base):
    """Base class for device calibration"""
    def __init__(self):
        self.name = None
        self.description = None
        self.urls = None
        self.manufacturer = None
        self.version = None
        self.dtype = None
        self.date = None

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

