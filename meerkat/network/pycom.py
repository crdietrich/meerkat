"""Network Connection on MicroPython Boards

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
