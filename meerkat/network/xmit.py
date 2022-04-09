"""Data Transmit and Server Response Logging"""

from meerkat.base import time
from meerkat.data import Meta, CSVWriter, JSONWriter


import sys

if sys.platform == 'linux':
    import socket  # imported to keep Socket class happy - move this sometime!
    import ssl
    import requests

elif sys.platform in ['FiPy', 'pyboard', 'OpenMV3-M7']:
    import usocket
    import ussl


class Socket:
    def __init__(self):

        self.url = None
        self.scheme = None
        self.host = None
        self.path = None
        self.host_port = None
        self.host_ip_addr = None
        self.socket = None  # usocket/socket instance
        self.timeout = 20  # seconds for socket connect timeout
        self.response_retries = 5  # number of attempts to read server response
        self.verbose = False

    def url_splitter(self, url):
        """Split a URL for use in an HTTP request

        Parameters
        ----------
        url : str, URL to split

        Returns
        -------
        scheme : str, either 'http' or 'https'
        host : str, host name of the remote server
        path : str, path on remote server to request
        """

        shp = url.split('/', 3)
        scheme, _, host = shp[0:3]
        scheme = scheme.replace(':', '')
        if len(shp) == 3:
            path = '/'
        if len(shp) == 4:
            path = '/' + shp[3]
        if self.verbose:
            print('url:', url, '| split length:', len(shp), '|', scheme, '|', host, '|', path)
        return scheme, host, path

    def set_url(self, url):
        """Set the remote server URL, host, scheme, path and port

        Parameters
        ----------
        url : str, URL of remote host to connect to
        """
        self.url = url
        self.scheme, self.host, self.path = self.url_splitter(url)

        if 'https' in self.scheme:
            self.port = 443
        else:
            self.port = 80

    def get_ip_address(self):
        """Get the IP address of the remote host server"""
        t0 = time.time()
        while True:
            try:
                _addr_info = usocket.getaddrinfo(self.host, self.port)
                self.host_ip_addr = _addr_info[0][-1][0]
                self.host_port    = _addr_info[0][-1][1]
                return
            except OSError:
                dt = time.time() - t0
                if dt > self.timeout:
                    print('Timeout on socket.connect OSError')
                    break
                print('waiting to retry...')
                time.sleep(1)
                continue

    def connect(self):
        """Create a socket connection to the remote host server"""


        t0 = time.time()
        while True:
            try:
                self.socket = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)
                if self.port == 443:
                    self.socket = ussl.wrap_socket(self.socket)
                self.socket.connect((self.host_ip_addr, self.host_port))
                return
            except OSError:
                dt = time.time() - t0
                if dt > self.timeout:
                    print('Timeout on socket.connect OSError')
                    break
                print('waiting to retry...')
                time.sleep(1)
                continue

        # if all else fails
        #print('>> RESTARTING DEVICE <<')
        #import machine
        #machine.reset()

    def send(self, request_text):
        """Send HTTP/HTTPS request"""
        if self.verbose:
            print('Connection Parameters')
            print('---------------------')
            print('url: ' + self.url + '\n' +
                  'port: ' + str(self.port) + '\n' +
                  'scheme: ' + self.scheme + '\n' +
                  'host: ' + self.host + '\n' +
                  'path: ' + self.path + '\n' +
                  'ip_address: ' + str(self.host_ip_addr) + '\n' +
                  'socket: ' + '\n')
            print('-----[Begin %s Request]-----' % self.scheme)
            print(request_text)
            print('-----[End %s Request]-----' % self.scheme)

        t0 = time.time()
        while True:
            try:
                self.socket.send(request_text)
                break
            except OSError:
                dt = time.time() - t0
                if dt > self.timeout:
                    return
                time.sleep(1)
                continue

        if self.verbose:
            print('-----[Begin %s Response]-----' % self.scheme)

        response_attempt = 1
        response_data = ''
        while True:
            try:
                response_chunk = self.socket.recv(1024)
            except OSError:
                if response_attempt >= self.response_retries:
                    print('Socket Response failed after %s tries' % self.response_retries)
                    return 'filler no_reply filler'
                else:
                    response_attempt += 1
                continue

            response_chunk = str(response_chunk, "utf8")

            if response_chunk != '':
                response_data = response_data + response_chunk
                if self.verbose:
                    print(response_chunk, end="")
            else:
                if self.verbose:
                    print('\n-----[End %s Response]-----' % self.scheme)
                break
        self.close()
        return response_data

    def get(self, url):
        """Get data from a remote server set in self.url

        Parameters
        ----------
        url : str, URL of remote server to send HTTP GET request to
        """

        self.set_url(url)
        self.get_ip_address()
        self.connect()
        request_text = bytes("GET %s HTTP/1.1\r\nHost: %s\r\nConnection: close\r\n\r\n" % (self.path, self.host), "utf8")
        return self.send(request_text)

    def post(self, url, data):
        """Post data remote server set in self.url

        Parameters
        ----------
        data : str, data to send
        """
        self.set_url(url)
        self.get_ip_address()
        self.connect()
        data_length = len(data)

        request_text = ("POST %s HTTP/1.1\r\n" +
                        "Host: %s\r\n" +
                        "Content-Length: %s\r\n" +
                        "Connection: close\r\n" +
                        "\r\n" +
                        "%s") % (self.path, self.host, data_length, data)
        return self.send(request_text)

    def close(self):
        self.socket.close()
        if self.verbose:
            print("Socket closed.")


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

        # wifi or ethernet connection - in case it needs resetting
        # TODO: decide if the network connection should be reset in this class
        #self.nework_connection = network_connection

        # information about this connection
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

        self.verbose = False

        # network connection
        self.sock = None
        self.url = None
        self.retries = 3
        self.auto_connect = False  # open and close socket for each send

        # response data buffers
        self._response = Ring()
        self._label = Ring()
        self._response_timestamp = Ring()

        # platform support
        if sys.platform == 'linux':
            self.platform = 'linux'
        elif sys.platform in ['FiPy', 'pyboard', 'OpenMV3-M7']:
            self.platform = 'upython'
            self.sock = Socket()

    def send(self, data, timestamp, desc):

        retry_counter = self.retries
        socket_resets = 3

        if self.platform == 'upython':
            self.sock.verbose = self.verbose
            if self.auto_connect:
                self.sock.connect()

        for sr in range(socket_resets):
            ok = False
            for retry_counter in range(self.retries):
                try:
                    if self.platform == 'linux':
                        post_response = requests.post(self.url, data)
                        status_code = post_response.status_code
                        post_response = post_response.text
                    elif self.platform == 'upython':
                        post_response = self.sock.post(self.url, data)
                        status_code = self.response_parser(post_response)
                    if self.verbose:
                        print('='*40)
                        print(post_response)
                        print('='*40)
                    ok = True
                    break
                except:
                    ok = False
                    retry_counter -= 1
                    time.sleep(1)
            if ok:
                break
            else:
                time.sleep(5)

        if not ok:
            if self.platform == 'upython':
                self.sock.close()
                time.sleep(5)
            if self.platform == 'upython':
                self.sock.connect()
            status_code = '090 - send error'

        self._response.append(status_code)
        self._response_timestamp.append(timestamp)
        self._label.append(desc)

        if (self.platform == 'upython') & self.auto_connect:
            self.sock.close()

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


    def get(self, description='NA'):

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


class SenderLinux(Sender):
    def __init__(self, output='json', name='transmit_log', sensor_id='network_log'):
        super().__init__(output, name, sensor_id)

    def send(self, data, timestamp, desc):
        retry_counter = self.retries
        socket_resets = 3

        self.sock.verbose = self.verbose

        for sr in range(socket_resets):
            ok = False
            for retry_counter in range(self.retries):
                try:
                    post_response = requests.post(self.url, data)
                    if self.verbose:
                        print('='*40)
                        print(post_response)
                        print('='*40)
                    status_code = post_response.response_code
                    ok = True
                    break
                except:
                    ok = False
                    retry_counter -= 1
                    time.sleep(1)

            if not ok:
                time.sleep(5)

        if not ok:
            status_code = '090 - send error'

        self._response.append(status_code)
        self._response_timestamp.append(timestamp)
        self._label.append(desc)

        if self.auto_connect:
            self.sock.close()



class SenderMicroPython(Sender):
    def __init__(self, output='json', name='transmit_log', sensor_id='network_log'):
        super().__init__(output, name, sensor_id)

    def send(self, data, timestamp, desc):
        retry_counter = self.retries
        socket_resets = 3

        self.sock.verbose = self.verbose

        if self.auto_connect:
            self.sock.connect()

        for sr in range(socket_resets):
            ok = False
            for retry_counter in range(self.retries):
                try:
                    post_response = self.sock.post(self.url, data)
                    if self.verbose:
                        print('='*40)
                        print(post_response)
                        print('='*40)
                    status_code = self.response_parser(post_response)
                    ok = True
                    break
                except:
                    ok = False
                    retry_counter -= 1
                    time.sleep(1)

            if not ok:
                self.sock.close()
                time.sleep(5)
                self.sock.connect()

        if not ok:
            status_code = '090 - send error'

        self._response.append(status_code)
        self._response_timestamp.append(timestamp)
        self._label.append(desc)

        if self.auto_connect:
            self.sock.close()


if sys.platform == 'linux':
    Semder = SenderLinux

elif sys.platform in ['FiPy', 'pyboard', 'OpenMV3-M7']:
    Sender = SenderMicroPython
