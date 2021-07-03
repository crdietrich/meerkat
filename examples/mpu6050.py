"""Test MPU6050 Accelerometer and Gyroscope"""

from meerkat import mpu6050
from meerkat.base import i2c_default_bus

dev = mpu6050.mpu6050(bus_n=i2c_default_bus, output='json')

dev.set_gyro_range(dev.GYRO_RANGE_1000DEG)
dev.set_accel_range(dev.ACCEL_RANGE_2G)

print('MPU650 Accelerometer & Gyroscope')
print('--------------------------------')
print()

print('Current temperature in degrees Celsius')
print('--------------------------------------')
print(dev.get_temp())
print()

print('Accelerometer measurement')
print('-------------------------')
print(dev.get_accel())
print()

print('Gyroscope measurement')
print('---------------------')
print(dev.get_gyro())
print()

print('Temp, Accel, Gryo measurement')
print('-----------------------------')
print(dev.get_all())
print()

print('Get 5 Accel and Gryo samples')
print('----------------------------')
for meas in dev.get(description='test_1', n=7):
    print(meas)
print()

# lower metadata interval from a default of once every 10 samples
dev.json_writer.metadata_interval = 3

# JSON publishing method with description and sample number
print('Publish in JSON Accel and Gryo samples')
print('----------------------------------------')
for meas in dev.publish(description='test_2', n=7):
    print(meas)
    print()

"""
# uncomment to run write tests
# On PyCom or PyBoard this
# will write to the main flash drive, so 
# by default this is commented out to
# preserve limited space on the drive

# default writer format is CSV, switch to JSON
dev.writer_output = 'json'

print('Write data in JSON format to file')
print('---------------------------------')
# writer method with description and sample number
dev.write(description='test_3', n=30)
print('...wrote data to {}'.format(dev.json_writer.path))

# switch to CSV format
dev.writer_output = 'csv'

print('Write data in CSV format to file')
print('--------------------------------')
# writer method with description and sample number
dev.write(description='test_3', n=30)
print('...wrote data to {}'.format(dev.csv_writer.path))
"""
