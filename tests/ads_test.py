"""Test the ADS1115 Analog to Digitial Converter"""

from meerkat import base, ads

dev = ads.ADS1115(bus_n=base.i2c_default_bus)

dev.pga('6.144')  # Other options: '6.144', '4.096'
dev.mux('1G')     # pin 0 relative to ground

print()
dev.print_attributes()
print()

print('One measurement')
print('---------------')
print(dev.get(description='test_1'))
print()

print('Multiple measurements')
print('---------------------')
dev.mux('2G')
for meas in dev.get(description='test_2', n=5):
    print(meas)
print()

# lower metadata interval from a default of once every 10 samples
dev.json_writer.metadata_interval = 3

print('Multiple JSON measurements')
print('--------------------------')
dev.mux('3G')
dev.json_writer.metadata_interval = 3
for meas in dev.publish(description='test_3', n=7):
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
dev.mux('4G')
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
