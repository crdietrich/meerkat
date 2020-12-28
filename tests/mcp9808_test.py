"""Test the MCP9808 temperature sensor"""

from meerkat import base, mcp9808

dev = mcp9808.MCP9808(bus_n=base.i2c_default_bus)

print()
print('Current MCP9808 Status:')
print('-----------------------')
dev.print_status()
print()

print('One measurement')
print('---------------')
print(dev.get_temp())
print()

print('Multiple measurements')
print('---------------------')
print(dev.get(description='test_1', n=5))
print()

print('Multiple JSON measurements')
print('--------------------------')
dev.json_writer.metadata_interval = 3
print(dev.publish(description='test_2', n=5))
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
