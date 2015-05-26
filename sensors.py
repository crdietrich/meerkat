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
        sample_rate : int, speed at which to sample, in seconds
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
        self.ox = None
        self.ph = None
        self.ec = None
        self.connect()

        # queue for each data reading
        # item format: [do,ox,ph,ec,tds,sal,sg]
        self.q = queue.Queue()

        # flags
        self.poll_flag = False

        # polling attributes
        self.sample_rate = sample_rate

    def connect(self):
        """Instance each sensor on the i2c bus"""
        self.do = atlas_rpi_i2c.atlas_i2c(address=0x61, bus=0)
        # self.ox = atlas_rpi_i2c.atlas_i2c(address=0x62, bus=0)
        self.ph = atlas_rpi_i2c.atlas_i2c(address=0x63, bus=0)
        self.ec = atlas_rpi_i2c.atlas_i2c(address=0x64, bus=0)

    def query_all(self):
        """Get all sensor values and return them in a list

        Returns
        -------
        list of floats, in format [unix_time,do,ox,ph,ec,tds,sal,sg]
        """

        try:
            dor = self.do.query("R")
            if dor[0]:
                do = [float(dor[1])]
        except:
            do = [-1]

        # try:
        #     oxr = self.ox.query("R")
        #     if oxr[0]:
        #         ox = [float(oxr[1])]
        # except:
        #     ox = [-1]

        ox = [-1]

        try:
            phr = self.ph.query("R")
            if phr[0]:
                ph = [float(phr[1])]
        except:
            ph = [-1]

        try:
            ecr = self.ec.query("R")
            if ecr[0]:
                ec_all = ecr[1]
                ec_all = [float(n) for n in ec_all.split(",")]
        except:
            ec_all = [-1,-1,-1,-1]
        all = [time.time()] + do + ox + ph + ec_all
        return all


    def poll(self):
        """Poll the sensors at regular intervals and put them in the queue.
        Items must be removed by explicit calls to self.q.get()
        """

        self.poll_flag = True
        while self.poll_flag:
            self.q.put(self.query_all(), block=True, timeout=10)  # note 10s
            time.sleep(self.sample_rate-1.5*3)

    def poll_print_queue(self):
        """Poll the sensors at regular intervals using the queue and
        print to terminal.  Unless something goes wrong, self.q should
        have at maximum 1 item in it.
        """
        self.poll_flag = True
        while self.poll_flag:
            self.q.put(self.query_all(), block=True, timeout=10)  # note 10s
            print(self.q.get(block=True, timeout=10))
            time.sleep(self.sample_rate-1.5*3)

    def poll_sensors(self):
        """Poll the sensors at regular intervals, but make it look
        good for terminal printing and debugging.  No use of the queue.
        """
        self.poll_flag = True
        while self.poll_flag:
            print(self.do.name, self.do.query("R"))
            print(self.ph.name, self.ph.query("R"))
            print(self.ec.name, self.ec.query("R"))
            time.sleep(self.sample_rate-1.5*3)

if __name__ == '__main__':
    ai2c = AtlasI2C()
    # ai2c.poll()
    ai2c.poll_print_queue()
    # ai2c.poll_sensors()
