# main.py
# V5 - requires meerkat.network, meerkat.lte

import pycom

# tools for development work
# ls = list directly alias for os.listdir()
# dev_clean = remove .csv and .jsontxt files from flash storage
from meerkat.tools import dev_clean, ls

from meerkat import lte
from meerkat import network
#from meerkat.network import MSocket, MWifi
from meerkat.base import json, time

from meerkat import base, mcp9808

"""
## SigFox CONNECTION
"""
print('SigFox State:', pycom.sigfox_info())

## WIFI CONNECTION
"""
wifi_list = [['cloudcap', '5bbfbfaafab9a'],
             ['build-a-toaster', 'T0@st3r2020'],
             ['lodgepole', 'E9eaW2vc@w!6'],
             ['broken_top', 'X3H76i447ygr4']]

wifi = network.Wifi()
wifi.verbose = True
wifi.ssid_list = wifi_list
wifi.scan()
wifi.connect()
"""

## Connect to LTE NETWORK
lte.LTE_init(verbose=True)

# this works for uploading directly to GCS

def post_wrapper(data, verbose=True):
    socket = network.Socket()
    socket.verbose = verbose

    print('Setting URL...')
    socket.set_url(url="https://us-west4-iot-4855.cloudfunctions.net/post-test-2")

    print('Trying to get IP address for URL...')
    socket.get_ip_address()

    print('Connecting to socket...')
    socket.connect()

    # not done so next section can be executed
    print('Sending POST request...')
    data = json.dumps(data)
    socket.post(json_data)

    socket.close()

# temperature logging to GCP
mcp_temp = mcp9808.MCP9808(bus_n=base.i2c_default_bus)

while True:
    try:
        mcp_temp.json_writer.metadata_interval = 3
        json_data = mcp_temp.publish(description='uPython-wifi-2', n=1)

        print('Sending POST request...')
        post_wrapper(json_data)
        time.sleep(5*60)

    except KeyboardInterrupt:
        socket.close()
        print('Closed port cleanly!')

#lte.LTE_end()
