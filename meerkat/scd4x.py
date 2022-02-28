"""Sensirion SCD4x CO2 sensor
Chapter references (chr x.x) to Datasheet version '1.1 - April 2021'
2021 Colin Dietrich"""

from meerkat.base import I2C, time
from meerkat.data import Meta, CSVWriter, JSONWriter


def CRC_calc(data):
    """Sensirion Common CRC checksum for 2-byte packets. See ch 3.11
    
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


class SCD4x():
    def __init__(self, bus_n, bus_addr=0x62, output='csv', sensor_id='SCD4x'):
        """Initialize worker device on i2c bus.

        Parameters
        ----------
        bus_n : int, i2c bus number on Controller
        bus_addr : int, i2c bus number of this Worker device
        output : str, writer output format, either 'csv' or 'json'
        sensor_id : str, sensor id, 'BME680' by default
        """

        # i2c bus
        self.bus = I2C(bus_n=bus_n, bus_addr=bus_addr)
        
        # information about this device
        self.metadata = Meta(name='SCD4x')
        self.metadata.description = 'SCD4x CO2 gas Sensor'
        self.metadata.urls = 'https://www.sensirion.com/en/environmental-sensors/carbon-dioxide-sensors/carbon-dioxide-sensor-scd4x/'
        self.metadata.manufacturer = 'Sensirion'
        
        self.metadata.header    = ['system_id', 'sensor_id', 'description', 'sample_n', 'co2',         'tC',              'rh']
        self.metadata.dtype     = ['str',       'str',       'str',         'int',      'int',         'float',           'int']
        self.metadata.units     = ['NA',        'NA',        'NA',          'count',    'ppm',         'degrees Celsius', 'percent']
        self.metadata.accuracy  = ['NA',        'NA',        'NA',          '1',        '+/- 40 + 5%', '+/- 1.5',         '+/- 0.4']
        self.metadata.precision = ['NA',        'NA',        'NA',          'NA',       '+/- 10',      '+/- 0.1',         '+/- 0.4']
        self.metadata.range     = ['NA',        'NA',        'NA',          'NA',       '0-40000',     '-10-60',          '0-100']
        
        self.metadata.bus_n = bus_n
        self.metadata.bus_addr = hex(bus_addr)
        
        # data recording information
        self.system_id = None
        self.sensor_id = sensor_id
        self.dt = None
        
        self.writer_output = output
        self.csv_writer  = CSVWriter(metadata=self.metadata, time_source='std_time_ms')
        self.json_writer = JSONWriter(metadata=self.metadata, time_source='std_time_ms')
    
    # Basic Commands, Ch 3.5
    def start_periodic_measurement(self):
        """Start periodic measurement, updating at a 5 second interval. See Ch 3.5.1"""
        self.bus.write_n_bytes([0x21, 0xB1])
        
    def read_measurement(self):
        """Read measurement from sensor. See Ch 3.5.2
        
        Returns
        -------
        co2 : int, CO2 concentration in ppm
        t : float, temperature in degrees Celsius
        rh : int, relative humidity in percent
        """
        self.bus.write_n_bytes([0xEC, 0x05])
        time.sleep(0.002)
        d = self.bus.read_n_bytes(9)
        d = CRC_check(d)
        
        co2 = d[0] << 8 | d[1]
        t   = d[2] << 8 | d[3]
        rh  = d[4] << 8 | d[5]
        
        t = -45 + 175 * t / 2**16
        rh = 100 * rh / 2**16
        
        d = [co2, t, rh]
        d = [round(n, 2) for n in d]
        return d
        
    def stop_periodic_measurement(self):
        """Stop periodic measurement to change configuration or 
        to save power. Note the sensor will only respond to other 
        commands after waiting 500ms after this command. See Ch 3.5.3"""
        self.bus.write_n_bytes([0x3F, 0x86])
    
    # On-chip output signal compensation, Ch 3.6
    def set_temperature_offset(self, tC):
        """Set the temperature offest, which only affects
        RH and T output. See Ch 3.6.1
        
        Parameters
        tC : float, temperature offset in degrees Celsius
        """
        tC = (tC * 2**16) / 175
        d0 = tC >> 8
        d1 = tC & 0xff
        d2 = CRC_check([d0, d1])
        self.bus.write_n_bytes([0x24, 0x1D, d0, d1, d2])
        time.sleep(0.01)
        
    def get_temperature_offset(self):
        """Get the temperature offset, which only affects 
        RH and T output. See Ch 3.6.2
        
        Returns
        -------
        float, temperature offset in degrees Celsius
        """
        self.bus.write_n_bytes([0x23, 0x18])
        time.sleep(0.01)
        d = self.bus.read_n_bytes(3)
        d = CRC_check(d)
        d = d[0] << 8 | d[1]
        return (175 * d) / 2**16
        
    def set_sensor_altitude(self, meters):
        """Set the altitude into memory. See Ch 3.6.3"""
        d0 = meters >> 8
        d1 = meters & 0xff
        d2 = CRC_check([d0, d1])
        self.bus.write_n_bytes([0x24, 0x27, d0, d1, d2])
        time.sleep(0.01)
        
    def get_sensor_altitude(self):
        """Get the altitude set in memory, this is not an 
        active measurement. See Ch 3.6.4
        
        Returns
        -------
        int, altitude in meters above sea level
        """
        self.bus.write_n_bytes([0x23, 0x22])
        time.sleep(0.002)
        d = self.bus.read_n_bytes(3)
        d = CRC_check(d)
        return d[0] << 8 | d[1]
        
    def set_ambient_pressure(self, pressure):
        """Set ambient pressure to enable continuous pressure
        compensation. See Ch 3.6.5
        
        Parameters
        ----------
        pressure : int, pressure in Pascals (Pa)
        """
        pressure = pressure / 100
        crc = CRC_calc([0x00, pressure])
        d = [0x00, pressure, crc]
        self.bus.write_n_bytes([0xE0, 0x00] + d)
        time.sleep(0.002)  
        
    # Field Calibration, Ch 3.7
    def perform_forced_recalibration(self, target_ppm):
        """Perform forced recalibration (FRC). See Ch 3.7.1
        
        Parameters
        ----------
        target_ppm : int, target CO2 ppm
        
        Returns
        -------
        int, FRC correction in CO2 ppm
            or
        None if FRC failed 
        """
        self.bus.write_n_bytes([0x36, 0x2F])
        time.sleep(0.41)
        d = self.bus.read_n_bytes(3)
        d = CRC_check(d)
        d = d[0] << 8 | d[1]
        if d == 0xFFF:
            return None
        else:
            return d - 0x8000
        
    def set_automatic_self_calibration(self, asc):
        """Set Automatic Self Calibration (ASC) state. See Ch 3.7.2
        
        Parameters
        ----------
        asc : bool, True for ASC enabled, False for disabled
        """
        
        if asc == True:
            w0 = 0x01
        else:
            w0 = 0x00
        crc = CRC_calc([0x00, w0])
        d = [0x00, w0, crc]
        self.bus.write_n_bytes([0x24, 0x16] + d)
        time.sleep(0.002)
        
    def get_automatic_self_calibration(self):
        """Get Automatic Self Calibration (ASC) state. See Ch 3.7.3
        
        Returns
        -------
        bool, True if ASC is enabled, False for disabled
        """
        self.bus.write_n_bytes([0x23, 0x13])
        time.sleep(0.002)
        d = self.bus.read_n_bytes(3)
        d = CRC_check(d)
        d = d[0] << 8 | d[1]
        if d == 0:
            return False
        else:
            return True
        
    # Low Power, Ch 3.8
    def start_low_power_periodic_measuremet(self):
        """Start low power periodic measurement, updates in
        approximately 30 seconds. See Ch 3.8.1"""
        self.bus.write_n_bytes([0x21, 0xAC])
        
    def data_ready(self):
        """Check if data is ready. See Ch 3.8.2
        
        Returns
        -------
        bool, True if data is ready, otherwise False
        """
        self.bus.write_n_bytes([0xE4, 0xB8])
        d = self.bus.read_n_bytes(3)
        d = CRC_check(d)
        d = d[0] << 8 | d[1]
        d = d & 0b11111111111
        if d == 0:
            return False
        else:
            return True
        
    # Advanced Features, Ch 3.9
    def presist_settings(self):
        """Stores current configuration in the EEPROM making them 
        persist across power-cycling. To avoid failure of the EEPROM, 
        this feature should only be used as required and if actual 
        changes to the configuration have been made. See Ch 3.9.1"""
        self.bus.write_n_bytes([0x36, 0x15])
        time.sleep(0.8)
        
    def get_serial_number(self):
        """Read the serial number to identify the chip and 
        verify presense of the sensor. See Ch 3.9.2"""
        self.bus.write_n_bytes([0x36, 0x82])
        time.sleep(0.01)
        d = self.bus.read_n_bytes(9)
        d = CRC_check(d)
        da = []
        for n in range(0, len(d), 2):
            da.append(d[n] << 8 | d[n+1])
        return da[0] << 32 | da[1] << 16 | da[2]
        
    def perform_self_test(self):
        """Perform a self test as an end-of-line test to check sensor
        functionality and the power supply to the sensor. See Ch 3.9.3"""
        self.bus.write_n_bytes([0x36, 0x39])
        time.sleep(11)
        d = self.bus.read_n_bytes(3)
        d = CRC_check(d)
        return d[0] << 8 | d[1]

    def perform_factory_reset(self):
        """Resets all configuration settings stored in EEPROM and 
        erases the FRC and ASC algorithm history. See Ch 3.9.4"""
        self.bus.write_n_bytes([0x36, 0x32])
    
    def reinit(self):
        """Reinitializes the sensor by reloading user settings from 
        EEPROM. See Ch 3.9.5"""
        self.bus.write_n_bytes([0x36, 0x46])
    
    # Low Power Single Shot, (SCD41 only), Ch 3.10
    def measure_single_shot(self):
        """On-demand measurement of CO2 concentration, relative humidity 
        and temperature. See Ch 3.10.1"""
        self.bus.write_n_bytes([0x21, 0x9D])
        time.sleep(5)
    
    def measure_single_shot_blocking(self):
        """On-demand measurement of CO2 concentration, relative humidity 
        and temperature. See Ch 3.10.1
        
        Returns
        -------
        co2 : int, CO2 concentration in ppm
        t : float, temperature in degrees Celsius
        rh : int, relative humidity in percent
        """
        
        t0 = time.time()        
        self.measure_single_shot()
        time.sleep(5)  # 5000 ms
        self.dt =  time.time() - t0
        return self.read_measurement()
        

    def read_measurement_blocking(self):
        """Read measurement from sensor. See Ch 3.5.2
        
        Returns
        -------
        co2 : int, CO2 concentration in ppm
        t : float, temperature in degrees Celsius
        rh : int, relative humidity in percent
        """
        pass
    
    def measure_single_shot_rht_only(self):
        """On-demand measurement of relative humidity and temperature only. 
        See Ch 3.10.2"""
        self.bus.write_n_bytes([0x21, 0x96])
        time.sleep(0.05)

        

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
            get = self.measure_single_shot_blocking
        else:
            get = self.read_measurement
        
        data_list = []
        for m in range(n):
            d = list(get())
            data_list.append(self.json_writer.publish([self.system_id, self.sensor_id, description, m] + d))
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
            get = self.measure_single_shot_blocking
        else:
            get = self.read_measurement
        
        wr = {"csv": self.csv_writer,
              "json": self.json_writer}[self.writer_output]
        for m in range(n):
            d = list(get())
            wr.write([self.sytem_id, self.sensor_id, self.description, m] + d)
            if delay is not None:
                time.sleep(delay)