# -*- coding: utf-8 -*-
"""Meerkat device methods"""
__author__ = "Colin Dietrich"
__copyright__ = "2018"
__license__ = "MIT"

try:
    import ujson as json
except:
    import json


iso_time_fmt = '%Y-%m-%dT%H:%M:%S%z'

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
    return (value & (1 << idx) != 0)


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


def bit_toggle(value, bit, bool):
    """Toggle bit in value to boolean
    
    Parameters
    ----------
    value : 16 bit int, value to change bit
    bit : int, bit index to set
        (binary notation: MSB left, LSB right - not Python indexing!)
    bool : boolean, direction to toggle bit
    
    Returns
    -------
    value with toggled bit
    """
    
    if bool is True:
        return bit_set(value, bit)
    elif bool is False:
        return bit_clear(value, bit)


def twos_comp_to_dec(value, bits):
    """Convert Two's Compliment format to decimal"""
    if (value & (1 << (bits - 1))) != 0:
        value = value - (1 << bits)
    return value


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
        
        self.device_name = device_name
        self.description = None
        self.urls = None

        self.state = None
        self.active = None
        self.error = None
        self.bus = None
        self.manufacturer = None
        self.version_hw = None
        self.version_sw = None
        self.accuracy = None
        self.precision = None
        self.dtype = None
        self.calibration_date = None

    def __repr__(self):
        return str(self.__dict__)

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True)

class DeviceCalibration(object):
    """Base class for device calibration"""

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
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True)

    def from_json(self, json_str):
        self.__dict__ = json.loads(json_str)

    def from_file(self, filepath):
        with open(filepath) as f:
            self.from_json(f)
