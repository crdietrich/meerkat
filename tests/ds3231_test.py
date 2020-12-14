"""Test the DS3221 RTC"""

import sys

from meerkat import ds3231

if sys.platform == "linux":
    i2c_bus = 1
else:
    i2c_bus = 0
rtc = ds3231.DS3231(bus_n=1, bus_addr=0x68)

# this is optional if the time hasn't already been set
#print("Saving time")
#print("...")
#rtc.save_time(YY=2020, MM=10, DD=14, hh=22, mm=6, ss=0, micro=0, tz=None)

print('Current Time:')
print(rtc.get_time())
print('-'*40)

print('Current Temperature in Celcius:')
print(rtc.get_temp())
print('-'*40)

print('DS3221 RTC Metadata:')
print(rtc.json_writer.metadata)
print('-'*40)

print('Publish JSON data:')
print(rtc.publish(description="test_1", n=1))
print('-'*40)

print("Write to RTC data to CSV file:")
rtc.write(description='test_2', n=6, delay=1)
print("data written to: ", rtc.csv_writer.path)
print("-"*40)
