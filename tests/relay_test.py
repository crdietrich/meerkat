# main.py -- put your code here!
import sys

from meerkat import relay
from meerkat.base import time


if sys.platform == "linux":
    i2c_bus = 1
else:
    i2c_bus = 0

r = relay.Single(i2c_bus, 0x18, "json")

print("Status: {}".format(r.get_status()))
print("---")

r.off()
print("Relay set to off")
print("Status: {}".format(r.get_status()))
print("---")
time.sleep(1)

r.on()
print("Relay set to on")
print("Status: {}".format(r.get_status()))
print("---")

# this should generate a header file of json metadata, then lines of data
for n in range(5):
    r.toggle(verbose=True)
    r.write(description="toggle {}".format(n))
    print("---")
    time.sleep(1)
