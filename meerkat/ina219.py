"""Texas Instruments INA219 current and power measurement
2019 Colin Dietrich"""

from meerkat.base import I2C, DeviceData, time
from meerkat.data import CSVWriter, JSONWriter


class INA219:
    def __init__(self, bus_n, bus_addr=0x48, output='csv'):
        """Initialize worker device on i2c bus.

        Parameters
        ----------
        bus_n : int, i2c bus number on Controller
        bus_addr : int, i2c bus number of this Worker device
        """

        # i2c bus
        self.bus = I2C(bus_n=bus_n, bus_addr=bus_addr)

        self.reg_00 = None
        self.reg_01 = None
        self.reg_02 = None
        self.reg_03 = None
        self.reg_04 = None

        self.bin_to_gain = {"00": 1, "01": 2, "10": 4, "11": 8}
        self.gain_to_bin = {1: "00", 2: "01", 4: "10", 8: "11"}

        self.gain_strings = {1: "+/- 40mV",
                             2: "+/- 80mV",
                             4: "+/- 160mV",
                             8: "+/- 320mV"}

        self.modes = {0: "power down",
                      1: "shunt voltage, triggered",
                      2: "bus voltage, triggered",
                      3: "shunt and bus voltages, triggered",
                      4: "adc off (disabled)",
                      5: "shunt voltage, continuous",
                      6: "bus voltage, continuous",
                      7: "shunt and bus voltages, continuous"}

        self.adc_modes = {9: 4, 10: 5, 11: 6, 12: 8, 2: 9, 4: 10, 8: 11, 16: 12, 32: 13, 64: 14, 128: 15}

        # defaults (on power up and reset)
        self.gain = 8  # chip default
        self.gain_string = self.gain_strings[self.gain]
        self.shunt_voltage = 0
        self.bus_voltage = 1
        self.bus_voltage_range = 32
        self.power = 0

        # Adafruit INA219 breakout board as a 0.1 ohm 1% 2W resistor
        self.r_shunt = 0.1

        # current calculated from bus voltage and shunt current only
        self.i = 0
        self.p = 0

        # times for energy calculations
        self.t0 = 0
        self.t_last = 0
        self.t_total = 0
        self.e = 0
        self.e_total = 0

        # default unit of power is joule, conversions for Wh, kWh
        self.available_units = ["J", "Wh", "kWh"]
        self.units = "J"
        self.e_unit_convert = 1

        self.raise_errors = True

    def get_config(self):
        pass

    def set_config(self):
        pass

    def reset(self):
        pass

    def set_voltage_range(self, v=32):
        pass

    def set_pga_range(self, gain=8):
        pass

    def set_bus_adc_resolution(self, bit=12):
        pass

    def set_shunt_adc_resolution(self, bit=12):
        pass

    def set_mode(self):
        pass

    def get_shunt_voltage(self):
        pass

    def get_bus_voltage(self):
        pass

    def get_current(self):
        pass

    def get_power(self):
        pass