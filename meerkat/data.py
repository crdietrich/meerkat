# -*- coding: utf-8 -*-
"""Meerkat data tools"""
__author__ = "Colin Dietrich"
__copyright__ = "2018"
__license__ = "MIT"

import sys

if sys.platform == "linux":
    import json

elif sys.platform in ["FiPy"]:
    import ujson as json

else:
    print("Error detecting system platform.")

from meerkat.base import TimePiece


class Writer(object):
    """Base class for data serialization
    Note: Any attribute prefixed with '_' will not be saved to metadata"""
    def __init__(self, name, time_format='std_time'):
        # data and file attributes
        self.name = name
        # self.uuid = str(uuid.uuid1(node=None, clock_seq=int(datetime.now().timestamp()*1000000)))
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

        # timestamp formatter
        self.timepiece = TimePiece(time_format)
        self.time_format = self.timepiece.format
        self.strfmtime = self.timepiece.strfmtime

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

    def to_json(self):
        return json.dumps(self.values())

    def create_data(self, data, indent=None):
        """Placeholder method to keep classes consistent"""
        return data

    def write(self, data, indent=None):
        """Write JSON metadata and arbitrary data to a file"""

        if self.path is None:
            self.path = self.name + '_' + self.timepiece.file_time() + '.txt'
        h = self.to_json(indent).encode('string-escape')
        with open(self.path, 'w') as f:
            f.write(h + self.line_terminator)
            for d in data:
                f.write(d + self.line_terminator)


class CSVWriter(Writer):
    """Specific attributes of comma delimited values (CSV) data formatting
    based on Frictionless Data CSV dialect
    """
    def __init__(self, name, time_format='std_time'):
        super().__init__(name, time_format)

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
        self._stream_init = False

    def create_metadata(self):
        """Generate JSON metadata and format it with
        a leading shebang sequence, '#!'

        Returns
        -------
        str, metadata in JSON with '#!' at the beginning
        indent, None or int - passed to json.dump builtin
        """
        #return '#!' + self.to_json(indent=indent)
        return '#!' + self.to_json()

    def create_data(self, data, indent=None):
        return ','.join([str(d) for d in data])

    def get(self, data):
        """Passthrough for child class method that returns a list,
        included here to support JSON passthrough.

        Parameters
        ----------
        data : data to be return"""
        return data

    def _write_init(self):
        """Write metadata to a header row designated
        by a shebang '#!' as the first line of a file at location
        self.path, then a header line in self.header, then lines of data
        for each item in self.data
        """
        if self.path is None:
            self.path = self.timepiece.file_time() + '_data.csv'
        with open(self.path, 'w') as f:
            if self.shebang:
                f.write(self.create_metadata() + self.line_terminator)
            if self.header is not None:
                h = ','.join([self.time_format] + self.header)
                f.write(h + self.line_terminator)

    def _write_append(self, data):
        """Append data to an existing file at location self.path"""

        with open(self.path, 'a') as f:
            dc = ','.join([self.timepiece.get_time()]+[str(_x) for _x in data])
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


class JSONWriter(Writer):
    def __init__(self, name, time_format='std_time'):
        super().__init__(name, time_format)

        self.version = '0.1 Alpha'
        self.standard = 'RFC 8259'
        self.media_type = 'text/json'

        # how often to write a metadata JSON packet
        self.metadata_interval = 10
        self.metadata_file_i = 1
        self.metadata_stream_i = 1

        # header is the JSON key values for the JSON value data
        self.header = None
        self._file_init = False

    def create_metadata(self, data_out):
        """Generate dict metadata

        Returns
        -------
        dict : public attributes from self.values method
        """
        md = self.values()
        for k,v in md.items():
            data_out[k] = v
        return data_out

    def get(self, data):
        """Return JSON data and metadata at intervals set by self.metadata_interval

        Parameters
        ----------
        data : list, data to be zipped with header descriptions

        Returns
        -------
        data_out : str, JSON formatted data and metadata
        """
        data_out = {k:v for k,v in zip(self.header, data)}
        data_out[self.time_format] = self.timepiece.get_time()

        if self.metadata_stream_i == self.metadata_interval:
            self.metadata_stream_i = 0
            data_out = self.create_metadata(data_out)

        self.metadata_stream_i += 1
        return json.dumps(data_out)

    def write(self, data):
        """Write JSON data and metadata at intervals set by self.metadata_interval
        to file location self.path

        Parameters
        ----------
        data : list, data to be zipped with header descriptions
        """
        if self.path is None:
            self.path = self.timepiece.file_time() + '.jsontxt'

        data_out = {k:v for k,v in zip(self.header, data)}
        data_out[self.time_format] = self.timepiece.get_time()

        if self.metadata_file_i == self.metadata_interval:
            self.metadata_file_i = 0
            data_out = self.create_metadata(data_out)

        with open(self.path, 'a') as f:
            f.write(json.dumps(data_out) + self.line_terminator)
        self.metadata_file_i += 1
