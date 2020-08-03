"""Basic I2C device classes for Raspberry PI & MicroPython"""

import sys

if sys.platform == "linux":
    import json
    import time
    import struct

    from meerkat import i2c_pi
    I2C = i2c_pi.WrapI2C

elif sys.platform in ["FiPy"]:
    import ujson as json
    import utime as time
    import ustruct as struct

    from meerkat import i2c_upython
    I2C = i2c_upython.WrapI2C

else:
    print("Error detecting system platform.")

'''
    
def bit_set_old(idx, value):
    """Set bit at index idx in value to 1

    Parameters
    ----------
    idx : int, bit index to set
        (binary notation: MSB left, LSB right - not Python indexing!)
    value : value to change bit
    """
    return value | (1 << idx)


def bit_clear_old(idx, value):
    """Set bit at index idx in value to 0

    Parameters
    ----------
    idx : int, bit index to set
        (binary notation: MSB left, LSB right - not Python indexing!)
    value : value to change bit
    """
    return value & ~(1 << idx)


def twos_comp_to_dec_old(value, bits):
    """Convert Two's Compliment format to decimal"""
    if (value & (1 << (bits - 1))) != 0:
        value = value - (1 << bits)
    return value
'''

class Base:
    """Common methods"""

    def __init__(self):
        self.name = None
        self.description = None
        self.urls = None
        self.manufacturer = None

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


class DeviceData(Base):
    """Base class for device driver metadata"""
    def __init__(self, device_name):

        self.name = device_name

        self.version_hw = None
        self.version_sw = None
        self.accuracy = None
        self.precision = None

        self.bus = None
        self.state = None  # TODO: clarify what these mean
        self.active = None
        self.error = None
        self.dtype = None


class DeviceCalibration(Base):
    """Base class for device calibration"""
    def __init__(self):

        self.version = None
        self.dtype = None
        self.date = None
