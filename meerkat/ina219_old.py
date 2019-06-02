# Class for controlling the TI INA219 current/power measurement chip
# Copyright (c) 2015 Colin Dietrich
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from sys import byteorder
import time

import Adafruit_GPIO.I2C as I2C


class INA219(object):
    """Texas Instruments INA219 current/power monitor"""

    def __init__(self, address=0x40, i2c=None, **kwargs):
        if i2c is None:
            self.i2c = I2C
        self.device = self.i2c.get_i2c_device(address=address, **kwargs)

        self.host_endian_is_little = True
        if byteorder == "big":
            self.host_endian_is_little = False

        self.status = "Initialized"

        self.mode = None
        self.mode_str = None
        self.mode_description = None

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

    def read_register(self, address):
        """Read an unsigned 16 bit Big Endian register
        """

        read_endian = not self.host_endian_is_little
        return self.device.readU16(address, little_endian=read_endian)

    def get_config(self):
        """Get the 16 bit Big Endian INA219 configuration register (0x00)
        """

        self.reg_00 = self.read_register(0x00)

    def set_config(self):
        """Set the 16 bit Big Endian INA219 configuration register (0x00)
        """

        reg_00 = self.reg_00
        if self.host_endian_is_little:
            reg_00 = I2C.reverseByteOrder(reg_00)
        self.device.write16(0x00, reg_00)

    def int_to_binary_string(self, number, bits=16):
        """convert a 16 bit integer to 16 bit string representation

        Parameters
        ----------
        number : int16, register value in 16 bit integer representation
        bits : int, number of zeros ('0') to pad the string representation
            to if the binary conversion is less than the bit size of the
            integer.  Defaults to 16.

        Returns
        -------
        str, 16 character string representation of register value
        """

        formatter = "{0:0" + str(bits) + "b}"
        return formatter.format(number)

    def sign_extend(self, value, bits):
        """Extend the sign bit of a value to a target number of total bits.

        Parameters
        ----------
        value : int, value to sign extend
        bits : int, number of bits to extend value to

        """
        sign_bit = 1 << (bits - 1)
        return (value & (sign_bit - 1)) - (value & sign_bit)

    def set_bit(self, v, index, x):
        """Set the index:th bit of v to x, and return the new value."""
        mask = 1 << index
        v &= ~mask
        if x:
            v |= mask
        return v

    def reset(self):
        """Resets all registers to default values, this bit self-clears"""
        self.get_config()
        self.reg_00 = self.set_bit(self.reg_00, 15, 1)
        self.device.write16(0x00, self.reg_00)

        # defaults (on power up and reset)
        self.shunt_voltage = 0
        self.bus_voltage = 0
        
        self.gain = 8  # chip default
        self.gain_string = self.gain_strings[self.gain]
        self.bus_voltage_range = 32
        self.status = "Reset to factory defaults"

    def set_bus_voltage_range(self, v=32):
        """Set the bus voltage range.  INA219 defaults to 32 volts.

        Parameters
        ----------
        v : int, voltage range of bus. Valid values = [16, 32]
        """

        if v not in [16, 32]:
            self.status = "Bus voltage can only be 16 or 32 volts."
            if self.raise_errors:
                raise ValueError(self.status)
        else:
            bit_values = {16: 0, 32: 1}
            bit = bit_values[v]
            self.get_config()
            self.reg_00 = self.set_bit(self.reg_00, 13, bit)
            self.set_config()
            self.bus_voltage_range = v
        self.status = "Bus voltage range set to %s VDC" % v

    def set_shunt_voltage_range(self, gain=8):
        """Sets PGA gain.  Voltage ranges are determined by gain level.

        Gains available:
        [1, 2, 4, 8]
        With ranges available:
        +/- [40, 80, 160, 320] in mV
        """

        gain_int = int(gain)
        if gain_int not in [1, 2, 4, 8]:
            self.status = "Gain voltage can only be set to 1, 2, 4, or 8."
            if self.raise_errors:
                raise ValueError(self.status)
        else:
            self.gain = gain_int
            self.gain_string = self.gain_strings[self.gain]
            gain_str = self.gain_to_bin[self.gain]
            self.get_config()
            self.reg_00 = self.set_bit(self.reg_00, 12, int(gain_str[0]))
            self.reg_00 = self.set_bit(self.reg_00, 11, int(gain_str[1]))
            self.set_config()
        self.status = "Shunt voltage range set to %s" % self.gain_strings[gain_int]

    def set_badc(self, mode=8):
        """Set the Bus Analog to Digital Converter resolution.  Accepts
        bits    mode    mode/samples
        0X00    4       9 bit
        0X01    5       10 bit
        0X10    6       11 bit
        0X11    7       12 bit
        1000    8       12 bit

        Parameters
        ----------
        mode : int, value to write to 4 bit register range
        """
        mode_int = int(mode)
        if mode_int not in self.adc_modes.keys():
            self.status = "BADC mode range invalid."
            if self.raise_errors:
                raise ValueError(self.status)
        self.get_config()
        mode_str = self.int_to_binary_string(self.adc_modes[mode_int], 4)
        self.reg_00 = self.set_bit(self.reg_00, 10, int(mode_str[0]))
        self.reg_00 = self.set_bit(self.reg_00, 9, int(mode_str[1]))
        self.reg_00 = self.set_bit(self.reg_00, 8, int(mode_str[2]))
        self.reg_00 = self.set_bit(self.reg_00, 7, int(mode_str[3]))
        self.set_config()
        self.status = "BADC mode set to %s" % self.adc_modes[mode_int]

    def set_sadc(self, mode=8):
        """Set the Shunt Analog to Digital Converter resolution"""
        mode_int = int(mode)
        if mode_int not in self.adc_modes.keys():
            self.status = "SADC mode range invalid."
            if self.raise_errors:
                raise ValueError(self.status)
        self.get_config()
        mode_str = self.int_to_binary_string(self.adc_modes[mode_int], 4)
        self.reg_00 = self.set_bit(self.reg_00, 6, int(mode_str[0]))
        self.reg_00 = self.set_bit(self.reg_00, 5, int(mode_str[1]))
        self.reg_00 = self.set_bit(self.reg_00, 4, int(mode_str[2]))
        self.reg_00 = self.set_bit(self.reg_00, 3, int(mode_str[3]))
        self.set_config()
        self.status = "SADC mode set to %s" % self.adc_modes[mode_int]

    def set_mode(self, mode=7):
        """Set the mode to the configuration register (0x00)
        Modes available listed in self.modes.

        Parameters
        ----------
        mode: int, value to write to 3 bit register range
        """
        mode_int = int(mode)
        if mode_int not in self.modes.keys():
            self.status = "INA219 mode invalid"
            if self.raise_errors:
                raise ValueError(self.status)
        self.get_config()
        mode_str = self.int_to_binary_string(mode_int, 3)
        self.reg_00 = self.set_bit(self.reg_00, 2, int(mode_str[0]))
        self.reg_00 = self.set_bit(self.reg_00, 1, int(mode_str[1]))
        self.reg_00 = self.set_bit(self.reg_00, 0, int(mode_str[2]))
        self.set_config()
        self.status = "Mode set to %s" % self.modes[mode_int]

    def get_shunt_voltage(self):
        """Read the shunt voltage register where LSB = 10uV

        Sets
        ----
        self.shunt_voltage : float, voltage across shunt resistor

        """
        self.reg_01 = self.read_register(0x01)
        # LSB is 10 microvolts, convert to volts
        self.shunt_voltage = (self.reg_01 * 10) / 1e6
        self.status = "Shunt voltage measured"

    def get_bus_voltage(self):
        """Read the bus voltage register where LSB = 4mV.

        Sets
        ----
        self.bus_voltage : unsigned int
            32 volt range => 0 to 32 VDC
            16 volt range => 0 to 16 VDC
        """

        self.reg_02 = self.read_register(0x02)
        _r = self.reg_02
        # right most 3 bits are 0, CNVR, OVF
        _r = _r >> 3
        # LSB is 4.0mV, convert to volts
        self.bus_voltage = (_r * 4.0) / 1000
        self.status = "Bus voltage measured"

    def get_current_simple(self):
        """Calculate the current in amps from the known shunt resistance,
        and measured shunt voltage across the resistance.  If shunt resistance
        attribute is not set, defaults to Adafruit INA219 shunt resistor
        (0.1 ohm 1% 2W resistor).  Does not use the INA219 internal configuration
        registers.

         Attributes
         ----------
         self.r : float, shunt resistance in ohms

         Returns
         -------
         i_simple : float, current in amps measured across shunt resistance
        """

        self.get_shunt_voltage()
        self.i = self.shunt_voltage / self.r_shunt
        self.status = "Current calculated"

    def get_power_simple(self):
        """Calculate the power in watts from the known shunt resistance,
        measured bus voltage and measured shunt voltage.  If shunt resistance
        attribute is not set, defaults to Adafruit INA219 shunt resistor
        (0.1 ohm 1% 2W resistor).  Does not use the INA219 internal configuration
        registers.

        Attributes
        ----------
        self.r : float, shunt resistance in ohms

        Returns
        -------
        p_simple : float, power in watts measured across shunt
        """

        self.get_bus_voltage()
        self.get_current_simple()
        self.p = self.bus_voltage * self.i
        self.status = "Power calculated"

    def set_energy_units(self, units="J"):
        """Set units for energy calculations.

        Parameters
        ----------
        units : str, accepted values are "J", "Wh" and "kWh" for
            joules, watt-hours and kilowatt-hours respectively.

        Sets
        ----
        self.units : str, class attribute of parameter units
        self.e_unit_convert : float, value to multiply class
            calculations in joules to return in parameter units
        """

        converter = {"J": 1.0,
                     "Wh": 1.0/3.6e3,
                     "kWh": 1.0/3.6e6}

        if units not in converter:
            self.status = "Energy unit not understood"
        else:
            self.units = units
            self.e_unit_convert = converter[units]
            self.status = "Energy units set to %s" % self.units

    def get_energy_simple(self):
        """Calculate energy transferred in joules from the known shunt
        resistance, measured bus voltage, measured shunt voltage and
        time since last method call.  Returns 0 power on first call
        and sets initial time.  Does not use INA219 internal power
        register.

        Attributes
        ----------
        self.r : float, shunt resistance in ohms

        Sets
        ----
        self.t0 : float, unix time when measurements began
        self.t_total : float, seconds measurements have been taken
        self.e : float, energy in joules transferred since self.t0

        """

        _t = time.time()
        self.get_power_simple()
        if self.t0 == 0:
            self.t0 = _t
            self.t_last = _t
        else:
            # energy = power x time (J = W * s)
            self.e = self.p * (_t - self.t_last) * self.e_unit_convert
            self.e_total += self.e
            self.t_last = _t
            self.t_total = _t - self.t0
        self.status = "Energy calculated"
