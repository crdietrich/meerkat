"""DS3221 Precision RTC I2C Driver for Raspberry PI & MicroPython
https://datasheets.maximintegrated.com/en/ds/DS3231.pdf
https://www.adafruit.com/product/3013
"""

from meerkat.base import I2C, time
from meerkat.data import Meta, CSVWriter, JSONWriter


def bcd2dec(bcd):
    """Binary Coded Decimal to Decimal conversion

    Parameters
    ----------
    bcd : int, binary coded decimal

    Returns
    -------
    decimal number
    """
    return ((bcd & 0b11110000) >> 4) * 10 + (bcd & 0b00001111)


def dec2bcd(dec):
    """Decimal to Binary Coded Decimal conversion

    Parameters
    ----------
    dec : decimal number

    Returns
    ----------
    bcd : int, binary coded decimal
    """
    t = dec // 10
    o = dec - t * 10
    return (t << 4) + o


class DS3231:
    def __init__(self, bus_n, bus_addr=0x68, output='csv', name='DS3231'):
        """Initialize worker device on i2c bus.

        Parameters
        ----------
        bus_n : int, i2c bus number on Controller
        bus_addr : int, i2c bus number of this Worker device
        output : str, output data format, either 'csv' (default) or 'json'
        """

        # i2c bus
        self.bus = I2C(bus_n=bus_n, bus_addr=bus_addr)

        # information about this device
        self.metadata = Meta(name=name)
        self.metadata.description = 'Adafruit DS3221 Precision RTC'
        self.metadata.urls = 'https://datasheets.maximintegrated.com/en/ds/DS3231.pdf'
        self.metadata.manufacturer = 'Adafruit Industries'
        
        self.metadata.header    = ["description", "sample_n", "rtc_time", "temp_C"]
        self.metadata.dtype     = ['str', 'int', 'str', 'float']
        self.metadata.units     = [None, 'count', 'datetime', 'degrees Celcius']
        self.metadata.accuracy  = [None, 1, '+/- 3.5 ppm', '+/- 3.0'] 
        self.metadata.precision = [None, 1, '1 second', 0.25]
        
        self.metadata.bus_n = bus_n
        self.metadata.bus_addr = hex(bus_addr)

        # python strftime specification for RTC output precision
        self.metadata.rtc_time_source = '%Y-%m-%d %H:%M:%S'
        
        # data recording method
        # note: using millisecond accuracy on driver timestamp, even though
        # RTC is only 1 second resolution
        self.writer_output = output
        self.csv_writer = CSVWriter(metadata=self.metadata, time_source='std_time_ms')
        self.json_writer = JSONWriter(metadata=self.metadata, time_source='std_time_ms')
        
    def set_time(self, YY, MM, DD, hh, mm, ss, micro, tz):
        """Set time of RTC

        Parameters
        ----------
        YY : int, year range 1900 to 2100 (approx)
        MM : int, month, range 1 to 12
        DD : int, day, range 1 to 31
        hh : int, hour, range 0 to 23 (24hr clock) or 1-12 (12 hr clock)
        mm : int, minute, range 1-59
        ss : int, second, range 1-59
        micro : int, microseconds, range 0-999 (not implemented)
        tz : str, time zone (not implemented)
        """

        self.bus.write_register_8bit(reg_addr=0x00, data=dec2bcd(ss))
        self.bus.write_register_8bit(reg_addr=0x01, data=dec2bcd(mm))
        self.bus.write_register_8bit(reg_addr=0x02, data=dec2bcd(hh))
        self.bus.write_register_8bit(reg_addr=0x04, data=dec2bcd(DD))

        if YY >= 2000:
            MM = dec2bcd(MM) | 0b10000000
            YY = dec2bcd(YY - 2000)
        else:
            MM = dec2bcd(MM)
            YY = dec2bcd(YY - 1900)

        self.bus.write_register_8bit(reg_addr=0x05, data=MM)
        self.bus.write_register_8bit(reg_addr=0x06, data=YY)

    def get_time(self):
        """Get time from RTC

        Returns
        ----------
        YY : int, year range 1900 to 2100 (approx)
        MM : int, month, range 1 to 12
        DD : int, day, range 1 to 31
        hh : int, hour, range 0 to 23 (24hr clock) or 1-12 (12 hr clock)
        mm : int, minute, range 1-59
        ss : int, second, range 1-59
        """

        data = self.bus.read_register_nbyte(reg_addr=0x00, n=7)

        ss = bcd2dec(data[0] & 0b01111111)
        mm = bcd2dec(data[1] & 0b01111111)
        if data[2] & 0b01000000 > 0:
            hh = bcd2dec(data[2] & 0b00011111)
            if data[2] & 0b00100000 > 0:
                hh += 12
        else:
            hh = bcd2dec(data[2] & 0b00111111)
        DD = bcd2dec(data[4] & 0b00111111)
        MM = bcd2dec(data[5] & 0b00011111)
        YY = bcd2dec(data[6])
        if data[5] & 0b10000000 > 0:
            YY = YY + 2000
        else:
            YY = YY + 1900
        return YY, MM, DD, hh, mm, ss

    def get_temp(self):
        """Get temperature of RTC

        Returns
        -------
        float, temperature in degrees Celsius
        """
        data = self.bus.read_register_nbyte(reg_addr=0x11, n=2)
        return float(data[0]) + (data[1] >> 6) * 0.25

    def publish(self, description='NA', n=1, delay=None):
        """Get RTC time and temperature in JSON, plus metadata at intervals
        set by self.metadata_interval

        Parameters
        ----------
        description : char, description of data sample collected, default='NA'
        n : int, number of samples to record in this burst
        delay : float, seconds to delay between samples if n > 1

        Returns
        -------
        str, formatted in JSON with keys:
            description : str
            n : sample number in this burst
            std_time : str, time formatted in YY-MM-DD hh:mm:ss
            temp_C : float, temperature of RTC in degrees C
        """
        data_list = []
        for m in range(n):
            std_time = '{:02d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}'.format(*self.get_time())
            temp_C = self.get_temp()
            data_list.append(self.json_writer.publish([description, 0, std_time, temp_C]))
            if n == 1:
                return data_list[0]
            if delay is not None:
                time.sleep(delay)
        return data_list

    def write(self, description='NA', n=1, delay=None):
        """Get RTC time and temperature and save to file,
        formatted as either .csv or .json.

        Parameters
        ----------
        description : str, description of data sample collected
        n : int, number of samples to record in this burst
        delay : float, seconds to delay between samples if n > 1

        Returns
        -------
        None, writes to disk the following data:
            description : str
            n : sample number in this burst
            std_time : str, time formatted in YY-MM-DD hh:mm:ss
            temp_C : float, temperature of RTC in degrees C
        """
        wr = {"csv": self.csv_writer,
              "json": self.json_writer}[self.writer_output]
        for m in range(n):
            std_time = '{:02d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}'.format(*self.get_time())
            temp_C = self.get_temp()
            wr.write([description, m, std_time, temp_C])
            if delay is not None:
                time.sleep(delay)
