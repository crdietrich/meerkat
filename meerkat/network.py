"""Networking Helper Classes"""

from meerkat.base import time

from network import WLAN
import pycom
import ubinascii
import machine
import usocket
import ussl

pycom.heartbeat(False)

def get_mac(verbose=False):
    mac_addr = ubinascii.hexlify(machine.unique_id(),':').decode()
    if verbose:
        print("WiPy MAC Address:", mac_addr)
    return mac_addr

class Wifi:
    def __init__(self):

        self.wlan = WLAN(mode=WLAN.STA, antenna=WLAN.INT_ANT)
        time.sleep(2)  # give it chance to initialize

        self.scan_results = None
        self.ssid_list = None
        self.connect_timeout = 3  # seconds
        self.antenna = WLAN.INT_ANT

        self.ssid = None
        self.bssid = None
        self.rssi = None
        self.wifi_channel = None
        self.key = None

        self.verbose = False

    def scan(self):
        self.scan_results = self.wlan.scan()
        if self.verbose:
            print('Found SSIDs:', self.scan_results)
            print('Known wifi:', self.ssid_list)
        _ssid_list = [x[0] for x in self.ssid_list]
        found_aps = [n for n in self.scan_results if n.ssid in _ssid_list]
        if len(found_aps) == 0:
            if self.verbose:
                print('No known SSIDs found')
            return None
        if self.verbose:
            print('Found known SSIDs:', found_aps)
        strongest_ap = found_aps[0]

        self.ssid = strongest_ap.ssid
        self.bssid = strongest_ap.bssid
        self.rssi = strongest_ap.rssi
        self.channel = strongest_ap.channel
        self.key = dict(self.ssid_list)[self.ssid]

        return self.ssid, self.bssid

    def connect(self):

        def _connect(_round):
            self.wlan.connect(ssid=self.ssid, bssid=self.bssid,
                              auth=(WLAN.WPA2, self.key))

            t0 = time.time()
            while not self.wlan.isconnected():
                machine.idle()

                if time.time() - t0 > self.connect_timeout:
                    return False

                if self.verbose:
                    print(_round, time.time())
            return True

        round = 0
        connected = False
        while not connected:
            round += 1
            connected = _connect(round)

        if self.verbose:
            print("WiFi connected succesfully")
            print(self.wlan.ifconfig())
        pycom.rgbled(0x0000FF)


class Socket:
    def __init__(self):

        self.url = None
        self.scheme = None
        self.host   = None
        self.path   = None
        self.host_port = None
        self.ip_addr = None
        self.socket = None

        self.verbose = False

    def set_url(self, url):
        self.url = url
        self.scheme, _, self.host, self.path = self.url.split("/", 3)

        if 'https' in self.scheme:
            self.port = 443
        else:
            self.port = 80

    def get_ip_address(self):

        if self.verbose:
            print('Using URL:', self.url)
            print('Using host_port:', self.port)

        self.ip_addr = usocket.getaddrinfo(self.host, self.port)
        if self.verbose:
            print('self.ip_addr:', self.ip_addr)

        self.host_port = self.ip_addr[0][-1]
        if self.verbose:
            print("host:port:", self.host_port)

    def connect(self):
        self.socket = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)
        if self.port == 443:
            self.socket = ussl.wrap_socket(self.socket)
        self.socket.connect(self.host_port)

    def send(self, request_text):
        if self.verbose:
            print('HTTP Request\n'+'-'*16)
            print(request_text)
            print('HTTP Response\n'+'-'*13)

        self.socket.send(request_text)

        while True:
            response_data = self.socket.recv(1024)
            response_data = str(response_data, "utf8")
            if self.verbose:
                print(response_data, end="")
            if response_data == '':
                if self.verbose:
                    print('\n'+'-'*16)
                break

    def get(self):
        request_text = bytes("GET /%s HTTP/1.1\nHost: %s\nConnection: close\n\n" % (self.path, self.host), "utf8")
        self.send(request_text)

    def post(self, data):
        data_length = len(data)
        request_text = "POST /%s HTTP/1.1\nHost: %s\nConnection: close\nContent-Length: %s\n\n%s\n" % (self.path, self.host, data_length, data)
        self.send(request_text)

    def close(self):
        self.socket.close()
        if self.verbose:
            print("Socket closed.")
