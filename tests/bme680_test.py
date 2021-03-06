"""Test the BME680 temperature, pressure, humidity and gas sensor"""

from meerkat import bme680
from meerkat.base import time, i2c_default_bus

dev = bme680.BME680(bus_n=i2c_default_bus)

print()
print('Setting up BME680...')
# set calibration and sensor configuration
dev.read_calibration()
dev.set_oversampling(h=1, t=2, p=16)
wait = dev.calc_wait_time(t=25, x=16)
dev.set_gas_wait(n=0, value=wait)
resistance = dev.calc_res_heat(target_temp=300)
dev.set_res_heat(n=0, value=resistance)
dev.nb_conv = 0
dev.gas_on()

print('One measurement')
print('---------------')
print(dev.get(description='test_1', n=1))
print()

print('Multiple measurements')
print('---------------------')
for meas in dev.get(description='test_2', n=5):
    print(meas)
print()

print('Multiple JSON measurements')
print('--------------------------')
dev.json_writer.metadata_interval = 3
for meas in dev.publish(description='test_3', n=5):
    print(meas)
print()

"""
# uncomment to run write tests
# On PyCom or PyBoard this
# will write to the main flash drive, so 
# by default this is commented out to
# preserve limited space on the drive
print('Write measurements to JSON')
print('-------------------------')
dev.writer_output = 'json'
dev.write(description='test_4', n=7)
print('Data written to: {}'.format(dev.json_writer.path))
print()

print('Write measurements to CSV')
print('-------------------------')
dev.writer_output = 'csv'
dev.write(description='test_5', n=7)
print('Data written to: {}'.format(dev.csv_writer.path))
"""
"""
# longer time test
dev.writer_output = 'csv'
hrs = 1
seconds = hrs * 60 * 60 / 5
dev.write(description='12hr_test', n=seconds, delay=5)
print('12hr data written to: {}'.format(dev.csv_writer.path))
"""