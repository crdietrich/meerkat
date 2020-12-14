"""Test the PA1010d GPS unit"""

import sys

from meerkat import pa1010d

if sys.platform == "linux":
    i2c_bus = 1
else:
    i2c_bus = 0

gps = pa1010d.PA1010D(bus_n=i2c_bus, bus_addr=0x10)

print("GPS Metadata")
print("-"*40)
print(gps.csv_writer.metadata)

print("Get one of each NMEA sentence type:")
print("-"*40)
print(gps.get())

print("Get a subset of NMEA sentences, 'GSV', 'RMC' & 'VTG':")
print("-"*40)
print(gps.get(nmea_sentences=['GSV', 'RMC', 'VTG']))

print("Write to GPS data to CSV file")
print("-"*40)
gps.write(description="test_1", n=4, nmea_sentences=['GGA', 'GSA'], delay=1)
print("data written to: ", gps.csv_writer.path)
