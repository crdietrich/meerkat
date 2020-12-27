"""Basic I2C device classes for Raspberry PI & MicroPython"""

import sys

if sys.platform == 'linux':
    import json
    import time
    import struct

    from meerkat import i2c_pi
    I2C = i2c_pi.WrapI2C
    i2c_default_bus = 1

    def json_dumps(value):
        return json.dumps(value, default=lambda x: x.class_values())

    from datetime import datetime  # Python 3.7

    def _struct_time():
        t = datetime.now()
        return (t.year, t.month, t.day, t.hour,
                t.minute, t.second, t.microsecond)

elif sys.platform in ['FiPy']:
    import ujson as json
    import utime as time
    import ustruct as struct

    from meerkat import i2c_upython
    I2C = i2c_upython.WrapI2C
    i2c_default_bus = 0

    def json_dumps(value):
        return json.dumps(value)

    import machine
    rtc = machine.RTC()
    _struct_time = rtc.now()

elif sys.platform in ['pyboard']:
    import ujson as json
    import utime as time
    import ustruct as struct

    from meerkat import i2c_pyboard
    I2C = i2c_pyboard.WrapI2C
    i2c_default_bus = 'X'

    def json_dumps(value):
        return json.dumps(value)

    import machine
    rtc = machine.RTC()

    def _struct_time():
        t = rtc.datetime()
        return t[0], t[1], t[2], t[4], t[5], t[6], t[7]

else:
    print("Error detecting system platform.")


class Base:
    """Common methods"""

    def __repr__(self):
        return str(self.class_values())

    def class_values(self):
        """Get all class attributes from __dict__ attribute
        except those prefixed with underscore ('_') or
        those that are None (to reduce metadata size)

        Returns
        -------
        dict, of (attribute: value) pairs
        """
        d = {}
        for k, v in self.__dict__.items():
            if v is None:
                continue
            if k[0] == '_':
                continue
            d[k] = v
        return d

    def to_json(self, indent=None):
        """Return all class objects from __dict__ except
        those prefixed with underscore ('_')
        See self.class_values method for implementation.

        Returns
        -------
        str, JSON formatted (attribute: value) pairs
        """
        return json_dumps(self.class_values())

class TimePiece(Base):
    """Formatting methods for creating strftime compliant timestamps"""
    def __init__(self, time_format='std_time', time_zone=None):
        super().__init__()

        self._import_error = []
        self._struct_time = _struct_time

        self.formats_available = {'std_time':    '%Y-%m-%d %H:%M:%S',
                                  'std_time_ms': '%Y-%m-%d %H:%M:%S.%f',
                                  'iso_time':    '%Y-%m-%dT%H:%M:%S.%f%z',
                                  'file_time':   '%Y_%m_%d_%H_%M_%S',
                                  'rtc_time':    '%Y-%m-%d %H:%M:%S',        # same as std_time
                                  'gps_time':    '%Y-%m-%dT%H:%M:%S.%f+%z',  # same as iso_time
                                  'gps_location': 'NMEA_RMC'  # recommended minimum specific GPS/transit data message
                                 }
        self._format   = None
        self.format    = time_format
        self.strfmtime = self.formats_available[time_format]

        # optional timezone
        self._tz = None
        self.tz  = time_zone

        # external hardware time source
        self.rtc = None
        self.gps = None

    @property
    def format(self):
        return self._format

    @format.setter
    def format(self, time_format):
        self._format = time_format
        self.strfmtime = self.formats_available[time_format]

    @property
    def tz(self):
        return self._tz

    @tz.setter
    def tz(self, time_zone):
        if time_zone is None:
            self._tz = ''
        else: self._tz = time_zone


    def get_time(self):
        """Get the time in a specific format.  For creating a reproducible
        format citation based on the attributes of the TimeFormats class.

        Returns
        -------
        str, formatted current time based on input argument
        """
        _formats = {'std_time': self.std_time, 'std_time_ms': self.std_time_ms,
                    'iso_time': self.iso_time, 'file_time':   self.file_time,
                    'rtc_time': self.rtc_time, 'gps_time':    self.gps_time,
                    'gps_location': self.gps_location}
        _method = _formats[self.format]
        return _method()

    def std_time(self, str_format='{:02d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}'):
        """Get time in stardard format '%Y-%m-%d %H:%M:%S' and accurate
        to the second
        """
        t = self._struct_time()
        return str_format.format(t[0], t[1], t[2], t[3], t[4], t[5])

    def std_time_ms(self, str_format='{:02d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}.{:06}'):
        """Get time in standard format '%Y-%m-%d %H:%M:%S.%f' and
        accurate to the microsecond
        """
        t = self._struct_time()
        return str_format.format(t[0], t[1], t[2], t[3], t[4], t[5], t[6])

    def iso_time(self):
        """Get time in ISO 8601 format '%Y-%m-%dT%H:%M:%SZ' and
        accurate to the second.  Note: assumes system clock is UTC.
        """
        str_format = '{:02d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}.{:06}' + self.tz
        return self.std_time_ms(str_format=str_format)

    def file_time(self):
        """Get time in a format compatible with filenames,
        '%Y_%m_%d_%H_%M_%S_%f' and accurate to the second
        """
        str_format = '{:02d}_{:02d}_{:02d}_{:02d}_{:02d}_{:02d}'
        return self.std_time(str_format)

    def rtc_time(self, bus_n=1, bus_addr=0x68):
        """Get time from the DS3221 RTC

        Parameters
        ----------
        bus_n : int, I2C bus number to access the RTC on
        bus_addr : int, I2C bus address the RTC is at on the bus

        Returns
        -------
        RTC time in std_time format
        """
        if self.rtc is None:
            from meerkat import ds3231
            self.rtc = ds3231.DS3231(bus_n=bus_n, bus_addr=bus_addr)

        t = self.rtc.get_time()
        if self.tz is not None:
            tz = self.tz

        str_format='{:02d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}'
        return str_format.format(t[0], t[1], t[2], t[3], t[4], t[5])

    def gps_location(self, bus_n=1, bus_addr=0x10):
        """Get NMEA RMC message from the PA1010D GPS

        Parameters
        ----------
        bus_n : int, I2C bus number to access the RTC on
        bus_addr : int, I2C bus address the RTC is at on the bus

        Returns
        -------
        GPS date, lat, lon and time in NMEA RMC format
        """
        if self.gps is None:
            from meerkat import pa1010d
            self.gps = pa1010d.PA1010D(bus_n=bus_n, bus_addr=bus_addr)

        nmea_sentence = self.gps.get(nmea_sentences=['RMC'])[0]
        return nmea_sentence

    def gps_time(self, bus_n=1, bus_addr=0x10):
        """Get time from the PA1010D GPS

        Parameters
        ----------
        bus_n : int, I2C bus number to access the RTC on
        bus_addr : int, I2C bus address the RTC is at on the bus

        Returns
        -------
        RTC time in iso_time format
        """
        nmea_sentence = self.gps_location(bus_n=bus_n, bus_addr=bus_addr)
        nmea_sentence = nmea_sentence.split(',')
        t = nmea_sentence[1].split('.')[0]
        t_ms = nmea_sentence[1].split('.')[1]
        t = [t[:2], t[2:4], t[4:]]
        d = nmea_sentence[9]
        d = ['20'+d[4:], d[2:4], d[:2]]
        str_format='{}-{}-{}T{}:{}:{}.{}+0:00'
        return str_format.format(d[0], d[1], d[2], t[0], t[1], t[2], t_ms)
