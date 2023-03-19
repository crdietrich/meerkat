"""TSL2591 Light Sensor

Note: Iterrupt features not implemented.
"""

from meerkat.base import I2C, time
from meerkat.data import Meta, CSVWriter, JSONWriter


def calc_k0_k1(f_lm, f_ch0_data, f_ch1_data, i_lm, i_ch0_data, i_ch1_data):
    k0 = ((f_lm * i_ch1_data - i_lm * f_ch1_data) / 
          (f_ch0_data * i_ch1_data - i_ch0_data * f_ch1_data))
    k1 = (k0 * i_ch0_data - i_lm) / i_ch1_data
    return k0, k1

def calc_dgf_coef_b(atime_ms, againx, k0, k1):
    dgf = (atime_ms * againx) * k0
    b = k1 / k0
    return dgf, b

def lux_equation_first_order(c0_data, c1_data, atime_ms, againx, dgf, b):
    cpl = (atime_ms * againx) / dgf
    return (1 / cpl) * c0_data - ((b / cpl) * c1_data)



class TSL2591:
    def __init__(self, i2c_bus, bus_addr=0x29, output='csv', sensor_id='TSL2591'):
        """Initialize worker device on i2c bus.

        Parameters
        ----------
        bus_n : int, i2c bus number on Controller
        bus_addr : int, i2c bus number of this Worker device
        output : str, output data format, either 'csv' (default) or 'json'
        """

        # i2c bus
        self.bus = i2c_bus
        self.bus.bus_addr = bus_addr

        # enable register (0x00)
        self._enable = 0x00
        self.npien   = 0
        self.sai     = 0
        self.aien    = 0
        self.aen     = 0
        self.pon     = 0

        # control register (0x01)
        self._control     = 0x00
        self.system_reset = 0
        self.a_gain       = 0
        self.a_time       = 0

        # status register (0x13)
        self._status = 0x00
        self.npintr = 0
        self.aint   = 0
        self.avalid = 0

        self._command_byte = 0x00

        # 1st order lux coefficients
        self.k0  = None
        self.k1  = None
        self.dgf = None
        self.b   = None

        # information about this device
        self.metadata = Meta(name=name)
        self.metadata.description = 'Dual channel 16bit photodiode light-to-digital converter'
        self.metadata.urls = 'https://ams.com/tsl25911'
        self.metadata.manufacturer = 'AMS (formerly TAOS)'
        
        self.metadata.header    = ['system_id', 'sensor_id', "description", "sample_n", "ch0",   "ch1",   "lux"]
        self.metadata.dtype     = ['str',       'str',       "",            "int",      "int",   "int",   "float"]
        self.metadata.units     = ['NA',        'NA',        None,          "count",    "count", "count", "lux"]
        self.metadata.accuracy  = ['NA',        'NA',        None,          1,          "",      "",      ""] 
        self.metadata.precision = ['NA',        'NA',        None,          1,          "",      "",      ""]
        
        self.metadata.bus_addr = hex(bus_addr)

        # python strftime specification for RTC output precision
        self.metadata.rtc_time_source = '%Y-%m-%d %H:%M:%S'

        # data recording information
        self.system_id = None
        self.sensor_id = sensor_id
        
        # data recording method
        # note: using millisecond accuracy on driver timestamp, even though
        # RTC is only 1 second resolution
        self.writer_output = output
        self.csv_writer  = CSVWriter( metadata=self.metadata, time_source='local')
        self.json_writer = JSONWriter(metadata=self.metadata, time_source='local')

    def command(self, reg_addr):
        """Set the Command control-status-data register for subsequent 
        read and write transactions. Writes CMD bit 7 as 0b1 and 
        TRANSACTION bits 6:5 as 0b01 for Normal Operation.

        Parameters
        ----------
        reg_addr : 5 bit integer, register to read or write
        """
        return  0b10100000 | reg_addr

    def command_special(self, special_function):
        """Set the Command register special function fields. Refer to datasheet
        for details. Options are:
            interrupt: forces an interrupt
            clear_als: clears ALS interrupt
            clear_als_no_persist: clears ALS and no persist ALS interrupt
            no_persist: clears no persist ALS interrupt


        Parameters
        ----------
        special_function : str, one of 
            'interrupt', 
            'clear_als', 
            'clear_als_no_persist', 
            'no_persist'
        """
        _addr_sf_mapper = {'interrupt': 0b00100, 'clear_als': 0b00110,
                           'clear_als_no_persist': 0b00111,
                           'no_persist': 0b01010}
        return 0b11100000 | _addr_sf_mapper[special_function]

    def read_register(self, reg_addr):
        """Read a 8bit register on the TSL2591"""
        self._command_byte = self.command(reg_addr)
        return self.bus.read_register_8bit(reg_addr=self._command_byte)

    def write_register(self, reg_addr, data):
        """Write a 8bit register on the TSL2591"""
        self._command_byte = self.command(reg_addr)
        self.bus.write_register_8bit(reg_addr=self._command_byte, data=data)

    # 0x00
    def enable_read(self):
        """Read enable register, power device on/off, enable functions and iterrupts
        """
        self._enable = self.read_register(0x00)
        self.npien =  self._enable >> 7
        self.sai   = (self._enable >> 6) & 0b1
        self.aien  = (self._enable >> 4) & 0b1
        self.aen   = (self._enable >> 1) & 0b1
        self.pon   =  self._enable & 0b1

    def enable_write(self):
        """Set the Enable register attributes"""

        self._enable = ((self.npien << 7) + 
                        (self.sai << 6) + 
                        (self.aien << 4) + 
                        (self.aen << 1) + 
                        (self.pon))
        self.write_register(reg_addr=0x00, data=self._enable)
        
    # 0x01
    def control_read(self):
        self._control = self.read_register(0x01)
        self.system_reset =  self._control >> 7
        self.a_gain       = (self._control >> 4) & 0b11
        self.a_time       =  self._control & 0b111

    def control_write(self):
        self._control = ((self.system_reset << 7) + 
                         (self.a_gain << 4) + 
                         (self.a_time))
        self.write_register(reg_addr=0x01, data=self._control)
        
    def set_atime(self, t):
        assert t in [100, 200, 300, 400, 500, 600], 'Not a valid integration time'
        _t_mapper = {100: 0b00, 200: 0b001, 300: 0b010, 
                     400: 0b011, 500: 0b100, 600: 0b101}
        self.a_time = _t_mapper[t]

    def set_again(self, g):
        """Set the ALS gain of the internal integration amplifiers
        for both photodiode channels

        Parameters
        ----------
        g : str, one of: 'low', 'med', 'high', 'max'
        """
        assert g in ['low', 'med', 'high', 'max'], 'Not a valid gain'
        _g_mapper = {'low': 0b00, 'med': 0b01, 'high': 0b10, 'max': 0b11}
        self.a_gain = _g_mapper[g]

    def id(self):
        return self.read_register(0x12)
        
    def status(self):
        self._status = self.read_register(0x13)
        self.npintr = (self._status >> 5) & 0b1
        self.aint   = (self._status >> 4) & 0b1
        self.avalid =  self._status & 0b1

    def als(self):
        """Read  ALS data.
        From the datasheet:
        ALS data is stored as two 16-bit values; one for each channel.
        When the lower byte of either channel is read, the upper byte
        of the same channel is latched into a shadow register.
        
        ...to minimize the potential for skew between CH0
        and CH1 data, it is recommended to read all four ADC bytes in
        sequence.
        

        Returns
        -------
        ch0 : int, 16 bit als data
        ch1 : int, 16 bit als data
        """     
        ch0 = (self.read_register(0x15) << 8) + self.read_register(0x14)
        ch1 = (self.read_register(0x17) << 8) + self.read_register(0x16)
        return ch0, ch1

    def publish(self, description='NA', n=1, delay=None):
            """Get measured air partical data and output in JSON,
            plus metadata at intervals set by self.metadata_interval

            Parameters
            ----------
            description : str, description of data collected
            n : int, number of samples to record in this burst
            delay : float, seconds to delay between samples if n > 1. This is
                in addition to any blocking settle time set.

            Returns
            -------
            str, formatted in JSON with keys:
                description : str
                n : sample number in this burst
                and values as described in self.metadata.header
            """

            data_list = []
            for m in range(n):

                ch0, ch1 = self.als()
                if self.b is not None:
                    _g_mapper = {0b00:1, 0b01:25, 0b10:400, 0b11:9600}
                    a_gain_x = _g_mapper[self.a_gain]
                    _t_mapper = {0b00: 100, 0b001: 200, 0b010: 300, 
                                 0b011: 400, 0b100: 500, 0b101: 600}
                    a_time_x = _t_mapper[self.a_time]
                    lux = lux_equation_first_order(ch0, ch1, a_time_x, a_gain_x, self.dgf, self.b)
                else:
                    lux = None
                _data = self.json_writer.publish([self.system_id, self.sensor_id, description, m] + list(self.als()) + [lux])
                data_list.append(_data)
                if n == 1:
                    return data_list[0]
                if delay is not None:
                    time.sleep(delay)
            return data_list

    def write(self, description='NA', n=1, delay=None):
        """Get measured air partical data and save to file,
        formatted as either CSV with extension .csv or
        JSON and extension .jsontxt.

        Parameters
        ----------
        description : str, description of data collected
        n : int, number of samples to record in this burst
        delay : float, seconds to delay between samples if n > 1. This is
            in addition to any blocking settle time set.

        Returns
        -------
        None, writes to disk the following data:
            description : str
            n : sample number in this burst
            and values as described in self.metadata.header
        """

        wr = {"csv": self.csv_writer,
              "json": self.json_writer}[self.writer_output]
        for m in range(n):
            wr.write([self.system_id, self.sensor_id, description, m] + get())
            if delay is not None:
                time.sleep(delay)
