"""Data Transmit and Server Response Logging"""

from meerkat.base import time
from meerkat.data import Meta, CSVWriter, JSONWriter
from meerkat import network

class Ring:
    def __init__(self):
        self.len = 10
        self.values = [None] * self.len
        self.p = 0

    def append(self, value):
        self.values[self.p] = value
        if self.p == self.len - 1:
            self.p = 0
        else:
            self.p += 1


class Sender:
    def __init__(self, output='json', name='transmit_log', sensor_id='network_log'):
        # information about this device
        self.metadata = Meta(name=name)
        self.metadata.description = 'Network Transmit Server Response Log'
        self.metadata.urls = None
        self.metadata.manufacturer = None

        self.metadata.header = ['system_id', 'sensor_id', 'response_timestamp', 'label', 'response']
        self.metadata.dtype  = ['str',       'str',       'list',               'list',  'list']
        self.metadata.units = None
        self.metadata.accuracy = None
        self.metadata.precision = None

        self.metadata.bus_n = None
        self.metadata.bus_addr = None

        # data recording information
        self.system_id = None
        self.sensor_id = sensor_id

        self.writer_output = output
        self.csv_writer = CSVWriter(metadata=self.metadata, time_source='std_time_ms')
        self.json_writer = JSONWriter(metadata=self.metadata, time_source='std_time_ms')

        # network connection
        self.sock = network.Socket()
        self.url = None
        self.retries = 3

        # response data buffers
        self._response = Ring()
        self._label = Ring()
        self._response_timestamp = Ring()

        self.verbose = False

    @property
    def response(self):
        return self._response.values

    @property
    def label(self):
        return self._label.values

    @property
    def response_timestamp(self):
        return self._response_timestamp.values

    def response_parser(self, response):
        if response is None:
            return 'NR'
        status = response.split('\n')[0]
        status_code = status.split(' ')[1]
        return status_code

    def send(self, data, timestamp, desc):
        retry_counter = self.retries
        while retry_counter >= 0:
            try:
                post_response = self.sock.post(self.url, data)
                if self.verbose:
                    print('='*40)
                    print(post_response)
                    print('='*40)
                status_code = self.response_parser(post_response)
                break
            except:
                status_code = '090 - send error'
                retry_counter -= 1
                time.sleep(1)

        self._response.append(status_code)
        self._response_timestamp.append(timestamp)
        self._label.append(desc)

    def get(self, description='NA'):
#        data = [list(x) for x in zip(self.timestamp,
#                                     self.label,
#                                     self.response) if x[0] is not None]

        data = [self.system_id,
                self.sensor_id,
                [_x for _x in self.response_timestamp if _x],
                [_x for _x in self.label if _x],
                [_x for _x in self.response if _x]]

        return data

    def publish(self):
        return self.json_writer.publish(data=self.get())

    def get_log(self):
        return ' '.join(map(str, self.response))

    def get_label(self):
        return ' '.join(map(str, self.label))

    def get_response_timestamp(self):
        return ' '.join(map(str, self.timestamp))
