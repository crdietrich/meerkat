"""Test the function of an INA219 current power measurement
chip on the i2c bus"""

import time

from ina219 import INA219

i = INA219()

print(">> Resetting configuration...\n")
i.reset()
time.sleep(0.5)  # insure time to complete

print("  Internal Register")
i.get_config()
print("  %s\n" % str(i.int_to_binary_string(i.reg_00)))

print(">> Setting to bus voltage = 16 (D13 = 0)\n")
i.set_bus_voltage_range(v=16)

print("  Internal Register")
i.get_config()
print("  %s\n" % str(i.int_to_binary_string(i.reg_00)))

print(">> Setting gain to 1, +/-40mV (D12, D11 = 00)\n")
i.set_shunt_voltage_range(gain=1)

print("  Internal Register")
i.get_config()
print("  %s\n" % str(i.int_to_binary_string(i.reg_00)))

print(">> Setting BADC to 16 samples (D10-D7 = 1100)\n")
i.set_badc(mode=16)

print("  Internal Register")
i.get_config()
print("  %s\n" % str(i.int_to_binary_string(i.reg_00)))

print(">> Setting SADC to 16 samples (D6-D3 = 1100)\n")
i.set_sadc(mode=16)

print("  Internal Register")
i.get_config()
print("  %s\n" % str(i.int_to_binary_string(i.reg_00)))

print(">> Setting Mode to Shunt Voltage Continuous (D2-D0 = 101)\n")
i.set_mode(mode=5)

print("  Internal Register")
i.get_config()
print("  %s\n" % str(i.int_to_binary_string(i.reg_00)))

print(">> Resetting configuration...\n")
i.reset()
time.sleep(0.5)  # insure time to complete

print("  Internal Register")
i.get_config()
print("  %s\n" % str(i.int_to_binary_string(i.reg_00)))

print("  Shunt Voltage")
i.get_shunt_voltage()
print("  %s mV\n" % i.shunt_voltage)

print("  Bus Voltage")
i.get_bus_voltage()
print("  %s V\n" % i.bus_voltage)

print(">> Setting to bus voltage = 16 (D13 = 0)\n")
i.set_bus_voltage_range(v=16)

print("  Bus Voltage")
i.get_bus_voltage()
print("  %s V\n" % i.bus_voltage)

print(">> Resetting configuration...\n")
i.reset()
time.sleep(0.5)  # insure time to complete

print("  Current Simple")
i.get_current_simple()
print("  %s A\n" % i.i)

print("  Power Simple")
i.get_power_simple()
print("  %s W\n" % i.p)

i.set_energy_units(units="J")
dt = 2  # seconds per delay
n = 4  # number of samples to take
print("Energy use over %s seconds at %ss interval" % (dt*n, dt))
print("------------------------------------------")
print("Assuming constant load, should be linear...")
print("time (s),power (W),sample_energy (%s),total_energy (%s)" % (i.units, i.units))
i.get_energy_simple()
t0 = time.time()
for _ in range(0, n):
    time.sleep(dt)
    i.get_energy_simple()
    t = time.time()
    t_elapsed = t - t0
    print("%s,%0.3f,%0.5f,%0.5f,%0.5f" % (t, t_elapsed, i.p, i.e, i.e_total))
