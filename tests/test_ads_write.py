import smbus2
import ads
from time import sleep

i2c = smbus2.SMBus(1)
dev = ads.Core(bus=i2c)
# this seems to work in Saleae Logic...
dev.get_config()
print(bin(dev.config_value))
dev.set_config()
sleep(0.1)  # a little delay to make sure write is done
dev.get_config()
print(bin(dev.config_value))
sleep(0.1)  # a little delay to make sure write is done
dev.pga('6.144')
sleep(0.1)
dev.get_config()
print(bin(dev.config_value))
sleep(0.1)  # a little delay to make sure write is done
dev.pga('4.096')
sleep(0.1)
dev.get_config()
print(bin(dev.config_value))
sleep(0.1)  # a little delay to make sure write is done
dev.pga('2.048')
sleep(0.1)
dev.get_config()
print(bin(dev.config_value))
sleep(0.1)  # a little delay to make sure write is done
dev.pga('1.024')
sleep(0.1)
dev.get_config()
print(bin(dev.config_value))
sleep(0.1)  # a little delay to make sure write is done
dev.pga('0.512')
sleep(0.1)
dev.get_config()
print(bin(dev.config_value))
sleep(0.1)  # a little delay to make sure write is done
dev.pga('0.256')
sleep(0.1)
dev.get_config()
print(bin(dev.config_value))
