"""GPS connect to Adafruit Ultimate v3"""

from meerkat.base import Device


def crc(line):
    """Calculate the cyclic redundancy check (CRC) for a string
    Parameters
    ----------
    line : str, characters to calculate crc
    Returns
    -------
    crc : str, in hex notation
    """

    c = ord(line[0:1])
    for n in range(1,len(line)-1):
        c = c ^ ord(line[n:n+1])
    return '%X' % c

class GPS(object):

    def __init__(self, machine_uart, name):
        # super().__init__(name)

        self.uart_class = machine_uart
        
        self.uart = None
        self.baud = 9600
        self.port = 6

        self.supported_messages = [b'GPRMC', b'GPGGA']

        self.valid = False
        self.lock = False
        
        self.date_time_raw = ''
        self.date_time_pretty = ''
        
        # $GPRMC
        self.gprmc = None
        self.utc = None
        self.rmc_status = None
        self.lat = None
        self.lat_dir = None
        self.lon = None
        self.lon_dir = None
        self.speed = None
        self.track_angle = None
        self.rmc_date = None
        self.mag_var = None
        
        # $GPGGA
        self.gpgga = None
        self.utc = None
        self.lat = None
        self.lat_dir = None
        self.lon = None
        self.lon_dir = None
        self.gps_quality = None
        self.svn_number = None
        self.hdop = None

        self.state = 'min'  # 'time', 'min', 'all', 'raw'
        self.verbose = True

        self.go = False


    def open(self):
        
        self.uart = self.uart_class(self.port, self.baud)

    def supported(self, line, verbose=False):
        if line is None:
            if verbose:
                print('gps>> None line from GPS')
            return False
        if len(line) <= 0:
            if verbose:
                print('gps>> Line length 0')
            return False
        code = line[1:6]
        if code in self.supported_messages:
            if verbose:
                print('gps>> supported code found')
            return True
        else:
            if verbose:
                print('gps>> code found, not supported')
            return False

    def gprmc_handler(self, items):
        """Get values from NMEA GPRMC string"""
        self.gprmc_handler_min(items)
        self.speed = items[7]
        self.track_angle = items[8]
        self.mag_var = items[10]
    
    def gprmc_handler_min(self, items):
        """Get values from NMEA GPRMC string"""
        self.gprmc_time(items)
        self.rmc_status = items[2]
        self.lat = items[3]
        self.lat_dir = items[4]
        self.lon = items[5]
        self.lon_dir = items[6]

    def gprmc_time(self, items):
        self.utc = items[1]
        self.rmc_date = items[9]
                
    def gpgga_handler(self, items):
        """Get values from NMEA GPGGA string"""
        self.gpgga_handler_min(items)
        self.svn_number = items[7]
        self.hdop = items[8]

        print(self.lat, self.lon)

    def gpgga_handler_min(self, items):
        self.utc = items[1]
        self.lat = items[2]
        self.lat_dir = items[3]
        self.lon = items[4]
        self.lon_dir = items[5]
        self.gps_qualty = items[6]
        
    def handler(self, items):
        self.set_attributes(items)
        
    def set_attributes(self, items):
        id = items[0]
        if id == 'GPGGA':
            if self.state == 'min':
                self.gpgga_handler_min(items)
            elif self.state == 'all':
                self.gpgga_handler(items)
        if id == 'GPRMC':
            if self.state == 'time':
                self.gprmc_time(items)
            elif self.state == 'min':
                self.gprmc_handler_min(items)
            elif self.state == 'all':
                self.gprmc_handler(items)

    def set_date_time(self):
        try:
            self.date_time_raw = self.rmc_date + self.utc
            self.date_time_pretty = ('20' 
                                     + self.rmc_date[4:6]
                                     + '/' + self.rmc_date[2:4]
                                     + '/' + self.rmc_date[0:2]
                                     + '_' + self.utc[0:2]
                                     + ':' + self.utc[2:4]
                                     + ':' + self.utc[4:6])
        # if either data type hasn't been captured yet
        except TypeError:
            pass
    
    def verbose_terminal(self, line):
        
        print("line >>", line)
        
        items, data, checksum_gps = self.extract(line)

        if self.validiate(data, checksum_gps):
            print('validiate>> gps +++ CRC Valid +++')
            # self.handler(items)
        else:
            print('validate>> gps ---- CRC NOT valid ---')
            
        self.handler(items)
        self.set_date_time()
        print('verbose_terminal>> date_time_raw:', self.date_time_raw)
        print('verbose_terminal>> date_time_pretty:', self.date_time_pretty)

    def extract(self, line):
        line = line.decode('utf-8').strip()
        data, checksum_gps = line.split('$')[1].split('*')
        items = data.split(',')
        data += '*'
        return items, data, checksum_gps
        
    def validiate(self, data, checksum_gps):
        self.valid = crc(data) == checksum_gps
        return self.valid
        
    def stream_terminal(self):
        while self.go:
            line = self.uart.readline()
            if self.supported(line):
                self.verbose_terminal(line)

    def stream(self):
        
        while self.go:
            print(self.uart.readline())

    def update_valid(self, rmc_status, date_time_raw):
        if (self.rmc_status == 'A') & (date_time_raw != self.date_time_raw):
            return True
        else:
            return False
        
    def update(self):
        date_time_raw = self.date_time_raw
        while True:
            line = self.uart.readline()
            if self.supported(line):
                print("update>>", line)
                items, data, checksum_gps = self.extract(line)
                self.handler(items)
                self.set_date_time()
                if self.update_valid(rmc_status=self.rmc_status, date_time_raw=date_time_raw):
                    print("Updated!")
                    print(date_time_raw, self.date_time_raw)
                    break
                