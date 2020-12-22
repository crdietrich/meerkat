"""Test for MCP23008 8bit I/O Expander I2C Driver for Raspberry PI & MicroPython
https://jap.hu/electronic/relay_module_i2c.html
https://www.microchip.com/wwwproducts/en/MCP23008
"""

import sys

from meerkat import mcp23008, tools
from meerkat.base import time


if sys.platform == "linux":
    i2c_bus = 1
else:
    i2c_bus = 0

relay = mcp23008.MCP23008(bus_n=1)
relay.json_writer.metadata_interval = 3

state = relay.get_all_channels()
print('Get state of all channels')
print(tools.left_fill(s=bin(state)[2:], n=8, x="0"))
print('-'*40)

'''
set_channel usage: Set a single channel On, Off or Toggle it

Parameters
----------
channel : int, 1-8 for the channel to change
state : int, where
    0 = On
    1 = Off
    2 = Toggle from last state
'''

print('Toggle channel 4')
relay.set_channel(channel=4, state=2)
state = relay.get_all_channels()
print(tools.left_fill(s=bin(state)[2:], n=8, x="0"))
print('-'*40)

print('Toggle channel 4 again')
relay.set_channel(channel=4, state=2)
state = relay.get_all_channels()
print(tools.left_fill(s=bin(state)[2:], n=8, x="0"))
print('-'*40)

print('Publish current relay state')
print(relay.publish(description="relay_test1"))
print('-'*40)

# switch back to CSV format
relay.writer_output = 'csv'
relay.csv_writer.description = "driver_demo"

relay.set_all_channels(state=0b11111111)
for n in range(1,9):
    print("Toggling channel:", n)
    relay.set_channel(channel=n, state=1)
    relay.write(description="channel_ramp_test_1")
    time.sleep(0.25)
    relay.set_channel(channel=n, state=0)
    relay.write(description="channel_ramp_test_1")
    time.sleep(0.25)
    relay.write(description="channel_ramp_test_1")
    time.sleep(0.25)
    relay.set_channel(channel=n, state=1)
    relay.write(description="channel_ramp_test_1")
    time.sleep(0.25)

print('Data written to:')
print(relay.csv_writer.path)
