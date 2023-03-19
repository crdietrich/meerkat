"""Test the DS3221 RTC"""

from meerkat import ds3231
from meerkat.base import i2c_default_bus

rtc = ds3231.DS3231(bus_n=i2c_default_bus, bus_addr=0x68)

print()
"""
# this is optional if the time hasn't already been set
print("Saving time")
print("...")
rtc.save_time(YY=2020, MM=10, DD=14, hh=22, mm=6, ss=0, micro=0, tz=None)
"""

print('Current Time:')
print(rtc.get_time())
print('-'*40 + '\n')

print('Current Temperature in Celcius:')
print(rtc.get_temp())
print('-'*40 + '\n')

print('DS3221 RTC Metadata:')
print(rtc.json_writer._metadata)
print('-'*40 + '\n')

print('Publish JSON data:')
rtc.json_writer.metadata_interval = 3
for meas in rtc.publish(description="test_1", n=7):
    print(meas)
print('-'*40 + '\n')

"""
# uncomment to run write tests
# On PyCom or PyBoard this
# will write to the main flash drive, so
# by default this is commented out to
# preserve limited space on the drive

print("Write to RTC data to CSV file:")
rtc.write(description='test_2', n=6, delay=1)
print("data written to: ", rtc.csv_writer.path)
print("-"*40)
"""
