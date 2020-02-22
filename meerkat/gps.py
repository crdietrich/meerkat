"""Global Positioning System I2C Driver for Raspberry PI & MicroPython"""

from time import sleep

from meerkat.base import Device


class GPS(object):
    def __init__(self, machine, name):

        self.machine = machine
        self.uart_class = None
        self.rtc = self.machine.RTC()

        self.uart = None
        self.baud = 9600
        self.port = 6

        self.supported_messages = [b'GPRMC', b'GPGGA']

        self.valid = False
        self.lock = False

        self.lock_timeout = 60    # total time to look for a gps lock in seconds
        self.lock_timeout_dt = 1  # time to sleep while searching for a lock in seconds

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

        # Date and Time
        self.date_time_raw = ''
        self.date_time_pretty = ''
        self.year = None
        self.month = None
        self.day = None
        self.hour = None
        self.minute = None
        self.second = None

        self.state = 'min'  # 'time', 'min', 'all', 'raw'
        self.verbose = True

        self.go = False

    def open(self):
        self.uart = self.machine.UART(self.port, self.baud)

    def crc(self, line):
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
        try:
            self.gprmc_handler_min(items)
            self.speed = items[7]
            self.track_angle = items[8]
            self.mag_var = items[10]
        except IndexError:
            pass

    def gprmc_handler_min(self, items):
        """Get values from NMEA GPRMC string"""
        try:
            self.gprmc_time(items)
            #self.rmc_status = items[2]
            self.lat = items[3]
            self.lat_dir = items[4]
            self.lon = items[5]
            self.lon_dir = items[6]
        except IndexError:
            pass

    def gprmc_time(self, items):
        try:
            self.utc = items[1]
            self.rmc_date = items[9]
        except IndexError:
            pass

    def gpgga_handler(self, items):
        """Get values from NMEA GPGGA string"""
        try:
            self.gpgga_handler_min(items)
            self.svn_number = items[7]
            self.hdop = items[8]
            print(self.lat, self.lon)

        except IndexError:
            pass

    def gpgga_handler_min(self, items):
        try:
            self.utc = items[1]
            self.lat = items[2]
            self.lat_dir = items[3]
            self.lon = items[4]
            self.lon_dir = items[5]
            self.gps_quality = items[6]
        except IndexError:
            pass

    def pre_fetcher(self, items):
        _id = items[0]
        if _id == 'GPRMC':
            utc = items[1]
            rmc_status = items[2]
            rmc_date = items[9]
            return rmc_status, rmc_date + utc
        else:
            return False, False

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
            self.year = int('20' + self.rmc_date[4:6])
            self.month = int(self.rmc_date[2:4])
            self.day = int(self.rmc_date[0:2])
            self.hour = int(self.utc[0:2])
            self.minute = int(self.utc[2:4])
            self.second = int(self.utc[4:6])

            self.date_time_raw = self.rmc_date + self.utc
            self.date_time_pretty = (str(self.year)
                                     + '/' + str(self.month)
                                     + '/' + str(self.day)
                                     + '_' + str(self.hour)
                                     + ':' + str(self.minute)
                                     + ':' + str(self.second))
        # if either data type hasn't been captured yet and values are None
        except TypeError:
            pass

    def verbose_terminal(self, line):

        print('line >>', line)
        try:
            items, data, checksum_gps = self.extract(line)
        except ValueError:
            return
        if self.validate(data, checksum_gps):
            print('validiate>> gps +++ CRC Valid +++')
        else:
            print('validate>> gps ---- CRC NOT valid ---')
            return

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

    def crc_valid(self, data, checksum_gps):
        self.valid = self.crc(data) == checksum_gps
        return self.valid

    def stream_terminal(self):

        while self.go:
            line = self.uart.readline()
            print('stream_terminal>>', line)
            if self.supported(line):
                self.verbose_terminal(line)

    def stream(self):

        while self.go:
            print(self.uart.readline())

    def lock_valid(self, rmc_status, date_time_raw, verbose=True):
        status_dict = {'A': True, 'V': False}
        valid = False
        if rmc_status is not None:
            valid = status_dict[rmc_status]
            if verbose:
                print('RMC status:', rmc_status, '& lock valid:', valid)
        if valid & (date_time_raw != self.date_time_raw):
            return True
        else:
            return False

    def update_rtc(self, how='both', verbose=True):
        c = 0
        while True:
            line = self.uart.readline()
            if self.supported(line):
                if verbose:
                    print('update_rtc parsing >>', line)
                try:
                    items, data, checksum_gps = self.extract(line)
                    if self.crc_valid(data=data, checksum_gps=checksum_gps):
                        if verbose:
                            print('GPS data crc valid')
                        rmc_status_now, date_time_raw_now = self.pre_fetcher(items)
                        if not rmc_status_now:
                            continue
                        if self.lock_valid(rmc_status=rmc_status_now,
                                           date_time_raw=date_time_raw_now):
                            if how == 'both' or how == 'gps':
                                self.handler(items)
                                self.set_date_time()
                                print('GPS lock found, Location updated')
                            if how == 'both' or how == 'rtc':
                                if verbose:
                                    print('RTC old time >>', self.rtc_pretty(self.rtc.datetime()))
                                self.rtc.datetime((self.year, self.month, self.day, 0, self.hour, self.minute, self.second, 0))
                                if verbose:
                                    print('RTC new time >>', self.rtc_pretty(self.rtc.datetime()))
                                    print('GPS lock found, Location and RTC updated.')
                            break
                    else:
                        if verbose:
                            print('GPS data crc NOT valid')
                except ValueError:
                    continue
            c += 1
            if c > self.lock_timeout:
                if verbose:
                    print('GPS lock timeout %ss met.' % self.lock_timeout)
                break
            else:
                sleep(self.lock_timeout_dt)

    def rtc_pretty(self, rtc_tuple):
        _m = [str(_n) for _n in rtc_tuple]
        _s = (_m[0] + '/' + _m[1] + '/' + _m[2] + '_' +
              _m[4] + ':' + _m[5] + ':' + _m[6] + '.' + _m[7])
        return _s
