"""ADS1x15 I2C ADC for Micropython/Meerkat
Author: Colin Dietrich 2016

TODO: set instance/chip attributes, regular polling method
"""

class BASE():
    def __init__(self):
        self.
        self.default_i2c_address = 0x48
        self.os_single = 0x8000
        self.mux_offset = 12

class REGISTER():
    def __init__(self):
        self.conversion     = 0x00
        self.config         = 0x01
        self.low_threshold  = 0x02
        self.high_threshold = 0x03
        
        
class GAIN():
    def __init__(self):
        self.x2_3   = 0x0000
        self.x1     = 0x0200
        self.x2     = 0x0400
        self.x4     = 0x0600
        self.x8     = 0x0800
        self.x16    = 0x0A00

class BASE():
    def __init__(self):
        self.
        
class GAIN():
    def __init__(self):
        self.

class GAIN():
    def __init__(self):
        self.
        
class GAIN():
    def __init__(self):
        self.