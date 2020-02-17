"""Test the ADS1115 Analog to Digitial Converter"""

import sys

from meerkat import ads
from meerkat.base import time


if sys.platform == "linux":
    i2c_bus = 1
else:
    i2c_bus = 0

dev = ads.ADS1115(bus_n=1)

dev.pga('6.144')  # Other options: '6.144', '4.096'
dev.mux('1G')     # pin 0 relative to ground

dev.print_attributes()

print("Multiple measurements")
print("---------------------")
print(dev.get(description='test_1', n=5))
print()

# lower metadata interval from a default of once every 10 samples
dev.json_writer.metadata_interval = 3

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