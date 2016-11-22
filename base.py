"""Base Meerkat classes"""

import ujson

class REG(object):
    """Basic mask for setting individual bits in a register"""
        
    def __init__(self, n):
        self.value = None
        self.bits = n
        self.mask = [2**n for n in range(0, self.bits)]
    
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
        
        bits = self.config.reverse(bits)
        for n in range(base, base + len(bits)):
            self.config.apply(n, bits[n])
        
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
        self.payload = None

    def dumps(self):
        if self.payload is not None:
            return ujson.dumps(self.payload)

    def loads(self):
        print(ujson.loads(self.payload))