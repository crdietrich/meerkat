"""Sensirion SPS30 Particulate Matter Sensor
https://www.sensirion.com/en/environmental-sensors/particulate-matter-sensors-pm25
Chapter references (chr x.x) to Datasheet version '1.0 - D1 - March 2020'

Note: Sensor requires 5v on VCC, if using a 3.3v I2C bus use a bus isolator
such as TI ISO1540. Sensor will run on 3.3v but will produce inaccurate data.

2021 Colin Dietrich"""

from meerkat import sps30
from meerkat.base import time, i2c_default_bus

sps = sps30.SPS30(bus_n=i2c_default_bus)
sps.json_writer.metadata_interval = 3

# Get product type, serial number and status
# wait between to give bus and device time to execute

# unique hex serial number
print('Serial Number:', sps.serial())
time.sleep(0.01)

# should be '00080000'
print('Product Type:', sps.product_type())
time.sleep(0.01)

# interval in seconds, default is 604800 ~= 168 hrs ~= 1 week
print('Cleaning Interval:', sps.read_cleaning_interval())
time.sleep(0.01)
# fan speed out of range, laser failure, fan failure
print('Status:', sps.status())

time.sleep(1)

# get partical values
def raw_measurement():
header = sps.metadata.header[2:]
    data = sps.measured_values_blocking()
    for h, d in zip(header, data):
        print(h, ':', d)
    print()

raw_measurement()
# demo JSON publishing

json_data = sps.publish(description='test1', n=3, delay=None, blocking=True)
print('JSON Data:')
print(json_data)
print()
print('Done!')
print('-'*40)
