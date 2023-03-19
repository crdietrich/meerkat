"""Basic I2C device classes for Raspberry PI & MicroPython

Board Support Lists that sys.platform matches:
https://docs.circuitpython.org/en/latest/README.html#ports

Default bus is first hardware I2C bus number. Can be overridden
in driver class attributes.
"""

import sys


if sys.platform == 'linux':
    import json
    import time
    import struct

    from meerkat import i2c_pi

    I2C = i2c_pi.WrapI2C
    i2c_default_bus = 1

    from datetime import datetime  # Python 3.7

    def _struct_time():
        t = datetime.now()
        return (t.year, t.month, t.day, t.hour,
                t.minute, t.second, t.microsecond)

    def _json_dumps(value):
        return json.dumps(value, default=lambda x: x.class_values())

elif sys.platform in ['FiPy']:
    import ujson as json
    import utime as time
    import ustruct as struct

    from meerkat import i2c_pycom

    I2C = i2c_pycom.WrapI2C
    i2c_default_bus = 0

    import machine

    rtc = machine.RTC()
    _struct_time = rtc.now

    def _json_dumps(value):
        return json.dumps(value)

elif sys.platform in ['Espressif', 'RP2040']:
    import json
    import time
    import struct

    from meerkat.base import i2c_circuitpython

    I2C = i2c_circuitpython.WrapI2C
    STEMMA_I2C = i2c_circuitpython.WrapSTEMMA_I2C

    def _struct_time():
        # Espressif does not support milliseconds
        t = time.struct_time(time.localtime())
        return(t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour,
               t.tm_min, t.tm_sec, 0)

    def _json_dumps(value):
        return json.dumps(value)

elif sys.platform in ['pyboard', 'OpenMV3-M7']:
    import ujson as json
    import utime as time
    import ustruct as struct

    from meerkat import i2c_pyboard

    I2C = i2c_pyboard.WrapI2C

    if sys.platform in ['pyboard']:
        i2c_default_bus = 'X'

    if sys.platform in ['OpenMV3-M7']:
        i2c_default_bus = 4

    import machine

    rtc = machine.RTC()

    def _struct_time():
        t = rtc.datetime()
        return t[0], t[1], t[2], t[4], t[5], t[6], t[7]

    def _json_dumps(value):
        return json.dumps(value)
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

    def json_dumps(self, value):
        return _json_dumps(value)

    def to_json(self, indent=None):
        """Return all class objects from __dict__ except
        those prefixed with underscore ('_')
        See self.class_values method for implementation.

        Returns
        -------
        str, JSON formatted (attribute: value) pairs
        """
        return _json_dumps(self.class_values())
