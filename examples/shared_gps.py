"""Shared GPS location to multiple device data writers.

This demo requires:
    * BME680 gas sensor
    * MCP9808 temperature sensor
    * PA1010D Global Position System (GPS) receiver
"""

from meerkat import bme680
from meerkat import mcp9808
from meerkat import pa1010d

from meerkat.base import time, i2c_default_bus
from meerkat.timepiece import TimePiece

bme = bme680.BME680(bus_n=i2c_default_bus)
mcp = mcp9808.MCP9808(bus_n=i2c_default_bus)
gps = pa1010d.PA1010D(bus_n=i2c_default_bus, bus_addr=0x10)

## I. GPS timestamp two devices
tp_ex = TimePiece(time_format='gps_location')
tp_ex.gps = gps

bme.json_writer.set_time_format('gps_location', external=True)
bme.json_writer.metadata_interval = 3

mcp.json_writer.set_time_format('gps_location', external=True)
mcp.json_writer.metadata_interval = 3

## I. Setup and First Measurement
## ------------------------------
# read existing calibration
bme.read_calibration()

# Measurement steps, based on the datasheet section 3.2.1 Quickstart:
# 1. Set humidty oversample
# 2. Set temperature oversample
# 3. Set pressure oversample
bme.set_oversampling(h=1, t=2, p=16)

# 4. Set gas wait time with gas_wait_0 to 0x59 = 100ms
ms = 25
multiplier = 16
wait = bme.calc_wait_time(t=ms, x=multiplier)
print("BME wait time: {} ms".format(ms*multiplier))

bme.set_gas_wait(n=0, value=wait)

# 5. Heater set-point with res_heat_0 to 200 C
resistance = bme.calc_res_heat(target_temp=200)
bme.set_res_heat(n=0, value=resistance)

# 6. Set nb_conv to the 0 profile used in steps 4 and 5
bme.nb_conv = 0

# 7. Set run_gas to 1 to enable gas measurements
bme.gas_on()

# 8. Define shared RTC timestamp use
def shared_timestamp():
    t = tp_ex.get_time()
    bme.json_writer.set_time(t)
    mcp.json_writer.set_time(t)
    x = bme.publish()
    y = mcp.publish()
    print(x)
    print('-'*40)
    print(y)
    print('='*40)
    time.sleep(5)

# 9. define main loop

def run():
    while True:
        shared_timestamp()

# 10. start the main loop
run()
