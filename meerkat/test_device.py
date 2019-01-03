# -*- coding: utf-8 -*-
"""Meerkat test device for development"""
__author__ = "Colin Dietrich"
__copyright__ = "2018"
__license__ = "MIT"

from meerkat.base import Base, DeviceData


class TestDevice(Base):
    """Non-hardware test class"""
    def __init__(self, output='json'):

        # TODO: make safe for MicroPython, leave here for now in Conda
        from collections import deque
        from math import sin, pi

        from meerkat.data import CSVWriter, JSONWriter

        # data bus placeholder
        self.bus = None
        self.bus_addr = None

        # what kind of data output to file
        self.output = output

        # types of verbose printing
        self.verbose = False
        self.verbose_data = False

        # thread safe deque for sharing and plotting
        self.q_maxlen = 300
        self.q = deque(maxlen=self.q_maxlen)
        self.q_prefill_zeros = False

        # realtime/stream options
        self.go = False
        self.unlimited = False
        self.max_samples = 1000

        # information about this device
        self.device = DeviceData('Software Test')
        self.device.description = 'Dummy data for software testing'
        self.device.urls = None
        self.device.manufacturer = None
        self.device.version_hw = None
        self.device.version_sw = None
        self.device.accuracy = None
        self.device.precision = None
        self.device.bus = None
        self.device.state = 'Test Not Running'
        self.device.active = False
        self.device.error = None
        self.device.dtype = None
        self.device.calibration_date = None

        # data writer
        if self.output == 'csv':
            self.writer = CSVWriter('Software Test')
            #self.writer.device = self.device.values()
        elif self.output == 'json':
            self.writer = JSONWriter('Software Test')

        self.writer.header = ['index', 'degrees', 'amplitude']
        self.writer.device = self.device.values()

        # example data of one 360 degree, -1 to 1 sine wave
        self._deg = [n for n in range(360)]
        self._amp = [sin(d * (pi/180.0)) for d in self._deg]
        self._test_data = list(zip(self._deg, self._amp))

    @staticmethod
    def _cycle(iterable):
        """Copied from Python 3.7 itertools.cycle example"""
        saved = []
        for element in iterable:
            yield element
            saved.append(element)
        while saved:
            for element in saved:
                yield element

    def run(self, delay=0, index='count'):
        """Run data collection"""

        # TODO: make safe for MicroPython, leave here for now in Conda
        from time import sleep, time, ctime

        if self.verbose:
            print('Test Started')

        # used in non-unlimited acquisition
        count = 0

        self.q.clear()

        if self.q_prefill_zeros:
            for _ in range(self.q_maxlen):
                self.q.append((0, 0))

        if index == 'time':
            def get_index():
                return time()
        elif index == 'ctime':
            def get_index():
                return ctime()
        else:
            def get_index():
                return count

        for d, a in self._cycle(self._test_data):

            if not self.go:
                if self.verbose:
                    print('Test Stopped')
                break

            self.device.state = 'Test run() method'

            i = get_index()

            data = [i, d, a]

            if self.output is not None:
                self.writer.write(data)

            q_out = self.writer.stream(data)
            self.q.append(q_out)

            if self.verbose_data:
                print(q_out)

            if not self.unlimited:
                count += 1
                if count == self.max_samples:
                    self.go = False

            sleep(delay)
