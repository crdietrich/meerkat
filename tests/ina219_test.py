"""Test the INA219 voltage and current sensor"""

from meerkat import base, ina219

dev = ina219.INA219(bus_n=base.i2c_default_bus, bus_addr=0x40, output='csv')

# reset all configuration settings
dev.reset()

# verbose mode prints more status info
dev.verbose = True

print()
print('Current INA219 Status')
print('---------------------')
cal = dev.get_config()
print()

print('One measurement')
print('---------------')
print(dev.get_bus_voltage(), dev.get_shunt_voltage())
print()

print('Multiple measurements')
print('---------------------')
for meas in dev.get(description='test_1', n=5):
    print(meas)
print()

print('Multiple JSON measurements')
print('--------------------------')
dev.json_writer.metadata_interval = 3
for meas in dev.publish(description='test_2', n=7):
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
dev.write(description='test_3', n=30)
print('Data written to: {}'.format(dev.json_writer.path))
print()

print('Write measurements to CSV')
print('-------------------------')
dev.writer_output = 'csv'
dev.write(description='test_4', n=30)
print('Data written to: {}'.format(dev.csv_writer.path))
"""
