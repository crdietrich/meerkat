"""Base Meerkat classes"""

import ujson

class REG(object):
    """Basic mask for setting individual bits in a register"""
        
    def __init__(self, n):
        self.value = None
        self.bits = n
        self.mask = [2**n for n in range(0, self.bits)]
    
    def mask_true(self, n):
        """Set bit n in register r to True (1)
        Parameters
        ----------
        n : int, zero index of bit to set (right lsb to left msb)
        Returns
        -------
        True if successfully set
        """
        self.value = r | self.mask[n]
        return True
        
    def mask_false(self, r, n):
        """Set bit n in register r to False (0)
        Parameters
        ----------
        n : int, zero index of bit to set (right lsb to left msb)
        Returns
        -------
        True if successfully set
        """
        
        self.value = r ^ self.mask[n]
        return True


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