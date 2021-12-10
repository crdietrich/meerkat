"""MCP4728 Digitial to Analog Converter (DAC) for Raspberry Pi & MicroPython

Colin Dietrich, 2021
"""

from meerkat.base import I2C, time
from meerkat.data import Meta, CSVWriter, JSONWriter


class MCP4728(object):
    def __init__(self, bus_n, bus_addr=0x60, output='csv', name='mcp4728'):
        """Initialize worker device on i2c bus.
        
        Note 1
        ------
        Default I2C bus address is 0x60 = 0b1100000
        
        From the dataset, section 5.3:
        The first part of the address byte consists of a 4-bit device code,
        which is set to 1100 for the MCP4728 device. The device code is 
        followed by three I2C address bits (A2, A1, A0) which are 
        programmable by the users.
        
        4-bit device code: 
            0b 1 1 0 0 

        Programmable user bits:
            0b A1 A2 A3 = 0b 0 0 0 

        (a) Read the address bits using “General Call Read
        Address” Command (This is the case when the
        address is unknown). See class self.read_address().
        (b) Write I2C address bits using “Write I2C Address
        Bits” Command. The Write Address command will replace 
        the current address with a new address in both input 
        registers and EEPROM. See class method self.XXXX().
        
        Note 2
        ------
        

        Parameters
        ----------
        bus_n : int, i2c bus number on Controller
        bus_addr : int, i2c bus number of this Worker device
        """
    
        # i2c bus
        self.bus = I2C(bus_n=bus_n, bus_addr=bus_addr)
        self.udac = 0
        
    def general_call_reset(self):
        """Reset similar to power-on reset. See section 5.4.1."""
        self.bus.write_n_bytes(data=[0x00, 0x06])

    def general_call_wake_up(self):
        """Reset power-down bits. See section 5.4.2"""
        self.bus.write_n_bytes(data=[0x00, 0x09]) 
        
    def general_call_software_update(self):
        """Update all DAC analog outputs. See section 5.4.3"""
        self.bus.write_n_bytes(data=[0x00, 0x08]) 

    def general_call_read_address(self):
        """Return the I2C address. See section 5.4.4"""
        self.bus.write_n_bytes(data=[0x00, 0x0C])
        return self.bus.read_byte()
    
    def single_write(self, channel, vref, power_down, gain, input_code):
        """Write single channel output
        
        Parameters
        ----------
        channel : str, either 'a', 'b', 'c' or 'd' corresponding 
            to the output channel
        vref : str, either 'internal' (2.048V) or 'external'
        power_down : str, either 'normal' or one of the power-down
            resistor to ground values of '1k' '100k' or '500k'
        gain : int, either 1 or 2 for multiplier relative to
            the internal reference voltage
        input_code : int, between 0 and 4095 to set the 
            output voltage
        """
        
        channel_map    = {'a': 0b00, 'b': 0b01, 'c': 0b10, 'd': 0b11}
        vref_map       = {'internal': 1, 'external': 0}
        power_down_map = {'normal': 0b00, '1k': 0b01, '100k': 0b10, '500k': 0b11}
        gain_map       = {1: 0, 2: 1}
        
        # single write command
        # C2 = 0, C1 = 1, C0 = 0, W1 = 1, W0 = 1
        single_write_command = 0b01011000
        byte_2 = single_write_command + channel_map[channel] + self.udac
        
        byte_3 = ((vref_map[vref] << 7) + 
                  (power_down_map[power_down] << 5) +
                  (gain_map[gain] << 4) + 
                  (input_code >> 8))
        
        byte_4 = input_code & 0b11111111
        
        self.bus.write_n_bytes(data=[byte_2, byte_3, byte_4])
        
    @staticmethod
    def target_voltage(v_target, v_ref=2.048, gain=1):
        """Compute the required input register code 
        required to produce a specific voltage

        Parameters
        ----------
        v_target : float, voltage target output on the DAC
        v_ref : float, voltage reference. Default is Vref = 2.048
        gain : int, gain of DAC, either 1 or 2

        Returns
        -------
        int, DAC inpute code required to achieve v_target
        """
        return round(((v_target * 4095 ) / v_ref) / gain)

    @staticmethod
    def output_voltage(input_code, v_ref=2.048, gain=1):
        """Check output code voltage output

        Parameters
        ----------
        inpute_code : int, DAC inpute code required to achieve v_target
        v_target : float, voltage target output on the DAC
        v_ref : float, voltage reference. Default is Vref = 2.048
        gain : int, gain of DAC, either 1 or 2

        Returns
        -------
        v_target : float, DAC vol
        """
        return v_ref * (input_code / 4095) * gain
