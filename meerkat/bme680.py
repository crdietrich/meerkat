"""Bosch BME680 Gas Sensor Driver for Raspberry PI & MicroPython

Manufacturer Information
https://www.bosch-sensortec.com/products/environmental-sensors/gas-sensors-bme680/
https://github.com/BoschSensortec/BME680_driver

Breakout Board and CircuitPython Driver this work derives from
https://www.adafruit.com/product/3660
https://github.com/adafruit/Adafruit_CircuitPython_BME680

"""
try:
    import struct
except ImportError:
    import ustruct as struct


from meerkat.base import I2C, DeviceData, time
from meerkat.data import CSVWriter, JSONWriter


def _read24(arr):
    """Parse an unsigned 24-bit value as a floating point and return it."""
    ret = 0.0
    for b in arr:
        ret *= 256.0
        ret += float(b & 0xFF)
    return ret


class BME680:
    def __init__(self, bus_n, bus_addr=0x77, output='csv'):
        """Initialize worker device on i2c bus.

        For register memory map, see datasheet pg 28, section 5.2

        Parameters
        ----------
        bus_n : int, i2c bus number on Controller
        bus_addr : int, i2c bus number of this Worker device
        """

        # i2c bus
        self.bus = I2C(bus_n=bus_n, bus_addr=bus_addr)
        
        # information about this device
        self.device = DeviceData('BME680')
        self.device.description = 'Bosch Humidity, Pressure, Temperature, VOC Sensor'
        self.device.urls = 'https://www.bosch-sensortec.com/products/environmental-sensors/gas-sensors-bme680/'
        self.device.active = None
        self.device.error = None
        self.device.bus = repr(self.bus)
        self.device.manufacturer = 'Bosch Sensortec'
        self.device.version_hw = '1.0'
        self.device.version_sw = '1.0'
        self.device.accuracy = None
        self.device.precision = 'VOC:0.08%, RH:0.01%, P:0.02Pa, T:1.0C'
        self.device.calibration_date = None

        # Default oversampling and filter register values.
        self.refresh_rate        = 1
        self.filter              = 1

        # memory mapped from 8 bit register locations
        self.mode     = 0b00   # 2 bits, ctrl_meas <1:0> operation mode
        self.osrs_p   = 0b001  # 3 bits, ctrl_meas <4:2>, oversample pressure
        self.osrs_t   = 0b001  # 3 bits, ctrl_meas <2:0>, oversample temperature
        self.osrs_h   = 0b001  # 3 bits, ctrl_hum <2:0>, oversample humidity
        self.run_gas  = 0b0    # 1 bit, ctrl_gas_1 <4>, run gas measurement
        self.nb_conv  = 0b000  # 4 bits, ctrl_gas_1 <3:0> conversion profile number
        self.heat_off = 0b0    # 1 bit, ctrl_gas_0 <3>, gas heater on/off

        # profile registers
        self.gas_wait_x  = None  # gas_wait registers 9-0
        self.res_heat_x  = None  # res_heat registers 9-0
        self.idac_heat_x = None  # idac_heat registers 9-0

        # meas_status_0 register
        self.gas_meas_index = None
        self._new_data = None
        self._gas_measuring = None
        self._measuring = None

        # calibration registers
        self._temp_calibration = None
        self._pressure_calibration = None
        self._humidity_calibration = None
        self._gas_calibration = None
        self._heat_range = None
        self._heat_val = None
        self.range_switch_error = None

        # raw ADC values
        self._adc_pres = None
        self._adc_temp = None
        self._adc_hum = None
        self._adc_gas = None
        self.adc_gas2 = None
        self._gas_range = None
        self._t_fine = None

        # control registers
        self._r_ctrl_meas = None
        self._r_ctrl_gas_1 = None
        
        # the datasheet gives two options: float or int values and equations
        # this code uses integer calculations, see table 16
        self._const_array1_int = (2147483647, 2147483647,
                                  2147483647, 2147483647,
                                  2147483647, 2126008810,
                                  2147483647, 2130303777,
                                  2147483647, 2147483647,
                                  2143188679, 2136746228,
                                  2147483647, 2126008810,
                                  2147483647, 2147483647)
        self._const_array2_int = (4096000000, 2048000000,
                                  1024000000, 512000000,
                                  255744255, 127110228,
                                  64000000, 32258064,
                                  16016016, 8000000,
                                  4000000, 2000000,
                                  1000000, 500000,
                                  250000, 125000)

        # data recording method
        self.writer_output = output
        self.csv_writer = CSVWriter("BME680", time_format='std_time_ms')
        self.csv_writer.device = self.device.__dict__
        self.csv_writer.header = ['description', 'sample_n', 'VOC', 'RH', 'P', 'T']
        self.json_writer = JSONWriter("BME680", time_format='std_time_ms')
        self.json_writer.device = self.device.__dict__
        self.json_writer.header = self.csv_writer.header

        # data recording information
        self.sample_id = None

        # Pressure in hectoPascals at sea level, used to calibrate altitude
        self.sea_level_pressure = 1013.25

        # sample collection metadata
        self._last_reading = 0
        self._min_refresh_time = 1 / self.refresh_rate

        # calculated ambient temperature for res_heat target calculation
        self.amb_temp = None

    def read(self, n):
        """Read n bytes from the device"""
        return self.bus.read_n_bytes(n=n)
    
    def write(self, reg, values):
        """Write values to register
        """
        if not isinstance(values, list):
            values = [values]
        self.bus.write_n_bytes([reg] + values)
        
    # ## Register Methods
    # In the order listed in Table 20: Memory Map, pg28
    
    def reset(self):
        """Reset the device using a soft-reset procedure, which has the 
        same effect as a power-on reset, by writing register
        'reset' at 0xE0 with value 0xB6.  Default value is 0x00."""
        self.bus.write_n_bytes([0xE0, 0xB6])
        time.sleep(0.005)
        
    def read_r_chip_id(self):
        """Check that the chip ID is correct.  Should return 0x61"""
        _chip_id = self.bus.read_register_8bit(0xD0)
        if _chip_id != 0x61:
            raise OSError('Expected BME680 ID 0x%x, got ID: 0x%x' % (0x61, _chip_id))
        
    def read_r_config(self):
        """Read register 'config' at 0x75 which contains the 
        'filter' contorl register.  'spi_3w_en' is always 
        0b0 in I2C mode"""
        _config = self.bus.read_register_8bit(0x75)
        self.filter = (_config >> 2) & 0b111  # mask to be sure
        
    def read_r_ctrl_meas(self):
        """Read register 'ctrl_meas' at 0x74 which contains the
        'mode', 'osrs_p' and 'osrs_t' control registers"""
        _ctrl_meas = self.bus.read_register_8bit(0x74)
        self.mode = _ctrl_meas & 0b11
        self.osrs_p = (_ctrl_meas >> 2) & 0b111
        self.osrs_t = _ctrl_meas >> 5
        
    def write_r_ctrl_meas(self):
        """Write register 'ctrl_meas' at 0x74 which contains the 
        'mode', 'osrs_p' and 'osrs_t' control registers"""
        _ctrl_meas = (((self.osrs_t << 5) |
                       (self.osrs_p << 2)) |
                        self.mode)
        self.bus.write_n_bytes([0x74, _ctrl_meas])
        
    def read_r_ctrl_hum(self):
        """Read register 'ctrl_hum' at 0x72 which contains the 
        'osrs_h' control register.  'spi_3w_int_en' is always 
        0b0 in I2C mode"""
        _ctrl_hum = self.bus.read_register_8bit(0x72)
        self.osrs_h = _ctrl_hum & 0b111  # mask just to be sure
        
    def write_r_ctrl_hum(self):
        """Write register 'ctrl_hum' at 0x72 which contains the 
        'osrs_h' control register.  'spi_3w_int_en' is always 
        0b0 in I2C mode"""
        self.bus.write_n_bytes([0x72, self.osrs_h])
        
    def reg_ctrl_gas_1(self):
        """Contains 'run_gas' and 'nb_conv' control registers"""
        _ctrl_gas_1 = self.bus.read_register_8bit(0x71)
        self.run_gas = (_ctrl_gas_1 >> 4) & 0b1
        self.nb_conv = _ctrl_gas_1 & 0b1111
        
    def reg_ctrl_gas_0(self):
        """Contains the 'heat_off' control register"""
        _ctrl_gas_0 = self.bus.read_register_8bit(0x70)
        self.heat_off = (_ctrl_gas_0 >> 3) & 0b1
        
    def reg_gas_wait_x(self):
        """Control register for gas wait profiles"""
        self.gas_wait_x = self.bus.read_n_bytes(0x64, 10)
        
    def reg_res_heat_x(self):
        """Control register for heater resistance profiles"""
        self.res_heat_x = self.bus.read_n_bytes(0x5A, 10)
        
    def reg_idac_heat_x(self):
        """Control register for heater current profiles"""
        self.idac_heat_x = self.bus.read_n_bytes(0x50, 10)
        
    def mode_sleep(self):
        """Set chip mode to Sleep Mode"""
        self.bus.write_n_bytes([])
        
    def mode_forced(self):
        """Set chip mode to Forced Mode (active for measurement)"""
        self.bus.write_n_bytes([])

    def read_calibration(self):
        """Read & save the calibration coefficients

        Coefficients are not listed in memory map, table 20.  Instead they are
        referenced in Tables 11, 12, 13 and 14
        """
        coeff  = self.bus.read_register_nbit(0x89, 25)
        coeff += self.bus.read_register_nbit(0xE1, 16)

        coeff = list(struct.unpack('<hbBHhbBhhbbHhhBBBHbbbBbHhbb', bytes(coeff[1:39])))
        coeff = [float(i) for i in coeff]
        
        # 3 bytes
        self._temp_calibration = [coeff[x] for x in [23, 0, 1]]
        # 10 bytes
        self._pressure_calibration = [coeff[x] for x in [3, 4, 5, 7, 8, 10, 9, 12, 13, 14]]
        # 7 bytes
        self._humidity_calibration = [coeff[x] for x in [17, 16, 18, 19, 20, 21, 22]]
        # 3 bytes
        self._gas_calibration = [coeff[x] for x in [25, 24, 26]]

        # current method = 39 byte read + 3 byte setup 
        
        # flip around H1 & H2
        self._humidity_calibration[1] *= 16
        self._humidity_calibration[1] += self._humidity_calibration[0] % 16
        self._humidity_calibration[0] /= 16
    
    # Operation Methods

    def set_filter(self, coeff):
        """Set the temperature and pressure IIR filter
        
        Parameters
        ----------
        coeff : int, filter coefficient.  Valid values are:
            0, 1, 3, 7, 15, 31, 63, 127
        """
        mapper = {0:  0b000,  1: 0b001,  3: 0b010,   7: 0b011,
                  15: 0b100, 31: 0b101, 63: 0b110, 127: 0b111}
        self.filter = coeff
        _filter = mapper[self.filter]
        self.bus.write_n_bytes([0x75, _filter << 2])  # config register
            
    def set_oversampling(self, h, t, p):
        """Set oversample rate for temperature, pressures and
        humidity.  Valid values for all three are:
            0, 1, 2, 4, 8, 16
            Note: 0 will skip measurement
        
        Parameters
        ----------
        h : int, oversampling rate of humidity
        t : int, oversampling rate of temperature
        p : int, oversampling rate of pressure
        """
        
        htp_mapper = {0: 0b000, 1: 0b001, 2: 0b010,
                      4: 0b011, 8: 0b100, 16: 0b101}
        
        # ctrl_hum register, 0x72
        self.osrs_h = htp_mapper[h]
        self.write_r_ctrl_hum()
        
        # ctrl_meas register, 0x74
        self.osrs_t = htp_mapper[t]
        self.osrs_p = htp_mapper[p]
        self.write_r_ctrl_meas()

    def set_x_register(self, reg_0, n, value):
        """Set register within one of the three 10 byte registers:
            Gas_wait_x  : gas_wait_9  @ 0x6D downto  gas_wait_0 @ 0x64
            Res_heat_x  : res_heat_0  @ 0x63 downto  res_heat_0 @ 0x5A
            Idac_heat_x : idac_heat_9 @ 0x59 downto idac_heat_0 @ 0x50
        See Table 20 Memory Map for details.
        
        Parameters
        ----------
        n : int, set the nth register within the register block
        reg_0 : int, 0th register of the register block
        value : int, value for register
        """
        self.bus.write_register_8bit(n + reg_0, value)
        
    def set_gas_wait(self, n, value):
        """Set gas wait time for Gas_wait_x registers.
        Registers range from 0 = 0x64 up to 9 = 0x6D
        
        Parameters
        ----------
        n : int, set the nth register within the register block
        value : int, value for register
        """
        self.set_x_register(reg_0=0x64, n=n, value=value)
    
    def set_res_heat(self, n, value):
        """Set resistance for the heater registers.
        Registers range from 0 = 0x64 up to 9 = 0x6D
        
        Parameters
        ----------
        n : int, set the nth register within the register block
        value : int, value for register
        """
        self.set_x_register(reg_0=0x64, n=n, value=value)
    
    def get_gas_wait(self):
        """Gas_wait_x  : gas_wait_9  @ 0x6D downto  gas_wait_0 @ 0x64
        
        Returns
        -------
        bytes : 10 bytes from register range reg_0 to reg_0 + 10"""
        return self.bus.read_register_nbit(0x64, 10)
    
    def get_res_heat(self):
        """Res_heat_x  : res_heat_0  @ 0x63 downto  res_heat_0 @ 0x5A
        
        Returns
        -------
        bytes : 10 bytes from register range reg_0 to reg_0 + 10"""
        return self.bus.read_register_nbit(0x5A, 10)
    
    def get_idac_heat(self):
        """Idac_heat_x : idac_heat_9 @ 0x59 downto idac_heat_0 @ 0x50
        
        Returns
        -------
        bytes : 10 bytes from register range reg_0 to reg_0 + 10"""
        return self.bus.read_register_nbit(0x50, 10)
            
    def calc_res_heat(self, target_temp):
        """Convert a target temperature for the heater to a resistance
        target for the chip
        
        Parameters
        ----------
        target_temp : int, target temperature in degrees Celcius
        
        Returns
        -------
        res_heat : int, register code for target temperature
        """
        
        if self.amb_temp is None:
            self.measure_tph()
            self.amb_temp = self.temperature()
        
        amb_temp = int(self.amb_temp)
        
        par_g1     = self.bus.read_register_8bit(0xED)
        par_g2_lsb = self.bus.read_register_8bit(0xEB)
        par_g2_msb = self.bus.read_register_8bit(0xEC)
        par_g2     = (par_g2_msb << 8) + par_g2_lsb
        par_g3     = self.bus.read_register_8bit(0xEE)
        
        res_heat_range = self.bus.read_register_8bit(0x02)
        res_heat_range = (res_heat_range >> 4) & 0b11
        res_heat_val   = self.bus.read_register_8bit(0x00)
        
        var1 = ((amb_temp * par_g3) // 10) << 8
        var2 = (
            (par_g1 + 784) * 
            (((((par_g2 + 154009) * int(target_temp) * 5) // 100) + 3276800) // 10)
            )
        var3 = var1 + (var2 >> 1)
        var4 = var3 // (res_heat_range + 4)
        var5 = (131 * res_heat_val) + 65536
        res_heat_x100 = int(((var4 // var5) - 250) * 34)
        res_heat_x = int((res_heat_x100 + 50) // 100)
        
        return res_heat_x
    
    def calc_wait_time(self, t, x):
        """Calculate the wait time code for a heating profile

        Parameters
        ----------
        t : int, valued 0-63 with 1 ms step sizes, 0 = no wait
        x : int, multiplier for x, one of 1, 4, 16, 64

        Returns
        -------
        byte : register value
        """
        assert t < 63
        mapper = {1: 0b00, 4: 0b01, 16: 0b10, 64: 0b11}
        x = mapper[x]
        return (x << 6) | t

    def setup_gas(self, t_ms, x, t_c, verbose=False):
        """Enable gas measurement
        See pg 15 for example quickstart sequence
        
        Note: sets nb_conv = number of conversions to index 0
        
        Parameters
        ----------
        t_ms : int, number of milliseconds to heat the gas sensor, 0-63
        x : int, multiplier for t_ms, 1, 4, 16, 64 are valid
        t_c : int, target temperature in degrees C
        verbose : bool, print debug statements
        """
        
        #TODO: break this apart into register functions
        self.range_switch_error = self.bus.read_register_8bit(0x04)
        
        wait_time = self.calc_wait_time(t=t_ms, x=x)
        
        if verbose:
            print("Wait code:", wait_time)
        
        # write gas_wait_x register 0
        #self.bus.write_register_8bit(0x64, wait_time)
        self.set_gas_wait(n=0, value=wait_time)
        
        resistance = self.calc_res_heat(target_temp=t_c)
        
        if verbose:
            print("Resistance code:", resistance)
        
        # write res_heat register 0
        #self.bus.write_register_8bit(0x5A, resistance)
        self.set_res_heat(n=0, value=resistance)
        
        # gas measurements enabled with 0b1 at <4>
        # nb_conv selects register 0 with 0b0000 at <3:0> 
        reg_ctrl_gas_1 = self.nb_conv | 0b10000
        self.bus.write_n_bytes([0x71, reg_ctrl_gas_1])
        
        # read current ctrl_meas register
        # (which contains osrs_t and osrs_p)
        # and initiate single shot mode at 1:0
        #r_ctrl_meas = self.bus.read_register_8bit(0x74)
        #r_ctrl_meas = (r_ctrl_meas & 0xFC) | 0x01
        #self.bus.write_n_bytes([0x74, r_ctrl_meas])
        
    def get_measurement_status(self):
        reg_meas_status = self.bus.read_register_8bit(0x1D)
        self.gas_meas_index = reg_meas_status & 0b111
        self._new_data = reg_meas_status >> 7
        self._gas_measuring = (reg_meas_status >> 6) & 0b1
        self._measuring = (reg_meas_status >> 5) & 0b1
        
    def get_reading(self):
        # self.setup_gas(t_ms=40, x=4, t_C=150)
        self._new_data = 0
        self.get_measurement_status()
        
        t0 = time.time()
        while self._new_data == 0:
            if (time.time() - t0) > 20:
                break
            else:
                time.sleep(0.005)
            self.get_measurement_status()
        
        # 0x1F to 0x2B
        return self.bus.read_n_bytes(0x1F, 14)
        
    def measure_tph(self):
        """Get the temperature, pressure and humidity"""
        data = self.get_reading()
        self._adc_temp = _read24(data[4:7]) / 16  # _read24(data[4:7]) / 16
        self._adc_pres = _read24(data[1:4]) / 16  # _read24(data[1:4]) / 16
        self._adc_hum = struct.unpack('>H', bytes(data[7:9]))[0]
        
        self._adc_gas = int(struct.unpack('>H', bytes(data[12:14]))[0] / 64)
        g2 = self.bus.read_register_16bit(0x2B)
        self.adc_gas2 = g2 >> 6
        self._gas_range = data[13] & 0x0F  # 0x2B <4:0>
        
    def gas(self):
        """Calculate the gas resistance in ohms"""
        # self._perform_reading()
        # print(self.range_switch_error, type(self.range_switch_error))
        var1 = ((1340 + (5 * self.range_switch_error)) * 
                (self._const_array1_int[self._gas_range])) >> 16
        
        # var2 = ((self._adc_gas << 15) - 16777216) + var1  # 1 << 24 = 16777216
        var2 = ((self.adc_gas2 << 15) - 16777216) + var1  # 1 << 24 = 16777216
        
        gas_res = (((self._const_array2_int[self._gas_range] * var1) >> 9) +
                   (var2 >> 1)) / var2
        # calc_gas_res = (var3 + (var2 / 2)) / var2
        # print("gas() var1, var2:", var1, var2) #, var3)
        return gas_res, self._adc_gas, self.adc_gas2, var1, var2
        
    def temperature(self):
        """Calculate the compensated temperature in degrees celsius"""
        var1 = (self._adc_temp / 8) - (self._temp_calibration[0] * 2)
        var2 = (var1 * self._temp_calibration[1]) / 2048
        var3 = ((var1 / 2) * (var1 / 2)) / 4096
        var3 = (var3 * self._temp_calibration[2] * 16) / 16384
        self._t_fine = int(var2 + var3)
        calc_temp = (((self._t_fine * 5) + 128) / 256) / 100       
        return calc_temp
        
    def pressure(self):
        """Calculate the barometric pressure in hectoPascals"""
        var1 = (self._t_fine / 2) - 64000
        var2 = ((var1 / 4) * (var1 / 4)) / 2048
        var2 = (var2 * self._pressure_calibration[5]) / 4
        var2 = var2 + (var1 * self._pressure_calibration[4] * 2)
        var2 = (var2 / 4) + (self._pressure_calibration[3] * 65536)
        var1 = (((((var1 / 4) * (var1 / 4)) / 8192) *
                 (self._pressure_calibration[2] * 32) / 8) +
                ((self._pressure_calibration[1] * var1) / 2))
        var1 = var1 / 262144
        var1 = ((32768 + var1) * self._pressure_calibration[0]) / 32768
        calc_pres = 1048576 - self._adc_pres
        calc_pres = (calc_pres - (var2 / 4096)) * 3125
        calc_pres = (calc_pres / var1) * 2
        var1 = (self._pressure_calibration[8] * (((calc_pres / 8) * (calc_pres / 8)) / 8192)) / 4096
        var2 = ((calc_pres / 4) * self._pressure_calibration[7]) / 8192
        var3 = (((calc_pres / 256) ** 3) * self._pressure_calibration[9]) / 131072
        calc_pres += ((var1 + var2 + var3 + (self._pressure_calibration[6] * 128)) / 16)
        calc_pres = calc_pres / 100
        return calc_pres
        
    def humidity(self):
        """The relative humidity in RH %"""
        temp_scaled = ((self._t_fine * 5) + 128) / 256
        var1 = ((self._adc_hum - (self._humidity_calibration[0] * 16)) -
                ((temp_scaled * self._humidity_calibration[2]) / 200))
        var2 = (self._humidity_calibration[1] *
                (((temp_scaled * self._humidity_calibration[3]) / 100) +
                 (((temp_scaled * ((temp_scaled * self._humidity_calibration[4]) / 100)) /
                   64) / 100) + 16384)) / 1024
        var3 = var1 * var2
        var4 = self._humidity_calibration[5] * 128
        var4 = (var4 + ((temp_scaled * self._humidity_calibration[6]) / 100)) / 16
        var5 = ((var3 / 16384) * (var3 / 16384)) / 1024
        var6 = (var4 * var5) / 2
        calc_hum = (((var3 + var6) / 1024) * 1000) / 4096
        calc_hum /= 1000  # get back to RH

        if calc_hum > 100:
            calc_hum = 100
        if calc_hum < 0:
            calc_hum = 0
        return calc_hum
        
    def debug_read_registers(self):
        """Print out the values of read only registers"""
        from meerkat import tools
        x = self.get_reading()
        reg = [0x1D, 0x1F, 0x20, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x2A, 0x2B]
        print("="*20)
        for n, b in enumerate(x):
            n = n + 0x1D
            print("REG: {}".format(hex(n)))
            if n in reg:
                tools.bprint(int(b), n=8)
            else:
                print("Not Used")
            print("="*20)
