#!/usr/bin/python
"""Atlas Scientific sensor reading using i2c bus on
Raspberry Pi
Colin Dietrich 2015
"""

import atlas_rpi_i2c


# instance i2c bus controller classes
do = atlas_rpi_i2c.atlas_i2c(address=0x61, bus=0)
ph = atlas_rpi_i2c.atlas_i2c(address=0x63, bus=0)
ec = atlas_rpi_i2c.atlas_i2c(address=0x64, bus=0)

# test of each sensor on the bus
for command in ["I", "STATUS"]:
    print("do>> " + do.query(command))
    print("ph>> " + ph.query(command))
    print("ec>> " + ec.query(command))
