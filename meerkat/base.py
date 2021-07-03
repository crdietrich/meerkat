"""Basic I2C device classes for Raspberry PI & MicroPython"""

import sys

if sys.platform == 'linux':
    import json

    from meerkat import i2c_pi
    I2C = i2c_pi.WrapI2C
    i2c_default_bus = 1

    from datetime import datetime  # Python 3.7

    def _struct_time():
        t = datetime.now()
        return (t.year, t.month, t.day, t.hour,
                t.minute, t.second, t.microsecond)

    def json_dumps(value):
        return json.dumps(value, default=lambda x: x.class_values())

elif sys.platform in ['FiPy']:
    import ujson as json

    from meerkat import i2c_pycom
    I2C = i2c_pycom.WrapI2C
    i2c_default_bus = 0

    import machine
    rtc = machine.RTC()
    _struct_time = rtc.now

    def json_dumps(value):
        return json.dumps(value)


elif sys.platform in ['pyboard', 'OpenMV3-M7']:
    import ujson as json

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

    def json_dumps(value):
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

    def to_json(self, indent=None):
        """Return all class objects from __dict__ except
        those prefixed with underscore ('_')
        See self.class_values method for implementation.

        Returns
        -------
        str, JSON formatted (attribute: value) pairs
        """
        return json_dumps(self.class_values())
