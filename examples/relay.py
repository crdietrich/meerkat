"""Test the Qwiic Relay"""

from meerkat import relay
from meerkat.base import time, i2c_default_bus

r = relay.Single(bus_n=i2c_default_bus, bus_addr=0x19, output='json')
r.json_writer.metadata_interval = 3

print()
print('Qwiic Single Relay')
print('------------------')
print()
print('> Status: {}'.format(r.get_status()))
print('-'*20 + '\n')

r.off()
print('> Relay set to off')
print('> Status: {}'.format(r.get_status()))
print('-'*20 + '\n')
time.sleep(1)

r.on()
print('> Relay set to on')
print('> Status: {}'.format(r.get_status()))
print('-'*20 + '\n')

"""
# uncomment to run write tests
# On PyCom or PyBoard this
# will write to the main flash drive, so 
# by default this is commented out to
# preserve limited space on the drive

# this should generate a header file of json metadata, then lines of data
for n in range(7):
    r.toggle(verbose=True)
    r.write(description='toggle {}'.format(n))
    print('List Format:', r.get(description='toggle {}'.format(n)))
    print('JSON Format:', r.publish(description='toggle {}'.format(n)))
    print('-'*20 + '\n')
    time.sleep(1)

q = relay.Single(i2c_bus, 0x18, 'csv')
# this should generate a header row of JSON metadata, then csv lines of data
for n in range(7):
    q.toggle(verbose=True)
    q.write(description='toggle {}'.format(n))
    print('List Format:', q.get(description='toggle {}'.format(n)))
    print('JSON Format:', q.publish(description='toggle {}'.format(n)))
    print('-'*20 + '\n')
    time.sleep(1)
"""
