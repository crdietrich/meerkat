# -*- coding: utf-8 -*-
"""Meerkat data tools"""
__author__ = "Colin Dietrich"
__copyright__ = "2018"
__license__ = "MIT"


class Writer(object):
    def __init__(self):
        pass


class Meta(object):
    """Metadata for a data resource using the
    based the Frictionless Data Specification
    """

    def __init__(self, name):
        self.version = '0.1 Alpha'

    	# data and file attributes
        self.name = name
        self.path = None
        #self.profile = None  # usefulness TBD?
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

    def __repr__(self):
        return vars(self)

    def json_dumps(self):
        return json.dumps(vars(self))


class Data(object):
    def __init__(self, name):
        self.meta = Meta(name)
        self.data = []
        self.path = None

        self.units = None
        self.dtypes = None
        self.accuracy = None
        self.precision = None

    def __repr__(self):
        return vars(self)

    def json_dumps(self):
        return json.dumps(vars(self))

    def write(self):
        """Write metadata as stored in self.meta and all data stored in
        self.data to file path location self.path"""

        h = self.meta.repr_json()
        with open(self.path, 'w') as f:
            f.write(h + self.line_terminator)
            for d in self.data:
                f.write(d + self.line_terminator)


class CSVResource(Data):
    """Specific attributes of comma delimited values (CSV) data formatting
    based on Frictionless Data CSV dialect
    """
    self __init__(self, name):
    	super(Data, self).__init__(name)

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

    def write(self, shebang=True, header=True):
        """Write metadata as stored in self.meta to a header row designated
        by a shebang '#!' as the first line of a file at location
        self.path, then a header line in self.header, then lines of data
        for each item in self.data"""

        m = self.meta.repr_json()
        with open(self.path, 'w') as f:
            if meta == True:
                f.write('#!' + m + self.line_terminator)
            if header == True:
                f.write(self.header + self.line_terminator)
            if self.data is not None:
                for d in self.data:
                    dc = ','.join([str(_x) for _x in d]
                    f.write(dc + self.line_terminator)

    def write_append(self, data):
        """Append data to an existing file at location self.path"""

        with open(self.path, 'w') as f:
            for d in data:
                dc = ','.join([str(_x) for _x in d]
                f.write(dc + self.line_terminator)


class JSONResource(Data):
    def __init__(self):
        super(Data, self).__init__()

        self.version = '0.1 Alpha'
        self.standard = 'RFC 8259'
        self.media_type = 'text/json'

    def write(self):
        """Write metadata as stored in self.meta and all data stored in
        self.data to file path location self.path"""

        with open(self.path, 'w') as f:
            d = json.dumps(vars(self))
            f.write(d + self.line_terminator)


class HTMLResource(Data):
    def __init__(self):
        super(Data, self).__init__

        self.version = '0.1 Alpha'
        self.standard = 'HTML5 & TBD'
        self.media_type = 'text/html'

    def header(self):
        """Create HTML header"""
        a = "<meta "
        for k, v in self.meta:
            a.append(str(k) + "='" + str(v) + "'" + self.line_terminator
        a.append(">")

        h_all = ("<!doctype html>"
                 "<head>"
                 "<title>Test of HTML data storage</title>"
                 "<meta name='description' content='Test of HTML data page'>"
                 "<meta name='author' content='Colin Dietrich'>"
                 "<meta charset='utf-8'>"
                 "<meta a='this' b='that'>"
                 "<style>.mono {font-family: 'Courier New', Courier, monospace;}</style>"
                 "</head>"
                 "<body class='mono'>").format()

        h = h_all(a)
        print(h)

    def write_header(self):
        with open(self.path, 'w') as f:
            f.write(self.header + self.line_terminator)

    def append(self, data):
        with open(self.path, 'w') as f:
            dc = ','.join([str(_x) for _x in data]
            f.write('<div>' + dc + self.line_terminator)
