# -*- coding: utf-8 -*-
"""Meerkat data tools"""
__author__ = "Colin Dietrich"
__copyright__ = "2018"
__license__ = "MIT"

try:
    import ujson as json
except ImportError:
    import json

import uuid
from datetime import datetime

from meerkat.base import file_time_fmt, get_ftime, TimePiece


class Writer(object):
    """Base class for data serialization
    Note: Any attribute prefixed with '_' will not be saved to metadata"""
    def __init__(self, name):
        # data and file attributes
        self.name = name
        self.uuid = str(uuid.uuid1(node=None, clock_seq=int(datetime.now().timestamp()*1000000)))
        self.title = None
        self.description = None
        self.format = None
        self.encoding = 'utf-8'
        self.bytes = None
        self.hash = None
        self.schema = None
        self.sources = None
        self.licenses = None

        # dialect attributes
        self.line_terminator = '\n'
        self.quote_char = '"'
        self.double_quote = True
        self.escape_char = '\\'  # note: \\ to escape \ in JSON... meta.
        self.null_sequence = 'NA'
        self.comment = '#'
        self.skip_lines = 0

        # data location
        self.path = None

        # device metadata information
        self.device = None

        # data quality - move to base.DeviceData?
        self.units = None
        self.dtypes = None
        self.accuracy = None
        self.precision = None

        self.timepiece = TimePiece()

    def __repr__(self):
        return str(self.__dict__)

    def values(self):
        """Get all class attributes from __dict__ attribute
        except those prefixed with underscore ('_')

        Returns
        -------
        dict, of (attribute: value) pairs
        """
        d = {}
        for k, v in self.__dict__.items():
            if k[0] != '_':
                d[k] = v
        return d

    def to_json(self, indent=None):
        """Return all class objects from __dict__ except
        those prefixed with underscore ('_')

        Returns
        -------
        str, JSON formatted (attribute: value) pairs
        """
        return json.dumps(self,
                          default=lambda o: o.values(),
                          sort_keys=True,
                          indent=indent)

    def create_data(self, data, indent=None):
        """Placeholder method to keep classes consistent"""
        return data

    def write(self, data, indent=None, name=''):
        """Write metadata to file path location self.path"""

        if self.path is None:
            self.path = name + get_ftime() + '.txt'
        h = self.to_json(indent).encode('string-escape')
        with open(self.path, 'w') as f:
            f.write(h + self.line_terminator)
            for d in data:
                f.write(d + self.line_terminator)


class CSVWriter(Writer):
    """Specific attributes of comma delimited values (CSV) data formatting
    based on Frictionless Data CSV dialect
    """
    def __init__(self, name):
        super(CSVWriter, self).__init__(name)

        self.version = '0.1 Alpha'
        self.standard = 'Follow RFC 4180'
        self.media_type = 'text/csv'

        # csv specific attributes
        self.header = None
        self.delimiter = ','
        self.skip_initial_space = True
        self.header = True
        self.case_sensitive_header = False
        self.skip_lines = 1

        # attributes
        self.shebang = True
        self.header = None
        self._file_init = False

    def create_metadata(self):
        """Generate JSON metadata and format it with 
        a leading shebang sequence, '#!'
        
        Returns
        -------
        str, metadata in JSON with '#!' at the beginning
        """
        return '#!' + self.to_json()

    def create_data(self, data, indent=None):
        return ','.join([str(d) for d in data])

    def _write_init(self):
        """Write metadata to a header row designated
        by a shebang '#!' as the first line of a file at location
        self.path, then a header line in self.header, then lines of data
        for each item in self.data"""

        if self.path is None:
            str_time = datetime.now().strftime(file_time_fmt)
            self.path = str_time + '_data.csv'
        
        with open(self.path, 'w') as f:
            if self.shebang:
                f.write(self.create_metadata() + self.line_terminator)
            if self.header is not None:
                h = ','.join(self.header)
                f.write(h + self.line_terminator)

    def _write_append(self, data):
        """Append data to an existing file at location self.path"""

        with open(self.path, 'a') as f:
            dc = ','.join([str(_x) for _x in data])
            f.write(dc + self.line_terminator)

    def write(self, data, indent=None):
        """Write data to file, write header if not yet done
        To be called by the child class method 'write'
        with a properly formed data list

        To just initialize metadata and header, pass
        data = None"""
        
        if not self._file_init:
            self._write_init()
            self._file_init = True
        if data is not None:
            self._write_append(data)

    def get(self, data):
        """Placeholder for child class method that will 
        return a list of data as it will be saved to disk.
        Requires correct formatting in the child class.

        Parameters
        ----------
        data : list, data that will be saved"""

        pass


class JSONWriter(Writer):
    def __init__(self, name):
        super(JSONWriter, self).__init__(name)

        self.version = '0.1 Alpha'
        self.standard = 'RFC 8259'
        self.media_type = 'text/json'

        # how often to write a metadata JSON packet
        self.metadata_interval = 100
        self.metadata_file_i = 0
        self.metadata_stream_i = 0

        # header is the JSON key values for the JSON value data
        self.header = None
        self._file_init = False

    def create_metadata(self):
        """Generate JSON metadata and format it with
        a leading shebang sequence, '#!'

        Returns
        -------
        str, JSON formatted metadata describing JSON data format
        """
        return json.dumps({'metadata': self.values, 'uuid': self.uuid})

    def create_data(self, data, indent=None):
        data_out = {}
        if self.metadata_file_i == self.metadata_interval:
            self.metadata_file_i = 0
        if self.metadata_stream_i == self.metadata_interval:
            self.metadata_stream_i = 0
        if (self.metadata_file_i == 0) or (self.metadata_stream_i == 0):
            data_out['metadata'] = self.values()
        data_out['data'] = data
        data_out['uuid'] = self.uuid
        return json.dumps(data_out, indent=indent)

    def write(self, data, indent=None):
        """Write metadata to file path location self.path"""

        if self.path is None:
            str_time = datetime.now().strftime(file_time_fmt)
            self.path = str_time + '_JSON_data.txt'

        with open(self.path, 'a') as f:
            f.write(self.create_data(data, indent=indent) + self.line_terminator)
        self.metadata_file_i += 1

    def stream(self, data, indent=None):
        self.metadata_stream_i += 1
        return self.create_data(data, indent=indent)


class SerialStreamer(JSONWriter):
    def __init__(self, name):
        super(SerialStreamer, self).__init__(name)

        self.name = name
        self.serial = None

    def writer(self, data, indent=None):
        with self.serial.open() as serial:
            if self.metadata_i == 0:
                serial.write(self.to_json(indent))
                self.metadata_i += 1
            elif self.metadata_i == self.metadata_interval:
                self.metadata_i = 0
                serial.write(json.dumps(data, indent=indent))
            self.metadata_i += 1


class HTMLWriter(Writer):
    def __init__(self, name):
        super(HTMLWriter, self).__init__(name)

        self.version = '0.1 Alpha'
        self.standard = 'HTML5 & TBD'
        self.media_type = 'text/html'

    def header(self):
        """Create HTML header"""
        a = ""
        _values = self.values()
        for k, v in _values.items():
            a = a + "<meta " + str(k) + "='" + str(v) + " >" + self.line_terminator

        h_all = ["<!doctype html>" + self.line_terminator,
                 "<head>" + self.line_terminator,
                 "<title>Test of HTML data storage</title>" + self.line_terminator,
                 "<meta name='description' content='Test of HTML data page'>" + self.line_terminator,
                 "<meta name='author' content='Colin Dietrich'>" + self.line_terminator,
                 "<meta charset='utf-8'>" + self.line_terminator,
                 a + self.line_terminator,
                 "<style>.mono {{font-family: 'Courier New', Courier, monospace;}}</style>" + self.line_terminator,
                 "</head>" + self.line_terminator,
                 "<body class='mono'>" + self.line_terminator]
        h_all = "".join(h_all)
        h_all = h_all.encode('ascii', 'xmlcharrefreplace')
        print(h_all)

    def write_header(self):
        with open(self.path, 'w') as f:
            f.write(self.header + self.line_terminator)

    def append(self, data):
        with open(self.path, 'w') as f:
            dc = ','.join([str(_x) for _x in data])
            f.write('<div>' + dc + self.line_terminator)
