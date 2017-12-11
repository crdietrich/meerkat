import smbus2
from time import sleep

from meerkat import ads

i2c = smbus2.SMBus(1)
dev = ads.Core(bus=i2c)
dev.get_config()
#dev.pga('6.144')
#dev.pga('4.096')
dev.pga('2.048')
dev.mux('0G')
dev.get_config()  # refresh for measurements
dev.print_attributes()
v = dev.measure()
print(v)
