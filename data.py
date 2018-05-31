# -*- coding: utf-8 -*-
"""Meerkat data tools"""
__author__ = "Colin Dietrich"
__copyright__ = "2018"
__license__ = "MIT"

try:
    import ujson as json
except:
    import json


class Data(object):
    """Base class for data serialization"""
    def __init__(self, name):
        # data and file attributes
        self.name = name
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
        self.escape_char = '\\'
        self.null_sequence = 'NA'
        self.comment = '#'
        self.skip_lines = 0

        # data location
        self.data = []
        self.path = None

        # device metadata information
        self.device_metadata = None

        # data quality
        self.units = None
        self.dtypes = None
        self.accuracy = None
        self.precision = None

    def __repr__(self):
        return str(self.__dict__)

    def values(self):
        return self.__dict__

    def to_json(self, indent=None):
        return json.dumps(self,
                          default=lambda o: o.__dict__,
                          sort_keys=True,
                          indent=indent)

    def write(self, indent=None):
        """Write metadata to file path location self.path"""

        h = self.to_json(indent)
        with open(self.path, 'w') as f:
            f.write(h + self.line_terminator)
            for d in self.data:
                f.write(d + self.line_terminator)


class CSVResource(Data):
    """Specific attributes of comma delimited values (CSV) data formatting
    based on Frictionless Data CSV dialect
    """
    def __init__(self, name):
        super(CSVResource, self).__init__(name)

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

        self._file_init = False

    def create_metadata(self):
        """Generate JSON metadata and format it with 
        a leading shebang sequence, '#!'
        
        Returns
        -------
        str, metadata in JSON with '#!' at the beginning
        """
        return '#!' + self.to_json() + self.line_terminator

    def write_init(self, shebang=True, header=True):
        """Write metadata to a header row designated
        by a shebang '#!' as the first line of a file at location
        self.path, then a header line in self.header, then lines of data
        for each item in self.data"""

        with open(self.path, 'w') as f:
            if shebang == True:
                f.write(self.create_metadata())
            if header == True:
                h = ','.join(self.header)
                f.write(h + self.line_terminator)

    def write_append(self, data):
        """Append data to an existing file at location self.path"""

        with open(self.path, 'w') as f:
            for d in data:
                dc = ','.join([str(_x) for _x in d])
                f.write(dc + self.line_terminator)

    def _write(self, data, shebang=True, header=True):
        """Write data to file, write header if not yet done
        To be called by the child class method 'write'
        with a properly formed data list"""
        
        if not self._file_init:
            self.write_init(shebang=shebang, header=header)
        if self.data is not None:
            self.write_append(data)

    def _get(self, data):
        """Placeholder for child class method that will 
        return a list of data as it will be saved to disk.
        Requires correct formatting in the child class.

        Parameters
        ----------
        data : list, data that will be saved"""

        pass


class JSONResource(Data):
    def __init__(self, name):
        super(JSONResource, self).__init__(name)

        self.version = '0.1 Alpha'
        self.standard = 'RFC 8259'
        self.media_type = 'text/json'

    def write(self, indent=None):
        """Write metadata to file path location self.path"""

        with open(self.path, 'w') as f:
            f.write(self.to_json(indent))


class HTMLResource(Data):
    def __init__(self, name):
        super(HTMLResource, self).__init__(name)

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
                 "<body class='mono'>" + self.line_terminator,]
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

