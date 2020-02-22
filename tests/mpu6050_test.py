"""Test MPU6050 Accelerometer and Gyroscope"""

import sys

from meerkat import mpu6050
from meerkat.base import time


if sys.platform == "linux":
    i2c_bus = 1
else:
    i2c_bus = 0
    
dev = mpu6050.mpu6050(bus_n=1, output='json')

dev.set_gyro_range(dev.GYRO_RANGE_1000DEG)
dev.set_accel_range(dev.ACCEL_RANGE_2G)

print("Current temperature in C:")
print(dev.get_temp())
print("-"*20)

print("Accelerometer measurement:")
print(dev.get_accel())
print("-"*20)

print("Gyroscope measurement:")
print(dev.get_gyro())
print("-"*20)

print("Temp, Accel, Gryo measurement:")
print(dev.get_all())
print("-"*20)

print("Get 5 Accel and Gryo samples:")
print(dev.get(description="test_1", n=5))
print("-"*20)

# lower metadata interval from a default of once every 10 samples
dev.json_writer.metadata_interval = 3

# writing method with description and sample number
print("Publish in JSON 5 Accel and Gryo samples:")
print(dev.publish(description='test_2', n=5))

# default writer format is CSV, switch to JSON
dev.writer_output = 'json'

print("Write data in JSON format to file.")
# writer method with description and sample number
dev.write(description='test_3', n=30)
print("...wrote data to {}".format(dev.json_writer.path))

# switch to CSV format
dev.writer_output = 'csv'

print("Write data in CSV format to file.")
# writer method with description and sample number
dev.write(description='test_3', n=30)
print("...wrote data to {}".format(dev.csv_writer.path))
