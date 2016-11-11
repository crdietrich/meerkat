"""Base Meerkat classes"""

import ujson

class Device(object):

    def __init__(self, name):

        # required
        self.data = Data(name)

        # optional
        self.description = None
        self.urls = None

        self.state = None
        self.active = None
        self.error = None
        self.name = None
        self.description = None
        self.bus = None
        self.manufacturer = None
        self.version_hw = None
        self.version_sw = None
        self.accuracy = None
        self.precision = None
        self.calibration_date = None


class Data(object):

    def __init__(self, name):
        # required
        self.name = name
        self.datetime = None
        self.lat = None
        self.lon = None
        self.payload = None

    def dumps(self):
        if self.payload is not None:
            return ujson.dumps(self.payload)

    def loads(self):
        print(ujson.loads(self.payload))