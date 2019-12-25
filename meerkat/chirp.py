"""Chirp Soil Moisture Sensor

2019 Colin Dietrich"""


from meerkat.base import I2C, DeviceData, twos_comp_to_dec, time
from meerkat.data import CSVWriter, JSONWriter

class Chirp:
    def __init__(self, bus_n, bus_addr=0x20, output='csv'):
        """Initialize worker device on i2c bus
        
        Parameters
        ----------
        bus_n : int, i2c bus number on Controller
        bus_addr : int, i2c bus number of this Worker device        
        output: str, output writer type
        """
        
        # i2c bus
        self.bus = I2C(bus_n=bus_n, bus_addr=bus_addr)

        # time to wait for conversion to finish
        self.delay = 1.1  # units = seconds
        
        self.reg_map = {"capacitance": 0,
                        "light": 4
                        "temperature": 5,
                        "reset": 6
                        }
        self.reg_delay = {"capacitance": 0.020,
                          "light": 9
                          "temperature": 0.020,
                          "reset": 0
                          }
        
    def read_register(self, reg_name):
        reg_addr = self.reg_map[reg_name]
        self.bus.write_byte(reg_addr)
        time.sleep(self.reg_delay[reg_name])
        return self.bus.read_register_16bit(2)
