"""Test the Grove Motor Controller stepper function"""

from meerkat import motor
from meerkat.base import time

m = motor.GroveMotor(bus_n=1)
m.stop()
print("> Initially set to stopped")
print()

m.set_mode(mode_type="dc")
m.set_frequency(f_Hz=31372)

print("> Device Description")
print(m.device)
print()
print("> Data Output Header")
print(m.csv_writer.header)
print()
print("> Initial State")
print(m.get("test_1_init"))
print()
print("> DC Motor Demo")
print("  =============")

print("> Full speed Clockwise and Counter Clockwise")

for d in ["cw", "ccw"]:
    m.set_direction(d)
    m.set_speed(motor_id=1, motor_speed=255)
    print(m.get("test_5a_dc_{}".format(d)))
    m.write("test_5b_dc_{}".format(d))
    print(m.publish("test_5c_dc_{}".format(d)))
    time.sleep(2)

    m.stop(motor_id=1)
    print(m.get("test_5d_dc_{}".format(d)))
    m.write("test_5e_dc_{}".format(d))
    print(m.publish("test_5f_dc_{}".format(d)))

m.stop()
time.sleep(0.5)
print("> Ramp up motor speed Clockwise")
for speed in range(0, 255, 25):
    m.set_speed(motor_id=1, motor_speed=speed)
    print("> State after motor speed set to {}".format(speed))
    desc = "test_6_{}".format(speed)
    m.write(description=desc)
    print("JSON Format:", m.publish(description=desc))
    time.sleep(0.25)
m.stop()

print()
print("All tests done.")
print("Data saved to file: {}".format(m.csv_writer.path))