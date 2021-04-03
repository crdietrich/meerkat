"""CSV and JSON writing and publishing methods"""


from meerkat.base import Base, TimePiece, json


class Meta(Base):
    """Metadata for data source"""
    def __init__(self, name):

        # device/source specific descriptions
        self.name         = name  # name of data source being recorded
        self.source_desc  = None  # description of the data source being recorded
        self.urls         = None  # URL(s) for data source reference
        self.manufacturer = None  # manufacturer of device/source of data
        self.state        = None  # general status of driver

        # data output descriptions
        self.header       = None  # names of each kind of data value being recorded
        self.dtype        = None  # data types (int, float, etc) for each data value
        self.units        = None  # measured units of data values
        self.accuracy     = None  # accuracy in units of data values
        self.precision    = None  # precision in units of data values

        # I2C bus descriptions
        self.bus_n        = None  # I2C bus the device is on
        self.bus_addr     = None  # I2C bus address the device is on


class Calibration(Base):
    """Device calibration"""
    def __init__(self):

        self.version    = None
        self.dtype      = None
        self.date       = None


class WriterBase(Base):
    """Base class for data serialization
    Note 1: Any attribute prefixed with '_' or with value None will not be written
    Note 2: Output file name will be:
        TimePiece.file_time() + '_' + self._metadata['name'] + self._metadata['description'] + (file extension)
        where (file extension) is either '.csv' or '.jsontxt'
        if self._metadata['description'] is None, it is omitted from the file name
    """
    def __init__(self, metadata, time_format):

        # file information
        self.encoding        = 'utf-8'  # encoding of output. Should stay 'utf-8'!
        self.format          = None     # format of data being written, CSV, JSON, etc
        self.standard        = None     # standard for format
        self.licenses        = None     # if there's licensing restrictions

        # file formatting conventions
        self.line_terminator = '\n'     #
        self.quote_char      = '"'      # note: in JSON, a quote will be "\""
        self.double_quote    = True     #
        self.escape_char     = '\\'     # note: \\ to escape \ in JSON... meta.
        self.null_sequence   = 'NA'     #
        self.comment         = '#'      #

        # device metadata
        self._metadata = metadata

        # filepath information
        self.path = None

        # timestamp formatter
        self._timepiece  = TimePiece(time_format)
        self.time_format = self._timepiece.format
        self.strfmtime   = self._timepiece.strfmtime


class CSVWriter(WriterBase):
    """Specific attributes of comma delimited values (CSV) data formatting
    based on Frictionless Data CSV dialect
    """
    def __init__(self, metadata, time_format='std_time'):
        super().__init__(metadata, time_format)

        self._file_init            = False              # file initialization flag

        # csv specific formatting
        self.format                = 'text/csv'         # file format
        self.standard              = 'Follow RFC 4180'  # formatting standard
        self.delimiter             = ','                # delimiter character
        self.skip_initial_space    = True               #
        self.case_sensitive_header = False              # header names are case sensitive
        self.comment               = '#'                # comment character
        self.skip_lines            = 1                  # how many lines to skip in CSV parsing

    def create_metadata(self):
        """Generate JSON metadata and format it with
        a leading shebang sequence, '#!'

        Returns
        -------
        str, metadata in JSON with '#!' at the beginning
        indent, None or int - passed to json.dump builtin
        """
        return '#!' + self.to_json()

    def _write_init(self):
        """Write metadata to a header row designated
        by a shebang '#!' as the first line of a file at location
        self.path, then a header line in self._header, then lines of data
        for each item in self.data
        """
        if self.path is None:
            self.path = (self._timepiece.file_time() + '_' +
                         self._metadata.name.lower().replace(' ', '_') +
                         '.csv')
        with open(self.path, 'w') as f:
            f.write(self.create_metadata() + self.line_terminator)
            if self._metadata.header is not None:
                h = ','.join([self.time_format] + self._metadata.header)
                f.write(h + self.line_terminator)

    def _write_append(self, data):
        """Append data to an existing file at location self.path"""
        with open(self.path, 'a') as f:
            dc = ','.join([self._timepiece.get_time()]+[str(_x) for _x in data])
            f.write(dc + self.line_terminator)

    def write(self, data):
        """Write data to file, write header if not yet done
        To be called by the child class method 'write'
        with a properly formed data list
        """
        if not self._file_init:
            self._write_init()
            self._file_init = True
        if data is not None:
            self._write_append(data)


class JSONWriter(WriterBase):
    def __init__(self, metadata, time_format='std_time'):
        super().__init__(metadata, time_format)

        self._file_init = False  # file initialization flag

        # json specific formatting
        self.format             = 'text/json'
        self.standard           = 'RFC 8259'

        # metadata insertion interval
        self.metadata_interval  = 10     # how often to write a metadata JSON packet
        self._metadata_file_i   = 1      # data packets since last metadata
        self._metadata_stream_i = 1      # data packets since last metadata

        self._file_init         = False  # file initialization check

    def add_metadata(self, data_out):
        """Generate writer metadata and append to data_out dictionary

        Returns
        -------
        dict : public attributes from self.values method
        """
        writer_metadata = self.class_values()
        device_metadata = self._metadata.class_values()
        data_out['writer'] = writer_metadata
        data_out['metadata'] = device_metadata
        return data_out

    def publish(self, data):
        """Return JSON data and metadata at intervals set by self.metadata_interval

        Parameters
        ----------
        data : list, data to be zipped with header descriptions

        Returns
        -------
        data_out : str, JSON formatted data and metadata
        """
        data_out = {k: v for k, v in zip(self._metadata.header, data)}
        data_out[self.time_format] = self._timepiece.get_time()

        if self._metadata_stream_i == self.metadata_interval:
            self._metadata_stream_i = 0
            data_out = self.add_metadata(data_out)

        self._metadata_stream_i += 1
        return json.dumps(data_out)

    def write(self, data):
        """Write JSON data and metadata at intervals set by
        self.metadata_interval to file location self.path

        Parameters
        ----------
        data : list, data to be zipped with header descriptions
        """
        if self.path is None:
            self.path = (self._timepiece.file_time() + "_" +
                         self._metadata.name.lower().replace(' ', '_') +
                         '.jsontxt')
        data_out = {k: v for k, v in zip(self._metadata.header, data)}
        data_out[self.time_format] = self._timepiece.get_time()

        if self._metadata_file_i == self.metadata_interval:
            self._metadata_file_i = 0
            data_out = self.add_metadata(data_out)

        data_out = json.dumps(data_out)

        with open(self.path, 'a') as f:
            f.write(data_out + self.line_terminator)
        self._metadata_file_i += 1
