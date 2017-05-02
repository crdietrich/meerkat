"""Base Meerkat classes"""

import ujson

def scan_I2C(i2c_bus):
    found_address = i2c_bus.scan()
    print('Found I2C devices at:', found_address)
    
class I2C(object):
    """Generic I2C Bus"""
    
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


def bit_set(value, bit):
    """Set bit in value to 1

    Parameters
    ----------
    value : 16 bit int, value to change bit
    bit : int, bit index to set
        (binary notation: MSB left, LSB right - not Python indexing!)
    """
    return value | (1 << bit)


def bit_clear(value, bit):
    """Set (clear) bit in value to 0

    Parameters
    ----------
    value : 16 bit int, value to change bit
    bit : int, bit index to set
        (binary notation: MSB left, LSB right - not Python indexing!)
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

def twos_complement(input_value, num_bits):
    """Calculates a two's complement integer from the given input value's bits"""
    mask = 2 ** (num_bits - 1)
    return -(input_value & mask) + (input_value & ~mask)


class REG(object):
    """Basic mask for setting individual bits in a register"""
        
    def __init__(self, n):
        self.value = None
        self.bits = n
        self.mask = [2**n for n in range(0, self.bits)]
    
    def combine(self, msb, lsb):
        """Combine most significant bit and least significant bit
        to a 16 bit number
        """
        return (msb << 8) | (lsb >> 8)
    
    def reverse_generator(self, x):
        """Reverse itteration, directly copied from PEP 322
        
        Parameters
        ----------
        x : itterator which does not support keys
        """
        
        if hasattr(x, 'keys'):
            raise ValueError("mappings do not support reverse iteration")
        i = len(x)
        while i > 0:
            i -= 1
            yield x[i]
    
    def reverse(self, string):
        """Reverse a string since str.reverse not implemented.
        Useful for str repr of bits to byte order repr.
        Definely other ways of doing this.
        
        Parameters
        ----------
        string : str, string to reverse
        """
        
        return ''.join([n for n in self.reverse_generator(string)])
    
    def mask_true(self, n):
        """Set bit n in register r to True (1)
        Parameters
        ----------
        n : int, zero index of bit to set (right lsb to left msb)
        Returns
        -------
        True if successfully set
        """
        
        self.value = self.value | self.mask[n]
        return True
        
    def mask_false(self, n):
        """Set bit n in register r to False (0)
        Parameters
        ----------
        n : int, zero index of bit to set (right lsb to left msb)
        Returns
        -------
        True if successfully set
        """
        
        self.value = self.value ^ self.mask[n]
        return True
        
    def apply(self, n, x):
        """Set bit n to state x
        
        Parameters
        ----------
        n : int, zero index of bit to set (right lsb to left msb)
        x : str/int/bool, value to set bit based on:
            1, '1', True = set bit to True/0b1
            0, '0', False = set bit to False/0b0
        """
        
        _conv = {1: True, '1': True, 0: False}
        
        if x == '0':
            x = 0
        elif x == '1':
            x = 1
        
        if x:
            self.mask_true(n)
        else:
            self.mask_false(n)

    def apply_bits(self, base, bits):
        """Set specific bits in a register starting at base address.
        
        Note: assumes python 0 index L --> R and MSB --> LSB 
        and binary 0 indexing L <-- R
        Probably needs more abstraction as not all chips are MSB LSB
        -CRD
        
        Parameters
        ----------
        base : int, base address to write bits
        bits : str, bits to apply in '1' and '0' format
        """
        
        bits = self.reverse(bits)
        print("len(bits)>> ", len(bits))
        print("base>> ", base)
        for n in range(0, len(bits)):
            print(base, n, bits[n])
            self.apply(base + n, bits[n])
        
    def get_bits(self, base, number):
        """Return a portion of a register in string binary format
        
        Parameters
        ----------
        base : int, base bin (R --> L) address to read bits
        number : int, number or bits to read
        """
        _reg = bin(self.value)[2:]
        _reg = self.reverse(_reg)
        sub_bits = _reg[base:base+number]
        sub_bits = self.reverse(sub_bits)
        return sub_bits
        
    def clean(self, x):
        """Convert a string representation hex to """
        x = x.decode('utf-8')
        y = [ord(n) for n in x]
        return y
        
        
class Device(object):

    def __init__(self, name):

        # required
        self.data = Data(name)

        # optional
        self.description = None
        self.urls = None

        self.state = None
        self.active = None
        self.error = None
        self.name = None
        self.description = None
        self.bus = None
        self.manufacturer = None
        self.version_hw = None
        self.version_sw = None
        self.accuracy = None
        self.precision = None
        self.calibration_date = None

        
    

class Data(object):

    def __init__(self, name):
        # required
        self.name = name
        self.datetime = None
        self.lat = None
        self.lon = None
        self.value = None

    def payload(self):
        return {'name': self.name,
                'datetime': self.datetime,
                'lat': self.lat,
                'lon': self.lon,
                'value': self.value}

    def dumps(self):
        if self.payload is not None:
            return ujson.dumps(self.payload())

    def loads(self, data):
        print(ujson.loads(data))
