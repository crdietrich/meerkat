"""Test the Qwiic Relay"""

import sys

from meerkat import relay
from meerkat.base import time


if sys.platform == "linux":
    i2c_bus = 1
else:
    i2c_bus = 0

r = relay.Single(i2c_bus, 0x18, "json")
r.json_writer.metadata_interval = 3
print("> Status: {}".format(r.get_status()))
print("-"*20)

r.off()
print("> Relay set to off")
print("> Status: {}".format(r.get_status()))
print("-"*20)
time.sleep(1)

r.on()
print("> Relay set to on")
print("> Status: {}".format(r.get_status()))
print("-"*20)

# this should generate a header file of json metadata, then lines of data
for n in range(7):
    r.toggle(verbose=True)
    r.write(description="toggle {}".format(n))
    print("List Format:", r.get(description="toggle {}".format(n)))
    print("JSON Format:", r.publish(description="toggle {}".format(n)))
    print("-"*20)
    time.sleep(1)

q = relay.Single(i2c_bus, 0x18, "csv")
# this should generate a header row of JSON metadata, then csv lines of data
for n in range(7):
    q.toggle(verbose=True)
    q.write(description="toggle {}".format(n))
    print("List Format:", q.get(description="toggle {}".format(n)))
    print("JSON Format:", q.publish(description="toggle {}".format(n)))
    print("-"*20)
    time.sleep(1)
