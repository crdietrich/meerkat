"""CSV and JSON writing and publishing methods"""


from meerkat.base import Base, _json_dumps
from meerkat.data.timepiece import TimePiece


class Meta(Base):
    """Metadata for data source"""
    def __init__(self, name):

        # device/source specific descriptions
        self.name         = name  # name of data source being recorded
        self.description  = None  # description of the data source being recorded
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
    Note 3: Properties hide class attributes from being written as metadata
    """
    def __init__(self, metadata, time_source):
        """
        Parameters
        ----------
        metadata : meerkat.data.Meta class instance
        time_source : str, meerkat.data.TimePiece class data source. 
            One of 'local', 'rtc', 'gps', 'external'. Default is 'local'
        """
        # file information
        self.encoding        = 'utf-8'  # encoding of output. Should stay 'utf-8'!
        self.format          = None     # format of data being written, CSV, JSON, etc
        self.standard        = None     # standard for format
        self.licenses        = None     # if there's licensing restrictions

        # file formatting conventions
        # TODO: establish if line_terminator is needed, it might complicate JSON parsing
        self.line_terminator = '\n'    # note: in JSON, this will load as '\n' into a dict
        #self.quote_char      = '"'     # note: in JSON, a quote will be "\""
        #self.double_quote    = True     #
        #self.escape_char     = '\\'    # note: \\ to escape \ in JSON... meta.
        self.null_sequence   = 'NA'     #
        self.comment         = '#'      #

        # device metadata
        self._metadata = metadata

        # filepath information
        self.path = None
        self.directory = None

        # timestamp information
        self.time_source = time_source
        self.time_kind = 'std_time_ms'
        
        self._timepiece = TimePiece(source=self.time_source, kind=self.time_kind)
        #self.set_time_source(self.time_source)
        #self.set_time_kind(self.time_kind)

    def set_time_source(self, time_source):
        """Override default TimePiece data source

        Parameters
        ----------
        time_source : str, meerkat.data.TimePiece class data source. 
            One of 'local', 'rtc', 'gps', 'external'
        """
        self.time_source = time_source
        self._timepiece.source = time_source
    
    def set_time_kind(self, time_kind):
        """Override default TimePiece output kind
        Parameters
        ----------
        time_kind : str, meerkat.data.TimePiece class data output kind.
            one of 'std_time', std_time_ms', 'iso_time', 'file_time', 'gps_location'
        """
        self.time_kind = time_kind
        self._timepiece.set_kind(time_kind)

    def set_time(self, time_str):
        self._timepiece.set_time(time_str)


class CSVWriter(WriterBase):
    """Attributes of comma delimited values (CSV) data formatting"""
    def __init__(self, metadata, time_source='std_time'):
        super().__init__(metadata, time_source)

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
            if self.directory is None:
                directory = ""
            else:
                directory = self.directory + '/'
            self.path = (directory + self._timepiece.file_time() + '_' +
                         self._metadata.name.lower().replace(' ', '_') +
                         '.csv')
        with open(self.path, 'w') as f:
            f.write(self.create_metadata() + self.line_terminator)
            if self._metadata.header is not None:
                h = ','.join(['timestamp', self.time_source] + self._metadata.header)
                f.write(h + self.line_terminator)

    def _write_append(self, data):
        """Append data to an existing file at location self.path"""
        with open(self.path, 'a') as f:
            dc = ','.join([self._timepiece.get_time(), self.time_source] +
                          [str(_x) for _x in data])
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
    """Attributes of JSON key-value data formatting"""
    def __init__(self, metadata, time_source='std_time'):
        super().__init__(metadata, time_source)

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

    def publish(self, data, timestamp=None):
        """Return JSON data and metadata at intervals set by self.metadata_interval

        Parameters
        ----------
        data : list, data to be zipped with header descriptions

        Returns
        -------
        data_out : str, JSON formatted data and metadata
        """
        data_out = {k: v for k, v in zip(self._metadata.header, data)}

        if timestamp is None:
            timestamp = self._timepiece.get_time()
        data_out['timestamp'] = timestamp
        data_out['time_source'] = self.time_source

        if self._metadata_stream_i == self.metadata_interval:
            data_out = self.add_metadata(data_out)
            self._metadata_stream_i = 1
        else:
            self._metadata_stream_i += 1
        return _json_dumps(data_out)

    def write(self, data):
        """Write JSON data and metadata at intervals set by
        self.metadata_interval to file location self.path

        Parameters
        ----------
        data : list, data to be zipped with header descriptions
        """
        if self.path is None:
            if self.directory is None:
                self.directory = ""
            self.path = (self.directory + '/' + self._timepiece.file_time() + "_" +
                         self._metadata.name.lower().replace(' ', '_') +
                         '.jsontxt')

        data_out = self.publish(data)

        with open(self.path, 'a') as f:
            f.write(data_out + self.line_terminator)
