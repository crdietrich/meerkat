"""Test the MCP9808 temperature sensor"""

import sys

from meerkat import mcp9808
from meerkat.base import time


if sys.platform == "linux":
    i2c_bus = 1
else:
    i2c_bus = 0
    
dev = mcp9808.MCP9808(bus_n=i2c_bus)

print("Current MCP9808 Status:")
dev.print_status()
print()

print("One measurement")
print("---------------")
print(dev.get_temp())
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
dev.write(description='test_2', n=30)
print("Data written to: {}".format(dev.csv_writer.path))