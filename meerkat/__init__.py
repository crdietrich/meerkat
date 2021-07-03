version = 0.5


import sys

if sys.platform == 'linux':
    import json
    import time

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
    import utime as time
    
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
    import utime as time
    
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
