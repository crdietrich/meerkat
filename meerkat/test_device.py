"""Test device for development"""

from meerkat.base import Base, TimePiece, time
from meerkat.data import Meta, CSVWriter, JSONWriter

# TODO: make safe for MicroPython, leave here for now in Conda
from collections import deque
from math import sin, pi


class TestDevice(Base):
    """Non-hardware test class"""
    def __init__(self, bus_n, bus_addr=0x00, output='json', name='software_test'):

        # data bus placeholder
        self.bus = 'fake I2C bus object on bus {} and address {}'.format(bus_n, bus_addr)

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

        ## Metadata information about this device
        self.metadata = Meta(name=name)

        # device/source specific descriptions
        self.metadata.description  = 'dummy_data'
        
        # URL(s) for data source reference
        self.metadata.urls         = 'www.example.com'
        
        # manufacturer of device/source of data
        self.metadata.manufacturer = 'Nikola Tesla Company'
        
        ## data output descriptions
        # names of each kind of data value being recorded
        self.metadata.header       = ['description', 'sample_n', 'degree', 'amplitude']
        
        # data types (int, float, etc) for each data value
        self.metadata.dtype        = ['str', 'int', 'float', 'float']
        
        # measured units of data values
        self.metadata.units        = [None, 'count', 'degrees', 'real numbers']
        
        # accuracy in units of data values
        self.metadata.accuracy     = [None, 1, 0.2, 0.2] 
        
        # precision in units of data values
        self.metadata.precision    = [None, 1, 0.1, 0.1]
        
        # I2C bus the device is on
        self.metadata.bus_n = bus_n
        
        # I2C bus address the device is on
        self.metadata.bus_addr = bus_addr

        ## Data writers for this device
        self.writer_output = output
        self.csv_writer = CSVWriter(metadata=self.metadata, time_format='std_time_ms')
        self.json_writer = JSONWriter(metadata=self.metadata, time_format='std_time_ms')
        
        # synthetic data
        self._deg = list(range(360))
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
        """Run data collection
        
        Parameters
        ----------
        delay : int, seconds to delay between returned data
        index : str, 'count' or 'timestamp'
        """

        if self.verbose:
            print('Test Started')
            print('='*40)
            
        # used in non-unlimited acquisition
        count = 0

        self.q.clear()

        if self.q_prefill_zeros:
            for _ in range(self.q_maxlen):
                self.q.append((0, 0))

        tp = TimePiece()
                
        if index == 'timestamp':
            def get_index():
                return tp.get_time()
        else:
            def get_index():
                return count
        
        if self.writer_output is not None:
            wr = {"csv": self.csv_writer,
                  "json": self.json_writer}[self.writer_output]
            
        for d, a in self._cycle(self._test_data):

            if not self.go:
                if self.verbose:
                    print("="*40)
                    print('Test Stopped')
                break

            self.metadata.state = 'Test run() method'

            i = get_index()

            data = [self.metadata.description, i, d, a]

            if self.writer_output is not None:
                wr.write(data)

            q_out = self.json_writer.publish(data)
            self.q.append(q_out)

            if self.verbose_data:
                print(q_out)

            if not self.unlimited:
                count += 1
                if count == self.max_samples:
                    self.go = False

            time.sleep(delay)
