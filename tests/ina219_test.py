"""Test the INA219 voltage and current sensor"""

import sys

from meerkat import ina219
from meerkat.base import time


if sys.platform == "linux":
    i2c_bus = 1
else:
    i2c_bus = 0

dev = ina219.INA219(bus_n=i2c_bus, bus_addr=0x40, output='csv')

# reset all configuration settings
dev.reset()

# verbose mode prints more status info
dev.verbose = True

print("Current INA219 Status:")
cal = dev.get_config()

print("One measurement")
print("---------------")
print(dev.get_bus_voltage(), dev.get_shunt_voltage())
print()

print("Multiple measurements")
print("---------------------")
print(dev.get(description='test_1', n=5))
print()

print("Multiple JSON measurements")
print("--------------------------")
dev.json_writer.metadata_interval = 3
print(dev.publish(description='test_2', n=5))
print()

print("Write measurements to JSON")
print("-------------------------")
dev.writer_output = 'json'
dev.write(description='test_3', n=30)
print("Data written to: {}".format(dev.json_writer.path))
print()

print("Write measurements to CSV")
print("-------------------------")
dev.writer_output = 'csv'
dev.write(description='test_4', n=30)
print("Data written to: {}".format(dev.csv_writer.path))
