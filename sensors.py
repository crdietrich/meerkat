#!/usr/bin/python
"""Atlas Scientific sensor reading using i2c bus on
Raspberry Pi
Colin Dietrich 2015
"""
try:
    import queue
except ImportError:
    import Queue as queue
import time

import atlas_rpi_i2c


class AtlasI2C(object):
    """Connect to Atlas Scientific sensors and poll them regularly"""

    def __init__(self, sample_rate=5):
        """Initalize i2c sensors

        Parameters
        ----------
        samplerate : int, speed at which to sample, in seconds
            Note: lower limit is 4.5s based on 1.5s per sensor limit

        """

        # default i2c addresses, override if there's a conflict
        self.do_default_address = 0x61
        self.ph_default_address = 0x63
        self.ec_default_address = 0x64

        # default i2c bus, different versions of RPi are on 0 or 1
        self.i2c_bus = 0

        # instance i2c bus controller classes
        self.do = None
        self.ph = None
        self.ec = None
        self.connect()

        # queues for each data reading
        self.doq = queue.Queue()
        self.phq = queue.Queue()
        self.ecq = queue.Queue()

        # flags
        self.poll_flag = False

        # polling attributes
        self.sample_rate = sample_rate
        self.temperature = 23.0
        self.conductivity = 0
        self.salinity = 0

    def connect(self):
        """Instance each sensor on the i2c bus"""
        self.do = atlas_rpi_i2c.atlas_i2c(address=0x61, bus=0)
        self.ph = atlas_rpi_i2c.atlas_i2c(address=0x63, bus=0)
        self.ec = atlas_rpi_i2c.atlas_i2c(address=0x64, bus=0)

    def poll(self):
        """Poll the sensors at regular intervals

        :return:
        """
        self.poll_flag = True
        while self.poll_flag:
            print(self.do.query("R"))
            print(self.ph.query("R"))
            print(self.ec.query("R"))
            time.sleep(self.sample_rate-1.5*3)


# # test of each sensor on the bus
# for command in ["I", "STATUS"]:
#     print("do>> " + do.query(command))
#     print("ph>> " + ph.query(command))
#     print("ec>> " + ec.query(command))
if __name__ == '__main__':
    ai2c = AtlasI2C()
    ai2c.poll()
