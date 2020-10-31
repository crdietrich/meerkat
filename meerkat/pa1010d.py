"""CDTop MTK3333 GPS I2C Driver for Raspberry PI & MicroPython

Source:
https://www.adafruit.com/product/4415

Datasheets:
https://cdn-learn.adafruit.com/assets/assets/000/084/295/original/CD_PA1010D_Datasheet_v.03.pdf?1573833002
https://cdn.sparkfun.com/assets/parts/1/2/2/8/0/GTOP_NMEA_over_I2C_Application_Note.pdf
https://www.cdtop-tech.com/products/pa1010d
"""

import re

from meerkat.base import I2C, DeviceData, time
from meerkat.data import CSVWriter, JSONWriter


regex = re.compile("[\r\n]")


def calc_checksum(s):
    """NMEA checksum calculation"""
    checksum = 0
    for char in s:
        checksum ^= ord(char)
    return "{:02x}".format(checksum).upper()


class PA1010D:
    def __init__(self, bus_n, bus_addr=0x10, output='csv'):
        """PA1010D GPS module using MTK3333 chipset
        
        Supported NMEA sentences
        
        Parameters
        ----------
        bus_n : int, i2c bus number on Controller
        bus_addr : int, i2c bus number of this Worker device
        nmea_sentence : str, NMEA sentence type to save for CSV.
            JSON will save
        """

        # i2c bus
        self.bus = I2C(bus_n=bus_n, bus_addr=bus_addr)

        # maximum data in buffer size
        self._bytes_per_burst = 255
        
        # information about this device
        self.device = DeviceData('pa1010d')
        self.device.description = 'Adafruit PA1010D GPS/GNSS module'
        self.device.urls = 'https://www.cdtop-tech.com/products/pa1010d'
        self.device.active = None
        self.device.error = None
        self.device.bus = repr(self.bus)
        self.device.manufacturer = 'CDTop Technology'
        self.device.version_hw = '1.0'
        self.device.version_sw = '1.0'
        self.device.accuracy = None
        self.device.precision = '<3.0 meters'
        self.device.calibration_date = None
        
        # data recording method
        self.writer_output = output
        self.csv_writer = CSVWriter("PA1010D", time_format='std_time_ms')
        self.csv_writer.device = self.device.__dict__
        self.csv_writer.header = ["description", "sample_n", "nmea_sentence"]

        self.json_writer = JSONWriter("PA1010D", time_format='std_time_ms')
        self.json_writer.device = self.device.__dict__
        self.json_writer.header = self.csv_writer.header

    def raw_get(self):
        """Get byte data from the GPS module, filtered of blanks
        and combining lines"""
        
        data = ""
        _d = self.bus.read_n_bytes(n=self._bytes_per_burst)
        _d = _d.decode("UTF-8")
        data = "".join([data, _d])

        data = regex.split(data)
        data = [_d for _d in data if _d != ""]
        data = set(data)

        data_out = []
        last_line = ""
        started = False

        for line in data:
            if (line[0] == "$") & ("*" in line):
                data_out.append(line)
            elif ("$" in line):
                last_line = line
            elif ("*" in line) & (last_line != ""):
                data_out.append(last_line + line)

        return data_out
        
    def get(self, nmea_sentences=['GGA', 'GSA', 'GSV', 'RMC', 'VTG'], timeout=15):
        """Get NMEA sentences
        
        Parameters
        ----------
        nmea_sentence : list of str, NMEA sentence codes to return i.e. 'GSV'
        timeout : int, seconds to wait for data before returning
        
        Returns
        -------
        list of str, NMEA sentences
        """
        
        check = {s: False for s in nmea_sentences}
        
        t0 = time.time()
        while sum([x == False for x in check.values()]) > 0:
            if time.time() - t0 > timeout:  # timeout in seconds
                break
            
            for single_line in self.raw_get():
                sentence_type = single_line[3:6]
                if (sentence_type in nmea_sentences) & ("*" in single_line):
                    gps_data = single_line.split("*")
                    gps_cs = gps_data[1]
                    gps_data = gps_data[0][1:]
                    driver_cs = calc_checksum(gps_data)
                    if gps_cs == driver_cs:
                        check[sentence_type] = single_line
                        
        return [v for k, v in check.items()]
        
    def send_command(self, command, add_format=True):
        """Send a command string to the GPS.
        
        Note: If add_format=True, do not add leading 
        '$' and trailing '*' plus checksum, these will 
        be added automatically
        
        Parameters
        ----------
        command : str, command to send
        add_format : bool, add '$' prefix and '*' plus calculated checksum
        """
        if add_format:
            checksum = calc_checksum(command)
            command = "${}*{}\r\n".format(command, checksum)
        command = bytes(command)
        self.bus.write_n_bytes(command)
        
    def full_power_mode(self):
        """Enable full power continuous mode"""
        self.send_command(b"$PMTK225,0*2B", add_format=False)
        
    def standby_mode(self):
        """Enable standby power mode"""
        self.send_command(b"$PMTK161,0*28", add_format=False)
        
    def periodic_mode(self, mode_type, rt1, st1, rt2, st2):
        """Enable periodic power on/off mode
        
        Parameters
        ----------
        mode_type : int, 1 or 2 where:
            1 = periodic backup mode
            2 = periodic standby mode
            See other mode method for descriptions
        rt1 : int, full power mode length in milliseconds
        st1 : int, mode_type length in milliseconds
        rt2 : int, full power mode length in milliseconds
        st2 : int, mode_type length in milliseconds
        """
        assert mode_type in [1,2]
        
        command = "PMTK225{},{},{},{},{}".format(mode_type, rt1, st1, rt2, st2)
        command = bytes(command)
        self.send_command(command, add_format=True)
        
    def always_locate_mode(self):
        """Enable always locate mode"""
        self.send_command(b"$PMTK225,8*23", add_format=False)
        
    def backup_mode(self):
        """Enable backup mode 
        Note: Before sending the command the WAKE-UP pin (pin 2) must 
        be tied to ground. It is not possible to wake up the module 
        from backup mode by software command."""
        self.send_command(b"$PMTK225,4*2F", add_format=False)
        
    def publish(self, description='NA', n=1, 
                nmea_sentences=['GGA', 'GSA', 'GSV', 'RMC', 'VTG'], delay=None):
        """Output relay status data in JSON.

        Parameters
        ----------
        description : str, description of data sample collected
        n : int, number of samples to record in this burst
        nmea_sentence : list of str, NMEA sentence codes to return i.e. 'GSV'
        delay : float, seconds to delay between samples if n > 1

        Returns
        -------
        str, formatted in JSON with keys:
            description : str
            n : sample number in this burst
            nmea_sentence : str, NMEA sentence
        """
        data_list = []
        for m in range(n):
            nmea_data = self.get(nmea_sentences=nmea_sentences)
            for p in range(len(nmea_data)):
                data = self.json_writer.publish([description, m, nmea_data[p]])
                data_list.append(data)
            if delay is not None:
                time.sleep(delay)
        return data_list
        
    def write(self, description='NA', n=1, 
              nmea_sentences=['GGA', 'GSA', 'GSV', 'RMC', 'VTG'], delay=None):
        """Format output and save to file, formatted as either .csv or .json.

        Parameters
        ----------
        description : str, description of data sample collected
        n : int, number of samples to record in this burst
        nmea_sentence : list of str, NMEA sentence codes to return i.e. 'GSV'
        delay : float, seconds to delay between samples if n > 1

        Returns
        -------
        None, writes to disk the following data:
            description : str
            n : sample number in this burst
            nmea_sentence : str, NMEA sentence
        """ 
        wr = {"csv": self.csv_writer,
              "json": self.json_writer}[self.writer_output]
        for m in range(n):
            nmea_data = self.get(nmea_sentences=nmea_sentences)
            for p in range(len(nmea_data)):
                wr.write([description, m, '"' + nmea_data[p] + '"'])
            if delay is not None:
                time.sleep(delay)
