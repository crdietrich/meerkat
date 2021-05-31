from meerkat import bme680
from meerkat.base import time, i2c_default_bus

bme = bme680.BME680(bus_n=i2c_default_bus)

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

# 8. Set mode to 0b01 to trigger a single forced mode measurement

bme.forced_mode()
bme.measure()
t = bme.temperature()
p = bme.pressure()
h = bme.humidity()
g = bme.gas()
print("T: ", t)
print("P: ", p)
print("RH:", h)
print("Gas Resistance:", g)
print("Gas Valid:", bme._gas_valid)
print("Heat Stable:", bme._heat_stab)
print('='*40)

def run():
    while True:
        x = bme.publish()
        print(x)
        time.sleep(5)
run()
