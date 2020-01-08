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

print("> Clockwise full speed")

m.set_direction('cw')
m.set_speed(motor_id=1, motor_speed=255)
print(m.get("test_4a_dc_clockwise"))
m.write("test_4b_dc_clockwise")

time.sleep(2)
m.stop(motor_id=1)
print(m.get("test_4c_dc_clockwise"))
m.write("test_4d_dc_clockwise")
