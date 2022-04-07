"""Networking Helper Classes

Reference
---------
https://docs.micropython.org/en/latest/esp8266/tutorial/network_tcp.html#http-get-request

Example usage
-------------

wifi = net.Wifi()
wifi.select_ap(wifi_ssid, wifi_password)
wifi.verbose = True  # optional debug statements
wifi.connect()

sock = net.Socket()
# sock.verbose = True  # optional debug statements
response_data = sock.get(url=server_url)
print(response_data)
"""

from network import WLAN
import pycom
import ubinascii
import machine
import usocket
import ussl

from meerkat.base import time
from meerkat.data import Meta, CSVWriter, JSONWriter


pycom.heartbeat(False)

def get_mac(verbose=False):
    mac_addr = ubinascii.hexlify(machine.unique_id(),':').decode()
    if verbose:
        print("WiPy MAC Address:", mac_addr)
    return mac_addr

class Wifi:
    def __init__(self):

        self.wlan = WLAN(mode=WLAN.STA, antenna=WLAN.INT_ANT)

        # TODO: check if these are available with a newer version of MicroPython
        #self.wlan.hostname = 'pycom_fipy_02'
        #self.wlan.max_tx_power([78])

        self.antenna = WLAN.INT_ANT

        self.ssid = None
        self.bssid = None
        self.rssi = None
        self.wifi_channel = None
        self.key = None

        self.scan_results = None
        self.verbose = False

    def scan(self, verbose=True):
        self.scan_results = self.wlan.scan()

        sec_mapper = {0: 'open', 1: 'WEP',
            2: 'WPA-PSK', 3: 'WPA2-PSK', 4: 'WPA/WPA2-PSK'}

        if verbose:
            print('Found SSID Name     Auth           Ch   RSSI')
            print('-'*44)
            for nx in self.scan_results:
                _sec = sec_mapper[nx.sec]   # security
                _channel = str(nx.channel)  # transmission channel
                _rssi    = str(nx.rssi)     # received signal strength indicator
                print(nx.ssid  + (20 - len(nx.ssid))  * ' ' +
                      _sec     + (15 - len(_sec))     * ' ' +
                      _channel + (5  - len(_channel)) * ' ' +
                      _rssi    + (5  - len(_rssi))    * ' ')

    def select_ap(self, ssid, key, verbose=False):
        """Find the access point with highest signal strength and

        Parameters
        ----------
        ssid : str, network SSID to connect to if present
        key : str, WPA2 passkey to connect to ssid
        """

        self.scan(verbose=verbose)

        # scan results are ordered by highest strength signal first
        for n in self.scan_results:
            if n.ssid == ssid:
                self.ssid    = n.ssid
                self.bssid   = n.bssid
                self.rssi    = n.rssi
                self.channel = n.channel
                self.key     = key
                if verbose:
                    print('Found known SSIDs:', found_aps)
                return self.ssid, self.bssid
        if verbose:
            print('No known SSID found')

    def connect(self, retries=4, timeout=20):
        """Connect to a Wireless Network.

        Parameters
        ----------
        retries : int, number of times to try connecting
        timeout : int, time in seconds to wait each attempt
        """

        if self.verbose:
            print('Attempting connection to SSID:', self.ssid)

        if self.wlan.isconnected():
            if self.verbose:
                print('Wifi is already connected.')
            return True

        connection_attempt = 1
        while connection_attempt < retries:

            print('Connection attempt: ', connection_attempt)

            self.wlan.connect(ssid=self.ssid, bssid=self.bssid,
                              auth=(WLAN.WPA2, self.key))

            t0 = time.time()
            while True:
                dt = time.time() - t0

                if dt > timeout:
                    connection_attempt += 1
                    break

                if self.wlan.isconnected():
                    return True

                if self.verbose:
                    print('WLAN connect attempt:', connection_attempt)
                    print('Time elapsed:', dt)
                    # ifconfig = (IP address, subnet mask, gateway, DNS server)
                    _ifconfig = self.wlan.ifconfig()
                    print('DNS Server: ', _ifconfig[3])
                time.sleep(2)

            return False
        pycom.rgbled(0x0000FF)

    def status(self):
        """Print the current wireless network status"""
        print('Wifi Status:')
        print(self.wlan.ifconfig())

    def reset(self, delay=5):
        """Reset the Wifi connection

        Parameters
        ----------
        delay : int, seconds to wait before reconnecting
        """

        self.wlan.deinit()
        time.sleep(delay)
        self.connect()


class Socket:
    def __init__(self):

        self.url = None
        self.scheme = None
        self.host = None
        self.path = None
        self.host_port = None
        self.host_ip_addr = None
        self.socket = None  # usocket instance
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
        _addr_info = usocket.getaddrinfo(self.host, self.port)
        self.host_ip_addr = _addr_info[0][-1][0]
        self.host_port    = _addr_info[0][-1][1]

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

class Log:

    def __init__(self, output='json', name='transmit_log'):
        # information about this device
        self.metadata = Meta(name=name)
        self.metadata.description = 'Network Transmit Log'
        self.metadata.urls = None
        self.metadata.manufacturer = None

        self.metadata.header = ["description", "state"]
        self.metadata.dtype = ['str', 'str']
        self.metadata.units = None
        self.metadata.accuracy = None
        self.metadata.precision = None

        self.metadata.bus_n = None
        self.metadata.bus_addr = None

        # data recording method
        self.writer_output = output
        self.csv_writer = CSVWriter(metadata=self.metadata, time_source='std_time_ms')
        self.json_writer = JSONWriter(metadata=self.metadata, time_source='std_time_ms')
