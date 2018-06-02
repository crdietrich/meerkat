import os
import sys
import smbus
from time import sleep
from datetime import datetime

# get current working directory and append to path for package import
p = os.path.dirname(__file__)
p = os.path.join(p, '..')
p = os.path.abspath(p)
print('Appending directory to path:', p)
sys.path.insert(0, p)

from meerkat import ads

i2c = smbus.SMBus(1)
dev = ads.ADS1115(bus=i2c)
dev.get_config()
dev.pga('4.096')  # Other options: '6.144', '4.096'
dev.mux('0G')     # pin 0 relative to ground
dev.get_config()  # refresh for measurements

# print to terminal status
dev.print_attributes()

def get_time():
    """Helper function to get formatted time"""
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')

# print to terminal test
print('Measured voltage: {}'.format(dev.measure()))
print(dev.data.writer.create_metadata())
print(dev.data.writer.header)
print(dev.get(t=get_time(), sid='test'))

# file saving test
dev.data.writer.path = 'test.csv'
for _ in range(10):
    dev.write(t=get_time(), sid='test_' + str(_))

