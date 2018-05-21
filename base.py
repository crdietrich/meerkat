# -*- coding: utf-8 -*-
"""Meerkat device tools"""
__author__ = "Colin Dietrich"
__copyright__ = "2018"
__license__ = "MIT"


try:
    import ujson as json
except:
    import json

try:
    import ustruct as struct
except:
    import struct


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


'''
class Resource(object):
    """Base metadata for a data resource using the
    Frictionless Data Specification
    frictionlessdata.io
    """

    def __init__(self, name):
        self.name = name
        self.profile = None  # TBD?
        self.title = None
        self.description = None
        self.format = None
        self.mediatype = 'text/csv'
        self.encoding = 'utf-8'
        self.bytes = None
        self.hash = None
        self.schema = None
        self.sources = None
        self.licenses = None

    def dumps(self):
        return json.dumps(vars(self))
'''
'''
class ResourcePath(Resource):
    """Tabular data resource referenced in JSON metadata,
    using the Frictionless Data Specification
    frictionlessdata.io
    """

    def __init__(self, name, path):
        super(ResourcePath, self).__init__(name)
        self.path = path
'''
'''
class ResourceData(Resource):
    """Tabular data inline with JSON data resource,
    using the Frictionless Data Specification
    frictionlessdata.io
    """

    def __init__(self, name):
        super(ResourceData, self).__init__(name)
        self.data = None
'''
'''
class DataDialect(object):
    def __init__(self):

        # attributes based on Frictionless Data CSV dialect
        self.delimiter = ','
        self.line_terminator = '\n'
        self.quote_char = '"'
        self.double_quote = True
        self.escape_char = '\\'
        self.null_sequence = 'NA'

    def __repr__(self):
        return json.dumps(vars(self))

        #return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True)
'''
'''
class CSVDialect(DataDialect):
    def __init__(self):
        #super(DataDialect, self).__init__()
        
        # attributes based on Frictionless Data CSV dialect
        self.delimiter = ','
        self.line_terminator = '\n'
        self.quote_char = '"'
        self.double_quote = True
        self.escape_char = '\\'
        self.null_sequence = 'NA'

        self.skip_initial_space = True
        self.header = True
        self.case_sensitive_header = False
        self.csvddf_version = 'meerkat_0.1 based on frictionless.io v1.2'

        # additional attributes
        self.comment_char = '#'

    def __repr__(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True)
'''

'''
class JSONDialect(DataDialect):
    def __init__(self):
        super(DataDialect, self).__init__()

    def __repr__(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True)
'''

class DataFormat(object):

    def __init__(self, format=None):
        """This whole thing needs to be converted to DataPackage format"""
        
        self.format = format.lower()

        # set dialect based on format
        if self.format == 'csv':
            self.dialect = CSVDialect()
        elif self.format == 'json':
            self.dialect = JSONDialect()
        else:
            self.dialect = CSVDialect()

        # data collection attributes
        self.sample_name = None
        self.sample_id = None
        self.datetime = None
        self.lat = None
        self.lon = None

        self.names = None
        self.values = None

    def __repr__(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True)


class CSVRecorder(object):
    def __init__(self, device, description, header, folder):
        self.device = device        
        self.data_format = DataFormat('csv')
        self.data_format.device = str(self.device)
        
        self.description = description
        self.header = header
        self.folder = folder  # local location to save .csv

    #def __enter__(self):
        
        self.resource = ResourcePath(name=self.description,
                                     path=self.description+'.csv')

        self.f = open(folder+self.description+'.csv', 'w')
        self.f.write(self.data_format.dialect.comment_char +
                     str(self.data_format))
        self.f.write(self.data_format.dialect.line_terminator)
        self.f.write(self.header)
        self.f.write(self.data_format.dialect.line_terminator)

    def __exit__(self):
        self.f.close()


    def write(self, sample_data):
        """
        sample_data : one line of data collected in a multi sample sweep/session
        """

        self.f.write(sample_data)
        self.f.write(self.data_format.dialect.line_terminator)
        

class Device(object):

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
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True)

    def dumps(self):
        return json.dumps(vars(self))

