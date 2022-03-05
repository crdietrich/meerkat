"""MCP4728 Digitial to Analog Converter (DAC) for Raspberry Pi & MicroPython

Colin Dietrich, 2021
"""

from meerkat.base import I2C
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
        In most I2C cases, v_dd will be either 3.3V or 5.0V. The MCP4728 can
        handle as much as 24mA current at 5V (0.12W) in short circuit. 
        By comparison, the Raspberry Pi can source at most 16mA of current 
        at 3.3V (0.05W). Unless the application output will draw a very 
        small amount of current, an external (to the I2C bus) voltage source 
        should probably be used. 
        See the Adafruit ISO1540 Bidirectional I2C Isolator as a possible solution.
        
        Note 3
        ------
        The manufacturer uses the term VDD (Vdd) for external voltage, many other 
        sources use the term VCC (Vcc). VDD is used here to be consistent with the
        datasheet, but manufacturers like Adafruit use VCC on the pinouts labels.
        
        Parameters
        ----------
        bus_n : int, i2c bus number on Controller
        bus_addr : int, i2c bus number of this Worker device
        """
    
        # i2c bus
        self.bus = I2C(bus_n=bus_n, bus_addr=bus_addr)
        self.udac = 0
        self.state = {'a': None, 'b': None, 
                      'c': None, 'd': None}
        self.v_dd = None
        
        # information about this device
        self.metadata = Meta(name=name)
        self.metadata.description = 'MCP4728 12-bit Digitial to Analog Converter'
        self.metadata.urls = 'http://ww1.microchip.com/downloads/en/DeviceDoc/22187E.pdf'
        self.metadata.manufacturer = 'Microchip'
        
        self.metadata.header    = ['description', 'channel', 'v_ref_source',  'v_dd',   'power_down', 'gain', 'input_code', 'output_voltage']
        self.metadata.dtype     = ['str',         'str',     'str',           'float',  'str',        'int',  'int', 'float']
        self.metadata.units     = [None,          None,      None,            'volts',  None,         None,   None, 'volts']
        self.metadata.accuracy  = None 
        self.metadata.precision = 'vref: gain 1 = 0.5mV/LSB, gain 2 = 1mV/LSB; vdd: vdd/4096'
        
        self.metadata.bus_n    = bus_n
        self.metadata.bus_addr = hex(bus_addr)

        # data recording method
        self.writer_output = output
        self.csv_writer  = CSVWriter(metadata=self.metadata,  time_source='std_time_ms')
        self.json_writer = JSONWriter(metadata=self.metadata, time_source='std_time_ms')
        
        
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
    
    def set_channel(self, channel, v_ref_source, power_down, gain, input_code, description='no description'):
        """Write single channel output
        
        Parameters
        ----------
        channel : str, either 'a', 'b', 'c' or 'd' corresponding 
            to the output channel
        v_ref_source : str, either 'internal' (2.048V/4.096V) or 'external' (VDD)
        power_down : str, either 'normal' or one of the power-down
            resistor to ground values of '1k' '100k' or '500k'
        gain : int, either 1 or 2 for multiplier relative to
            the internal reference voltage
        input_code : int, between 0 and 4095 to set the 
            output voltage
        """
        
        assert self.v_dd is not None, "External reference voltage, `v_dd` is not set."
        
        channel_map      = {'a': 0b00, 'b': 0b01, 'c': 0b10, 'd': 0b11}
        v_ref_source_map = {'internal': 1, 'external': 0}
        power_down_map   = {'normal': 0b00, '1k': 0b01, '100k': 0b10, '500k': 0b11}
        gain_map         = {1: 0, 2: 1}
        
        # single write command
        # C2 = 0, C1 = 1, C0 = 0, W1 = 1, W0 = 1
        single_write_command = 0b01011000
        byte_2 = single_write_command + channel_map[channel] + self.udac
        
        byte_3 = ((v_ref_source_map[v_ref_source] << 7) + 
                  (power_down_map[power_down] << 5) +
                  (gain_map[gain] << 4) + 
                  (input_code >> 8))
        
        byte_4 = input_code & 0b11111111
        
        self.bus.write_n_bytes(data=[byte_2, byte_3, byte_4])
        
        self.channel_state = self.channel_state[channel] = {'v_ref_source': v_ref_source, 
                                                            'power_down': power_down,
                                                            'gain': gain, 
                                                            'input_code': input_code, 
                                                            'description': description}
        
        v_dd_to_v_ref_map = {'internal': 2.048 * gain, 'external': self.v_dd}
        v_ref_voltage = v_dd_to_v_ref_map[v_ref_source]
        output_voltage = self.output_voltage(input_code, v_ref_source=v_ref_source, gain=gain, v_dd=v_ref_voltage)
        
        # round to one more place than the precision of the chip
        # gain 1 = 0.5mV/LSB so 0.5mV = 0.0005V, therefore return 5 decimal places
        # gain 2 = 1mV/LSB so 1mV = 0.001V, therefore return 4 decimal places
        gain_rounder = {1: 5, 2: 4}
        output_voltage = round(output_voltage, gain_rounder[gain])
        
        self.state[channel] = [description, channel, v_ref_source, self.v_dd, power_down, gain, input_code, output_voltage]
        
    @staticmethod
    def calculate_input_code(v_target, v_ref_source, gain, v_dd):
        """Calculate the required input register code
        required to produce a specific voltage

        Parameters
        ----------
        v_target : float, voltage target output on the DAC
        v_ref_source : str, either 'internal' (2.048V/4.096V) or 'external' (VDD)
        gain : int, gain of DAC, either 1 or 2
        v_dd : float, voltage source for the device. Could be I2C 3.3V or 5.0V, 
            or something else supplied on VDD

        Returns
        -------
        int, DAC inpute code required to achieve v_target
        """

        if v_ref_source == 'internal':
            if v_target > v_dd:
                return 'v_target must be <= v_dd'
            
            if (v_target > 2.048) & (gain == 1):
                return 'Gain must be 2 for v_target > v_ref internal'

            if (v_target > 4.096) & (gain == 2):
                return 'v_target must be <= 4.096V if using internal'
                
            return int((v_target * 4096) / (2.048* gain))
        if v_ref_source == 'external':
            if v_target > v_dd:
                return 'v_target must be <= v_dd'
            
            return int((v_target * 4096) /  v_dd)

    @staticmethod
    def output_voltage(input_code, v_ref_source, gain, v_dd=None):
        """Check output code voltage output

        Parameters
        ----------
        input_code : int, DAC inpute code required to achieve v_target
        v_ref_source : str, either 'internal' (2.048V/4.096V) or 'external' (VDD)
        gain : int, gain of DAC, either 1 or 2
        v_dd : float, voltage source for the device. Could be I2C 3.3V or 5.0V, 
            or something else supplied on VDD
        Returns
        -------
        v_target : float, DAC vol
        """

        if v_ref_source == 'internal':
            return (2.048 * input_code * gain) / 4096
        
        if v_ref_source == 'external':
            return (v_dd * input_code) / 4096
    
    @staticmethod
    def data_filler(data, cid):
        """Fill non-initialized channel data for publishing and writing

        Parameters
        ----------
        data : dict, self.state
        cid : str, channel id, one of 'a', 'b', 'c' or 'd'

        Returns
        -------
        list of lists, self.state data with None data filled 
            to match self.metadata.header
        """

        if data[cid] is None:
            return ['not_initialized', cid, None, None, None, None, None]
        else:
            return data[cid]
            
    def publish(self):
        """Output relay status data in JSON.

        Parameters
        ----------
        description : str, description of data sample collected
        n : int, number of samples to record in this burst
        delay : float, seconds to delay between samples if n > 1

        Returns
        -------
        str, formatted in JSON with keys:
            description: str, description of sample under test
            temperature : float, temperature in degrees Celcius
        """
        
        data_list = []
        for channel in ['a', 'b', 'c', 'd']:
            data = self.data_filler(self.state, channel)
            data_list.append(self.json_writer.publish(data))
        return data_list
    
    def write(self):
        """Format output and save to file, formatted as either
        .csv or .json.

        Parameters
        ----------
        description : str, description of data sample collected
        n : int, number of samples to record in this burst
        delay : float, seconds to delay between samples if n > 1
        
        Returns
        -------
        None, writes to disk the following data:
            description : str, description of sample
            sample_n : int, sample number in this burst
            temperature : float, temperature in degrees Celcius
        """
        wr = {"csv": self.csv_writer,
              "json": self.json_writer}[self.writer_output]
        for channel in ['a', 'b', 'c', 'd']:
            data = self.data_filler(self.state, channel)
            wr.write(data)
