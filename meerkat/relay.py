"""Relays for controlling high current devices

Colin Dietrich 2019"""

from meerkat.base import I2C, DeviceData, time
from meerkat.data import CSVWriter, JSONWriter

class Single:
    
    def __init__(self, bus_n, bus_addr=0x18, output='csv'):
        
        # i2c bus
        self.bus = I2C(bus_n=bus_n, bus_addr=bus_addr)
        
        self.state_mapper = {0: "closed", 1: "open"}
        
    def get_version(self):
        """Get the firmware version of the relay
        
        Returns
        -------
        int, version number of firmware
        """
        return self.bus.read_register_8bit(0x04)
        
    def get_status(self):
        """Get the status of the relay
        
        Returns
        -------
        int, where 0 == relay is open / not connected 
                   1 == relay is closed / connected
        """
        
        return self.bus.read_register_8bit(0x05)
    
    def off(self):
        """Turn the relay off.  State will report 0."""
        self.bus.write_byte(0x00)
    
    def on(self):
        """Turn the relay on.  State will report 1."""
        self.bus.write_byte(0x01)
        
    def toggle(self, verbose=False):
        """Toggle state of relay
        if open, close
        if closed, open
        
        Parameters
        ----------
        verbose : bool, print debug statements
        """
        
        state = self.get_status()
        if verbose:
            print("Relay found {}.".format(self.state_mapper[state]))
        
        if state == 0:
            self.on()
        elif state == 1:
            self.off()
        
        if verbose:
            print("Relay toggled.")
            
    def change_address(self, new_address, verbose=False):
        """Change the I2C address of the relay.  This is a persistant change in 
        EPROM memory.
        
        Parameters
        ----------
        new_address : int, new I2C address between 0x07 and 0x78
        verbose : bool, print debug statements
        """
        
        if ((new_address < 0x07) or (new_address > 0x78)):
            if verbose:
                print("Address outside allowed range")
            return False
        
        self.bus.write_register_8bit(0x03, new_address)
        if verbose:
            print("Relay I2C address changed to 0x{:02x}".format(new_address))