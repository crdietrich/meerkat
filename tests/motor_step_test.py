"""Test the Grove Motor Controller stepper function"""

from meerkat import motor
from meerkat.base import time

m = motor.GroveMotor(bus_n=1)
m.stop()
print("> Initially set to stopped")
print()
print("> Device Description")
print(m.device)
print()
print("> Data Output Header")
print(m.csv_writer.header)
print()
print("> Initial State")
print(m.get("test_1_init"))
print()
print("> Microstep Demo")
print("  ==============")

print("> 10001 clockwise microsteps...")
m.step_micro(1001, delay=0.0001, verbose=False)

time.sleep(1)

print("> 10001 counter-clockwise microsteps...")
m.step_micro(-1001, delay=0.0001, verbose=False)

print("> State after microsteps")
print(m.get("test_2_microsteps"))
print()
print("> Full Demo")
print("  =========")

print("> 100 clockwise full steps...")
m.step_full(100, delay=0.0001, verbose=False)

time.sleep(1)

print("> 100 counter clockwise full steps...")
m.step_full(-100, delay=0.0001, verbose=False)
print("> State after full steps")
print(m.get("test_3_full_steps"))

# this should generate a header row of JSON metadata, then csv lines of data
for n in range(4):
    print("> 100 clockwise full steps...")
    m.step_full(100, delay=0.0001, verbose=False)
    print("JSON Format:", m.publish(description="100_cw_steps_{}".format(n)))
    
    print("> 100 counter clockwise full steps...")
    m.step_full(-100, delay=0.0001, verbose=False)
    print("JSON Format:", m.publish(description="-100_cw_steps_{}".format(n)))
    print("-"*20)
    time.sleep(1)