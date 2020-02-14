"""Test Atlas Scientific Conductivity Sensor"""

import sys

from meerkat import atlas
from meerkat.base import time


if sys.platform == "linux":
    i2c_bus = 1
else:
    i2c_bus = 0
    
# instance device and set output format to .csv (which is default)
dev = atlas.Conductivity(bus_n=1, output='csv')

# device information: device type, firmware version
time.sleep(0.5)
print("Device Information:")
print(dev.info())

# status of device power: restart code, input voltage Vcc
time.sleep(0.5)
print("Power Status:")
print(dev.status())

# since this is a single file, skip calibration demo
# see Jupyter Notebook and Datasheet for examples

# single conductivity measurement
print("Measurement:")
print(dev.measure())

# get 5 samples with a description
print("Five measurements:")
print(dev.get('test_2', n=5))

# set the metadata publishing interval to every third sample
dev.json_writer.metadata_interval = 3

print("Publish in JSON:")
print(dev.publish(description='test_3', n=5))

# write 5 samples to .csv file with description
print("Write CSV data to file {}".format(dev.csv_writer_path))
dev.write(description='test_4', n=5)

dev.writer_output = "json"

# get 7 samples with a description
print("Write JSON data to file {}".format(dev.json_writer_path))
dev.write(description='test_5', n=7)
