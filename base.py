"""Base Meerkat classes"""
try:
    import ujson as json
except:
    import json

try:
    import ustruct as struct
except:
    import struct


def scan_I2C(i2c_bus):
    found_address = i2c_bus.scan()
    print('Found I2C devices at:', found_address)
    
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


def bit_set(bit, value):
    """Set bit in value to 1

    Parameters
    ----------
    bit : int, bit index to set
        (binary notation: MSB left, LSB right - not Python indexing!)
    value : 16 bit int, value to change bit
    """
    return value | (1 << bit)


def bit_clear(bit, value):
    """Set (clear) bit in value to 0

    Parameters
    ----------
    bit : int, bit index to set
        (binary notation: MSB left, LSB right - not Python indexing!)
    value : 16 bit int, value to change bit
    """
    return value & ~(1 << bit)

    
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


class Data(dict):

    def __init__(self, name):
        """This whole thing needs to be converted to DataPackage format"""

        self['name'] = name
        self['sample_name'] = None
        self['sample_id'] = None
        self['datetime'] = None
        self['lat'] = None
        self['lon'] = None

        self['names'] = None
        self['values'] = None


    def payload(self):
        return self

    def dumps(self):
        return json.dumps(self.payload())

    def loads(self, data):
        print(json.loads(data))

        
class Device(Data):

    def __init__(self, name):
        super().__init__(name)

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
        self.calibration_date = None

