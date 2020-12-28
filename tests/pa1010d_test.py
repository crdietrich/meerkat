"""Test the PA1010d GPS unit"""

from meerkat import pa1010d
from meerkat.base import i2c_default_bus

gps = pa1010d.PA1010D(bus_n=i2c_default_bus, bus_addr=0x10)

print()
print('GPS Metadata')
print('------------')
print(gps.metadata)
print()

print('Get one of each NMEA sentence type')
print('----------------------------------')
for meas in gps.get():
    print(meas)
print()

print("Get a subset of NMEA sentences, 'GSV', 'RMC' & 'VTG' ")
print('----------------------------------------------------')
for meas in gps.get(nmea_sentences=['GSV', 'RMC', 'VTG']):
    print(meas)
print()

"""
# uncomment to run write tests
# On PyCom or PyBoard this
# will write to the main flash drive, so 
# by default this is commented out to
# preserve limited space on the drive

print('Write to GPS data to CSV file')
print('-----------------------------')
gps.write(description='test_1', n=4, nmea_sentences=['GGA', 'GSA'], delay=1)
print('data written to: ', gps.csv_writer.path)
"""
