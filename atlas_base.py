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
import MCP9808

class AtlasI2C(object):
    """Connect to Atlas Scientific sensors and poll them regularly.
    All sensors return -1 if there's an error."""

    def __init__(self, sample_rate=5):
        """Initalize i2c sensors

        Parameters
        ----------
        sample_rate : int, speed at which to sample, in seconds
            Note: lower limit is 4.5s based on 1.5s per sensor limit

        """

        # default i2c addresses, override if there's a conflict
        self.do_default_address = 0x61
        self.ox_default_address = 0x62
        self.ph_default_address = 0x63
        self.ec_default_address = 0x64

        # default i2c bus, different versions of RPi are on 0 or 1
        self.i2c_bus = 1

        # instance i2c bus controller classes
        self.do = None
        # self.ox = None
        self.ph = None
        self.ec = None
        self.connect()

        # queue for each data reading
        # item format: [do,ox,ph,ec,tds,sal,sg]
        self.q = queue.Queue()

        # flags
        self.poll_flag = False
        self.temp_error = False

        # polling attributes
        self.sample_rate = sample_rate

        # temperature sensor MCP9808
        self.temp = MCP9808.MCP9808()
        self.temp.begin()


    def connect(self):
        """Instance each sensor on the i2c bus"""
        self.do = atlas_rpi_i2c.atlas_i2c(address=0x61, bus=self.i2c_bus)
        self.ox = atlas_rpi_i2c.atlas_i2c(address=0x62, bus=self.i2c_bus)
        self.ph = atlas_rpi_i2c.atlas_i2c(address=0x63, bus=self.i2c_bus)
        self.ec = atlas_rpi_i2c.atlas_i2c(address=0x64, bus=self.i2c_bus)

    def query_all(self):
        """Get all sensor values and return them in a list. Doesn't attempt
        to pass dependent values between sensors.

        Returns
        -------
        list of floats and ints, in format:
            [unix_time,t,do,ox,ph,ec,tds,sal,sg,status]
            where:
            unix_time : float, seconds since the epoch
            t : float, temperature in degrees C
            do : float, dissolved oxygen in mg/L (% sat)
            ox : float, oxidation reduction potential in mV
            pH : float, pH units (negative logarithm of hydrogen ion)c
            ec : float, micro Siemens
            tds : float, mg/L
            sal : float, PSS-78 (no defined units, amount of dissolved salts)
            sg : float, Dimensionless unit (density ratio to pure water)

            All the following status variables follow
                0 = failure, 1 = success
            Read temperature sensor query
            tq : int, temperature sensor query
            Temperature Compensation
            dotc : int, dissolved oxygen temperature compensation command
            oxtc : int, oxydation reduction temperature compensation command
            phtc : int, dissolved oxygen temperature compensation command
            ectc : int, dissolved oxygen temperature compensation command
            Read sensor query
            doq : int, dissolved oxygen sensor query
            oxq : int, oxidation reduction potential sensor query
            phq : int, pH sensor query
            ecq : int, electrical conductivity sensor query

        """

        # keep track of errors
        status = []

        # 0 : Get the current temperature from the MCP9808
        try:
            t = [self.temp.readTempC()]
            self.temp_error = False
            status += [1]
        except:
            self.temp_error = True
            t = [-1]
            status += [0]

        # if there's an error getting the temperature, default to 23.0 C
        if self.temp_error:
            temp_temp = "23.0"
        else:
            temp_temp = "{:.2f}".format(t[0])

        # 1 : Dissolved Oxygen Temperature Compensation
        try:
            self.do.query("T," + temp_temp)
            status += [1]
        except:
            status += [0]

        # 2 : Oxidation Reduction Potential Temperature Compensation
        # try:
        #     self.ox.query("T," + temp_temp)
        #     status += [1]
        # except:
        #     status += [0]
        status += [0]

        # 3 : pH Temperature Compensation
        try:
            self.ph.query("T," + temp_temp)
            status += [1]
        except:
            status += [0]

        # 4 : Conductivity Temperature Compensation
        try:
            self.ec.query("T," + temp_temp)
            status += [1]
        except:
            status += [0]

        # 5 : Dissolved Oxygen Reading
        try:
            dor = self.do.query("R")
            # if dor[0]:
            do = [float(dor[1])]
            status += [1]
        except:
            status += [0]
            do = [-1]

        # 5 : Oxidation Reduction Potential Reading
        # try:
        #     oxr = self.ox.query("R")
        #     if oxr[0]:
        #         ox = [float(oxr[1])]
        # except:
        #     ox = [-1]
        ox = [-1]
        status += [0]

        # 6 : pH Reading
        try:
            phr = self.ph.query("R")
            # if phr[0]:
            ph = [float(phr[1])]
            status += [1]
        except:
            ph = [-1]
            status += [0]

        # 7 : Electrical Conductivity Reading
        try:
            ecr = self.ec.query("R")
            # if ecr[0]:
            ec_all = ecr[1]
            ec_all = [float(n) for n in ec_all.split(",")]
            status += [1]
        except:
            ec_all = [-1,-1,-1,-1]
            status += [0]

        # could go either way here, back to string for now
        status = [("").join([str(_) for _ in status])]

        all = [time.time()] + t + do + ox + ph + ec_all + status
        return all

    def poll(self):
        """Poll the sensors at regular intervals and put them in the queue.
        Items must be removed by explicit calls to self.q.get()
        """

        self.poll_flag = True
        while self.poll_flag:
            t0 = time.time()
            self.q.put(self.query_all(), block=True, timeout=10)  # note 10s
            t_total = time.time() - t0
            if t_total < self.sample_rate:
                time.sleep(self.sample_rate - t_total)

    def poll_print_queue(self):
        """Poll the sensors at regular intervals using the queue and
        print to terminal.  Unless something goes wrong, self.q should
        have at maximum 1 item in it.
        """
        self.poll_flag = True
        while self.poll_flag:
            t0 = time.time()
            self.q.put(self.query_all(), block=True, timeout=10)  # note 10s
            print(self.q.get(block=True, timeout=10))
            t_total = time.time() - t0
            if t_total < self.sample_rate:
                time.sleep(self.sample_rate - t_total)

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
