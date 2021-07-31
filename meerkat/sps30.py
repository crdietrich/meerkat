"""Sensirion SPS30 Particulate Matter Sensor
Chapter references (chr x.x) to Datasheet version '1.0 - D1 - March 2020'
2021 Colin Dietrich"""

from meerkat.base import I2C, time
from meerkat.data import Meta, CSVWriter, JSONWriter

import struct


def CRC_calc(data):
    """Sensirion Common CRC checksum for 2-byte packets. See ch 6.2
    
    Parameters
    ----------
    data : sequence of 2 bytes
    
    Returns
    -------
    int, CRC check sum
    """
    crc = 0xFF
    for i in range (0, 2):
        crc = crc ^ data[i]
        for j in range(8, 0, -1):
            if crc & 0x80:
                crc = (crc << 1) ^ 0x31
            else:
                crc = crc << 1
    crc = crc & 0x0000FF
    return crc

def CRC_check(data, verbose=False):
    """Apply the Sensirion Common CRC checksum for 2-byte packets
    to a byte array. Check that all values received are uncorrupted 
    by matching the CRC checksum byte (third after 2 data bytes) and 
    returning the data bytes.
    
    Parameters
    ----------
    data : sequence of data, 3 per data value where 
        bytes 0 and 1 are data
        byte 2 is the CRC checksum bytes
        
    Returns
    -------
    sequence of data values with checksum removed
    or
    None if sequence is corrupt and does not match checksum
    """
    d = []
    for i in range(2, len(data), 3):
        crc = data[i]
        n0 = data[i-2]
        n1 = data[i-1]
        crc_calc = CRC_calc([n0, n1])
        if verbose:
            print('crc:', crc, 'crc_calc:', crc_calc)
        if (crc_calc == crc):
            d.append(n0)
            d.append(n1)
        else:
            return d
    return d

def ascii_check(ordinal):
    if (ordinal > 31) & (ordinal < 127):
        return True
    else:
        return False

def ascii_join(data):
    """Convert sequence of numbers to ASCII characters"""
    return ''.join([chr(n) for n in data])


class SPS30():
    def __init__(self, bus_n, bus_addr=0x69, output_format='float', output='csv', name='SPS30'):
        """Initialize worker device on i2c bus.

        Parameters
        ----------
        bus_n : int, i2c bus number on Controller
        bus_addr : int, i2c bus number of this Worker device
        """

        self.output_format = None
        
        # i2c bus
        self.bus = I2C(bus_n=bus_n, bus_addr=bus_addr)
        
        # information about this device
        self.metadata = Meta(name=name)
        self.metadata.description = 'SPS30 Particulate Matter Sensor'
        self.metadata.urls = 'https://www.sensirion.com/en/environmental-sensors/particulate-matter-sensors-pm25'
        self.metadata.manufacturer = 'Sensirion'
        self.metadata.bus_n = bus_n
        self.metadata.bus_addr = hex(bus_addr)
        self.metadata.speed_warning = 0
        self.metadata.laser_error = 0
        self.metadata.fan_error = 0
        
        self.set_format(output_format)
        
        # data recording information
        self.sample_id = None
        
        self.writer_output = output
        self.csv_writer = CSVWriter(metadata=self.metadata, time_format='std_time_ms')
        self.json_writer = JSONWriter(metadata=self.metadata, time_format='std_time_ms')
    
    def set_format(self, output_format):
        """Set output format to either float or integer.
        
        Parameters
        ----------
        output_format : str, either 'int' or 'float' where
            'int' = Big-endian unsigned 16-bit integer values
            'float' = Big-endian IEEE754 float values
        """
        self.output_format = output_format
        
        self.metadata.header = ['description', 'sample_n', 'mc_pm1.0', 'mc_pm2.5', 'mc_pm4.0', 'mc_pm10', 
                   'nc_pm0.5', 'nc_pm1.0', 'nc_pm2.5', 'nc_pm4.0', 'nc_pm10', 'typical_partical_size']
        _units = [None, 'count'] + ['µg/m3']*4 + ['#/cm3']*5
        
        self.metadata.precision = [None, 1, '+/-10', '+/-10', '+/-25', '+/-25', '+/-1.25', '+/-1.25']
        self.metadata.range     = [None, None, '0.3-1.0', '0.3-2.5', '0.3-4.0', '0.3-10',
                                   '0.3-0.5', '0.3-1.0', '0.3-2.5', '0.3-4.0', '0.3-10.0', '0-3000']
        self.metadata.mass_concentration_range = '0-1000µg/m3'
        self.metadata.number_concentration_range = '0-3000 #/cm3'
        self.metadata.accuracy  = [None, 1] + ['NA'] * 10
        
        if output_format == 'int':
            self.metadata.dtype     = ['str', 'int'] + ['int'] * 10
            self.metadata.units     = _units + ['nm']
            
        if output_format == 'float':
            self.metadata.dtype     = ['str', 'int'] + ['float'] * 10
            self.metadata.units     = _units + ['µm']
        
    def start_measurement(self):
        """Start measurement and set the output format. See ch 6.3.1
        
        Parameters
        ----------
        output_format : str, either 'int' or 'float' where
            'int' = Big-endian unsigned 16-bit integer values
            'float' = Big-endian IEEE754 float values
        """
        command = {'int': [0x05, 0x00, 0xF6],
                   'float': [0x03, 0x00, 0xAC]}[self.output_format]
        self.bus.write_n_bytes([0x00, 0x10] + command)
    
    def stop_measurement(self):
        """Stop measurement. See ch 6.3.2"""
        self.bus.write_n_bytes([0x01, 0x04])
    
    def data_ready(self):
        """Read Data-Ready Flag. See ch 6.3.3
        
        Returns
        -------
        bool, True if data is ready, otherwise False
        """
        self.bus.write_n_bytes([0x02, 0x02])
        time.sleep(0.1)
        d = self.bus.read_n_bytes(3)
        d = CRC_check(d)
        if d[1] == 0x00:
            return False
        elif d[1] == 0x01:
            return True
        
    def measured_values_blocking(self, dt=1, timeout=30, continuous=False, verbose=False):
        """Block and poll until new data is available
        
        Parameters
        ----------
        dt : int, seconds to pause between polling requests
        timeout : int, maximum seconds to poll
        continuous : bool, if True do not stop measurement to read latest data
        verbose : bool, print debug statements
        """
        self.start_measurement()
        time.sleep(dt)
        
        t0 = time.time()
        while (time.time() - t0 < timeout):
            if self.data_ready():
                self.stop_measurement()
                return self.measured_values()
            time.sleep(dt)
            if verbose:
                print('waiting...')
        return False
    
    def measured_values(self):
        """Read measured values. See ch 6.3.4 for I2C method 
        and ch 4.3 for format"""
        byte_number = {'int': 30, 'float': 60}[self.output_format]
        self.bus.write_n_bytes([0x03, 0x00])
        time.sleep(0.1)
        d = self.bus.read_n_bytes(byte_number)
        d = CRC_check(d)
        if self.output_format == 'float':
            d_f = []
            for n in range(0, len(d), 4):
                d_f.append(struct.unpack('>f', bytes(d[n:n+4]))[0])
            return d_f
        elif self.output_format == 'int':
            d_i = []
            for n in range(0, len(d), 2):
                d_i.append(struct.unpack('>h', bytes(d[n:n+2]))[0])
            return d_i
        # for just the bytes, set self.output_format == None
        else:
            return d
    
    def sleep(self):
        """Put sesnor to sleep. See ch 6.3.5"""
        self.bus.write_n_bytes([0x10, 0x01])
    
    def wake(self):
        """Power sensor up from sleep state. See ch 6.3.6"""
        self.bus.write_n_bytes([0x11, 0x03])
        self.bus.write_n_bytes([0x11, 0x03])
    
    def start_fan_cleaning(self):
        """Start fan cleaning cycle. See ch 6.3.7"""
        self.bus.write_n_bytes([0x56, 0x07])
    
    def read_cleaning_interval(self):
        """Read the fan cleaning cycle. See ch 6.3.8"""
        self.bus.write_n_bytes([0x80, 0x04])
        time.sleep(0.1)
        d = self.bus.read_n_bytes(6)
        d = CRC_check(d)
        return int((d[0] << 16) | d[1])
    
    def write_cleaning_interval(self, interval):
        """Write the cleaning interval. See ch 6.3.8 and 4.2"""
        i_msb = interval >> 16
        i_lsb = interval & (2**16 -1)
        self.bus.write_n_bytes([0x80, 0x04, i_msb, i_lsb])    
    
    def product_type(self):
        """Read product type. See ch 6.3.9"""
        self.bus.write_n_bytes([0XD0, 0X02])
        time.sleep(0.1)
        d = self.bus.read_n_bytes(12)
        d = CRC_check(d)
        d = [chr(x) for x in d if ascii_check(x)]
        return ''.join(d)
    
    def serial(self):
        """Read device serial number. See ch 6.3.9"""
        self.bus.write_n_bytes([0xD0, 0x33])
        time.sleep(0.1)
        d = self.bus.read_n_bytes(48)
        d = CRC_check(d)
        d = [chr(x) for x in d if ascii_check(x)]
        return ''.join(d)
    
    def version(self):
        """Get firmware version in major.minor notation. See ch 6.3.10"""
        self.bus.write_n_bytes([0xD1, 0x00])
        d = CRC_check(d)
        d = [chr(x) for x in d if ascii_check(x)]
        return '.'.join(d)
    
    def status(self):
        """Get status device status. See ch 4.4"""
        self.bus.write_n_bytes([0xD2, 0x06])
        time.sleep(0.1)
        d = self.bus.read_n_bytes(6)
        d = CRC_check(d)
        d = (d[0] << 8) + d[1]
        self.metadata.speed_warning = d & (1 << 21 -1)
        self.metadata.laser_error = d & (1 << 5 -1)
        self.metadata.fan_error = d & (1 << 4 -1)
        return (self.metadata.speed_warning, 
                self.metadata.laser_error,
                self.metadata.fan_error)
        
    def status_clear(self):
        """Clear device status. See ch 6.3.12"""
        self.bus.write_n_bytes([0xD2, 0x10])
    
    def reset(self):
        """Reset device. See ch 6.3.13"""
        self.bus.write_n_bytes([0xD3, 0x04])

    def publish(self, description='NA', n=1, delay=None, blocking=True):
        """Get measured air partical data and output in JSON, 
        plus metadata at intervals set by self.metadata_interval
        
        Parameters
        ----------
        description : str, description of data collected
        n : int, number of samples to record in this burst
        delay : float, seconds to delay between samples if n > 1
        blocking : bool, if True wait until data is ready. If False, 
            self.start_measurement and self.stop_measurement must be 
            called externally to this method.
        
        Returns
        -------
        str, formatted in JSON with keys:
            description : str
            n : sample number in this burst
            and values as described in self.metadata.header
        """
        
        if blocking:
            get = self.measured_values_blocking
        else:
            get = self.measured_values
        
        data_list = []
        for m in range(n):
            data_list.append(self.json_writer.publish([description, m] + get()))
            if n == 1:
                return data_list[0]
            if delay is not None:
                time.sleep(delay)
        return data_list

    def write(self, description='NA', n=1, delay=None, blocking=True):
        """Get measured air partical data and save to file, 
        formatted as either CSV with extension .csv or 
        JSON and extension .jsontxt.

        Parameters
        ----------
        description : str, description of data collected
        n : int, number of samples to record in this burst
        delay : float, seconds to delay between samples if n > 1
        blocking : bool, if True wait until data is ready. If False, 
            self.start_measurement and self.stop_measurement must be 
            called externally to this method.

        Returns
        -------
        None, writes to disk the following data:
            description : str
            n : sample number in this burst
            and values as described in self.metadata.header
        """
        
        if blocking:
            get = self.measured_values_blocking
        else:
            get = self.measured_values
            
        wr = {"csv": self.csv_writer,
              "json": self.json_writer}[self.writer_output]
        for m in range(n):
            wr.write([description, m] + get())
            if delay is not None:
                time.sleep(delay)