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


# Memory Map, see datasheet pg 28, section 5.2
chip_id          = 0x61

#REG_chip_id      = 0xD0
COEFF_ADDR1     = 0x89
COEFF_ADDR2     = 0xE1


REG_SOFTRESET   = 0xE0
REG_CTRL_GAS    = 0x71
#REG_CTRL_HUM    = 0x72
REG_STATUS      = 0x73
#REG_CTRL_MEAS   = 0x74
REG_CONFIG      = 0x75

REG_STATUS        = 0x73

REG_RESET         = 0xE0

#REG_ID            = 0xD0
REG_CONFIG        = 0x75

REG_CTRL_MEAS     = 0x74
#REG_CTRL_HUM      = 0x72

REG_CTRL_GAS_1    = 0x71
REG_CTRL_GAS_0    = 0x70

# REG_GAS_WAIT_X  = 0x6D...0x64
REG_GAS_WAIT_0    = 0x64

# REG_RES_HEAT_X  = 0x63...0x5A
REG_RES_HEAT_0    = 0x5A

# REG_IDAC_HEAT_X = 0x59...0x50
REG_IDAC_HEAD_0   = 0x50

REG_PDATA         = 0x1F
REG_TDATA         = 0x22
REG_HDATA         = 0x25


REG_GAS_R_LSB     = 0x2B
REG_GAS_R_MSB     = 0x2A

REG_HUM_LSB       = 0x26
REG_HUM_MSB       = 0x25

REG_TEMP_xLSB     = 0x24
REG_TEMP_LSB      = 0x23
REG_TEMP_MSB      = 0x22

REG_PRESS_xLSB    = 0x21
REG_PRESS_LSB     = 0x20
REG_PRESS_MSB     = 0x1F

REG_MEAS_STATUS   = 0x1D

SAMPLERATES       = (0, 1, 2, 4, 8, 16)
FILTERSIZES       = (0, 1, 3, 7, 15, 31, 63, 127)

RUNGAS          = 0x10

# these appear to be the integer const_array1_int values
_LOOKUP_TABLE_1            = (2147483647.0, 2147483647.0, 
                              2147483647.0, 2147483647.0, 
                              2147483647.0, 2126008810.0,
                              2147483647.0, 2130303777.0, 
                              2147483647.0, 2147483647.0,
                              2143188679.0, 2136746228.0, 
                              2147483647.0, 2126008810.0, 
                              2147483647.0, 2147483647.0)

_LOOKUP_TABLE_2             = (4096000000.0, 2048000000.0, 
                               1024000000.0, 512000000.0, 
                               255744255.0, 127110228.0, 
                               64000000.0, 32258064.0, 
                               16016016.0, 8000000.0, 
                               4000000.0, 2000000.0, 
                               1000000.0, 500000.0, 
                               250000.0, 125000.0)

def _read24(arr):
    """Parse an unsigned 24-bit value as a floating point and return it."""
    ret = 0.0
    #print([hex(i) for i in arr])
    for b in arr:
        ret *= 256.0
        ret += float(b & 0xFF)
    return ret


class BME680:
    def __init__(self, bus_n, bus_addr=0x77, output='csv'):
        """Initialize worker device on i2c bus.

        Parameters
        ----------
        bus_n : int, i2c bus number on Controller
        bus_addr : int, i2c bus number of this Worker device
        """

        # i2c bus
        self.bus = I2C(bus_n=bus_n, bus_addr=bus_addr)
        
        # information about this device
        self.device = DeviceData('BME680')
        self.device.description = ('Bosch Humidity, Pressure, Temperature, VOC Sensor')
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
        self.humidity_oversample = 1
        self.pressure_oversample = 1
        self.temp_oversample     = 1

        self.nb_conv = 0b000
        
        self._temp_calibration = None
        self._pressure_calibration = None
        self._humidity_calibration = None
        self._gas_calibration = None

        self._heat_range = None
        self._heat_val = None
        self._sw_err = None
        
        self._adc_pres = None
        self._adc_temp = None
        self._adc_hum = None
        self._adc_gas = None
        self._gas_range = None
        self._t_fine = None

        self._last_reading = 0
        self._min_refresh_time = 1 / self.refresh_rate
        
        # data recording information
        self.sample_id = None
        
        # data recording method
        self.writer_output = output
        self.csv_writer = CSVWriter("BME680", time_format='std_time_ms')
        self.csv_writer.device = self.device.__dict__
        self.csv_writer.header = ['description', 'sample_n', 'VOC', 'RH', 'P', 'T']
        
        self.json_writer = JSONWriter("BME680", time_format='std_time_ms')
        self.json_writer.device = self.device.__dict__
        self.json_writer.header = self.csv_writer.header
        
        # setup chip state
        
        #self.soft_reset()
        #time.sleep(1)
        #self.check_id()
        #time.sleep(0.5)
        #self.read_calibration()
        
        # set up heater
        #self.bus.write_n_bytes([REG_RES_HEAT_0, 0x73])
        #self.bus.write_n_bytes([REG_GAS_WAIT_0, 0x65])
        
        # Pressure in hectoPascals at sea level, used to calibrate altitude
        self.sea_level_pressure = 1013.25
        
    def read(self, n):
        """Read n bytes from the device"""
        return self.bus.read_n_bytes(n=n)
    
    def write(self, reg, values):
        """Write values to register
        """
        if not isinstance(values, list):
            values = [values]
        self.bus.write_n_bytes([reg] + values)
        
    # register functions are in the order listed in Table 20: Memory Map, pg28
    
    def reg_soft_reset(self):
        """Reset the device using a soft-reset procedure, which has the 
        same effect as a power-on reset.  
        Note: The reset register is 0xE0 with default value 0x00"""
        self.bus.write_n_bytes([0xE0, 0xB6])
        time.sleep(0.005)
        
    def reg_check_id(self):
        """Check that the chip ID is correct.  Should return 0x61"""
        chip_id = self.bus.read_register_8bit(0xD0)
        if _chip_id != 0x61:
            raise OSError('Expected BME680 ID 0x%x, got ID: 0x%x' % (chip_id, _chip_id))
        
    def reg_config(self):
        """'config' contains the 'filter' and 'spi_3w_en' control registers"""
        _config = self.bus.read_regsiter_8bit(0x75)
        self.filter = (_config >> 2) & 0b111
        
    def reg_ctrl_meas(self):
        """'ctrl_meas' contains the 'mode', 'osrs_p' and 'osrs_t' control registers"""
        _ctrl_meas = self.bus.read_register_8bit(0x74)
        self.mode = _ctrl_meas & 0b11
        self.osrs_p = (_ctrl_meas >> 2) & 0b111
        self.osrs_t = _ctrl_meas >> 5
        
    def reg_ctrl_hum(self):
        """'ctrl_hum contains the 'spi_3w_int_en' and 'osrs_h' control registers"""
        ctrl_hum = self.bus.read_register_8bit(0x72)
        
    def reg_ctrl_gas_1(self):
        """Contains 'run_gas' and 'nb_conv' control registers"""
        _ctrl_gas_1 = self.bus.read_register_8bit(0x71)
        self.run_gas = (_ctrl_gas_1 >> 4) & 0b1
        self.nb_conv = _ctrl_gas_1 & 0b1111
        
    def reg_ctrl_gas_0(self):
        """Contains the 'heat_off' control register"""
        _ctrl_gas_0 = self.bus.read_register_8bit(0x70)
        self.head_off = (_ctrl_gas_0 >> 3) & 0b1
        
    def reg_gas_wait_x(self):
        """"""
        self.gas_wait_x = self.bus.read_n_bytes(0x64, 10)
        
    def reg_res_heat_x(self):
        self.res_heat_x = self.bus.read_n_bytes(0x5A, 10)
        
    def reg_idac_heat_x(self):
        self.idac_head_x = self.bus.read_n_bytes(0x50, 10)
        
    def mode_sleep(self):
        """Set chip mode to Sleep Mode"""
        self.bus.write_n_bytes([])
        
    def mode_forced(self):
        """Set chip mode to Forced Mode (active for measurement)"""
        self.bus.write_n_bytes([])

        
    def read_calibration(self):
        """Read & save the calibration coefficients
        
        COEFF_ADDR1     = 0x89
        COEFF_ADDR2     = 0xE1
        
        Coefficients are not listed in memory map, table 20.  Instead they are
        referenced in Tables 11, 12, 13 and 14
        """
        coeff  = self.bus.read_register_nbit(0x89, 25)
        coeff += self.bus.read_register_nbit(0xE1, 16)

        coeff = list(struct.unpack('<hbBHhbBhhbbHhhBBBHbbbBbHhbb', bytes(coeff[1:39])))
        #print("\n\n",coeff)
        coeff = [float(i) for i in coeff]
        self._temp_calibration = [coeff[x] for x in [23, 0, 1]]
        self._pressure_calibration = [coeff[x] for x in [3, 4, 5, 7, 8, 10, 9, 12, 13, 14]]
        self._humidity_calibration = [coeff[x] for x in [17, 16, 18, 19, 20, 21, 22]]
        self._gas_calibration = [coeff[x] for x in [25, 24, 26]]

        # flip around H1 & H2
        self._humidity_calibration[1] *= 16
        self._humidity_calibration[1] += self._humidity_calibration[0] % 16
        self._humidity_calibration[0] /= 16

        self._heat_range = (self.bus.read_register_8bit(0x02) & 0x30) / 16
        self._heat_val = self.bus.read_register_8bit(0x00)
        self._sw_err = (self.bus.read_register_8bit(0x04) & 0xF0) / 16

    # break out reading methods
        
    def set_filter(self, coeff):
        """Set the temperature and pressure IIR filter
        
        Parameters
        ----------
        coeff : int, filter coefficient.  Valid values are:
            0, 1, 3, 7, 15, 31, 63, 127
        """
        mapper = {0: 0b000, 1: 0b001, 3: 0b010, 7:0b011, 15:0b100,
                  31: 0b101, 63: 0b110, 127: 0b111}
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
        
        htp_mapper = {0:0b000, 1:0b001, 2:0b010, 4:0b011, 8:0b100, 16:0b101}
        self.humidity_oversample = h_mapper[h]
        # ctrl_hum register, 0x72, osrs_h
        self.bus.write_n_bytes([0x72, self.humidity_oversample])
        
        self.temp_oversample = htp_mapper[t]
        self.pressure_oversample = htp_mapper[p]
        # ctrl_meas register, 0x74, osrs_t and osrs_p
        self.bus.write_n_bytes([0x74,
                               ((self.temp_oversample << 5) |
                                (self.pressure_oversample << 2))
                               ])
            
    def enable_measurement(self):
        """Enable gas measurement
        Note: sets nb_conv = number of conversions to index 0"""
        # gas measurements enabled
        reg_ctrl_gas_1 = self.nb_conv | 0b1000
        self.bus.write_n_bytes([0x71, reg_ctrl_gas_1])

        # read current ctrl_meas register
        # (which contains osrs_t and osrs_p)
        # and initiate single shot mode at 1:0
        reg_ctrl_meas = self.bus.read_register_8bit(0x74)
        reg_ctrl_meas = (reg_ctrl_meas & 0xFC) | 0x01
        self.bus.write_n_bytes([0x74, reg_ctrl_meas])
        
    def enable_measurement_old(self):
        # gas measurements enabled
        self.bus.write_n_bytes([REG_CTRL_GAS, RUNGAS])

        ctrl = self.bus.read_register_8bit(REG_CTRL_MEAS)
        ctrl = (ctrl & 0xFC) | 0x01  # enable single shot!
        self.bus.write_n_bytes([REG_CTRL_MEAS, ctrl])
        
    def get_measurement_status(self):
        reg_meas_status = self.bus.read_register_8bit(0x1D)
        self.gas_meas_index = reg_meas_status & 0b111
        self._new_data = reg_meas_status >> 7
        self._gas_measuring = (reg_meas_status >> 6) & 0b1
        self._measuring = (reg_meas_status >> 5) & 0b1
        
        #return self.bus.read_n_bytes(0x1D, 1)
        
    def get_reading(self):
        self.enable_measurement()
        self._new_data = 0
        while self._new_data == 0:
            self.get_measurement_status()
        return self.bus.read_n_bytes(0x1F, 14)
        
        #new_data = False
        #while not new_data:
            
        #    new_data = data[0] & 0x80 != 0
        #    time.sleep(0.005)
        
    def measure(self):
        data = self.get_reading()
        self._adc_pres = _read24(data[1:4]) / 16
        self._adc_temp = _read24(data[4:7]) / 16
        self._adc_hum = struct.unpack('>H', bytes(data[7:9]))[0]
        self._adc_gas = int(struct.unpack('>H', bytes(data[12:14]))[0] / 64)
        self._gas_range = data[13] & 0x0F

        var1 = (self._adc_temp / 8) - (self._temp_calibration[0] * 2)
        var2 = (var1 * self._temp_calibration[1]) / 2048
        var3 = ((var1 / 2) * (var1 / 2)) / 4096
        var3 = (var3 * self._temp_calibration[2] * 16) / 16384
        self._t_fine = int(var2 + var3)
        calc_temp = (((self._t_fine * 5) + 128) / 256)
        calc_temp = calc_temp / 100
        print(self._t_fine, calc_temp)
        
    @property
    def temperature(self):
        """The compensated temperature in degrees celsius."""
        #self._perform_reading()
        calc_temp = (((self._t_fine * 5) + 128) / 256)
        print("here")
        return calc_temp / 100
        
    def debug_read_registers(self):
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
        
    def _perform_reading(self):
        """Perform a single-shot reading from the sensor and fill internal data structure for
           calculations"""
        if time.monotonic() - self._last_reading < self._min_refresh_time:
            return

        # set filter
        self.bus.write_n_bytes([REG_CONFIG, self.filter << 2])
        
        # turn on temp oversample & pressure oversample
        self.bus.write_n_bytes([REG_CTRL_MEAS,
                                ((self.temp_oversample << 5) |
                                 (self.pressure_oversample << 2))])
        
        # turn on humidity oversample
        self.bus.write_n_bytes([REG_CTRL_HUM, self.humidity_oversample])
        
        # gas measurements enabled
        self.bus.write_n_bytes([REG_CTRL_GAS, RUNGAS])

        ctrl = self.bus.read_register_8bit(REG_CTRL_MEAS)
        ctrl = (ctrl & 0xFC) | 0x01  # enable single shot!
        self.bus.write_n_bytes([REG_CTRL_MEAS, ctrl])
        
        new_data = False
        while not new_data:
            #data = self._read(REG_MEAS_STATUS, 15)
            data = self.bus.read_n_bytes(REG_MEAS_STATUS, 15)
            new_data = data[0] & 0x80 != 0
            time.sleep(0.005)
        self._last_reading = time.monotonic()

        self._adc_pres = _read24(data[2:5]) / 16
        self._adc_temp = _read24(data[5:8]) / 16
        self._adc_hum = struct.unpack('>H', bytes(data[8:10]))[0]
        self._adc_gas = int(struct.unpack('>H', bytes(data[13:15]))[0] / 64)
        self._gas_range = data[14] & 0x0F

        var1 = (self._adc_temp / 8) - (self._temp_calibration[0] * 2)
        var2 = (var1 * self._temp_calibration[1]) / 2048
        var3 = ((var1 / 2) * (var1 / 2)) / 4096
        var3 = (var3 * self._temp_calibration[2] * 16) / 16384
        self._t_fine = int(var2 + var3)
            
            
            
            

    
    def get_temperature(self):
        par_t1 = self.bus.read_register_16bit(0xE9)
        par_t2 = self.bus.read_register_16bit(0x8A)
        par_t3 = self.bus.read_register_8bit(0x8C)
        
        temp_adc = self.bus.read_n_bytes(0x22)
        
    def test(self):
        '''
        par_t1 = self.bus.read_register_16bit(0xE9)
        print(hex(par_t1))
        print(hex(par_t1 >> 8))
        print(hex(par_t1 & 0x00ff))
        '''
        
        # set filter
        self.bus.write_n_bytes([REG_CONFIG, self.filter << 2])
        
        # turn on temp oversample & pressure oversample
        self.bus.write_n_bytes([REG_CTRL_MEAS,
                                ((self.temp_oversample << 5) |
                                 (self.pressure_oversample << 2))])
        
        ctrl = self.bus.read_register_8bit(REG_CTRL_MEAS)
        ctrl = (ctrl & 0xFC) | 0x01  # enable single shot!
        self.bus.write_n_bytes([REG_CTRL_MEAS, ctrl])
        
        par_t1_lsb = self.bus.read_register_8bit(0xE9)
        par_t1_msb = self.bus.read_register_8bit(0xEA)
        
        par_t1 = (par_t1_msb << 8) + par_t1_lsb
        
        par_t2_lsb = self.bus.read_register_8bit(0x8A)
        par_t2_msb = self.bus.read_register_8bit(0x8B)
        
        par_t2 = (par_t2_msb << 8) + par_t1_lsb
        
        par_t3 = self.bus.read_register_8bit(0x8C)
        
        t24 = self.bus.read_register_8bit(0x24)
        t23 = self.bus.read_register_8bit(0x23)
        t22 = self.bus.read_register_8bit(0x22)
        
        temp_adc = ((t22 << 16) + (t23 << 8) + t24) >> 4
        
        print("reg_t24:", hex(t24))
        print("reg_t23:", hex(t23))
        print("reg_t22:", hex(t22))
        print("temp_adc:", temp_adc)
        
        var1 = ((temp_adc / 16384.0) - (par_t1 / 1024.0)) * par_t2
        var2 = (((temp_adc / 131072.0) - (par_t1 / 8192.0)) *
                ((temp_adc / 131072.0) - (par_t1 / 8192.0)) * 
                (par_t3 * 16.0))
        t_fine = var1 + var2
        
        temp_comp = t_fine / 5120.0
        print("temp_comp:", temp_comp)
        
        #print(hex(par_t1_lsb))
        #print(hex(par_t1_msb))
        
        #par_t2 = self.bus.read_register_16bit(0x8A)
        #par_t3 = self.bus.read_register_8bit(0x8C)
        
        #temp_adc = self.bus.read_n_bytes(0x22, 3)
        #print(hex(temp_adc / 16))