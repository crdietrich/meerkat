"""Test the Grove Motor Controller stepper function"""

from meerkat import motor
from meerkat.base import time, i2c_default_bus

m = motor.GroveMotor(bus_n=i2c_default_bus)
m.stop()

print()
print('> Initially set to stopped')
print()
print('> Device Metadata')
print(m.metadata)
print()
print('> Data Output Header')
print(m.metadata.header)
print()
print('> Initial State')
print(m.get('test_1a_init'))
m.write('test_1b_init')
print()
print('> Stepper Demo')
print('  ============')
print()
print('> 1001 clockwise microsteps')
m.step_micro(1001, delay=0.0001, verbose=False)
print('> Get:', m.get('test_2a_microsteps'))
m.write('test_2b_microsteps')
print('> JSON: ', m.publish('test_2c_microsteps'))
time.sleep(1)
print()
print('> 1001 counter-clockwise microsteps')
m.step_micro(-1001, delay=0.0001, verbose=False)
print('> Get:', m.get('test_2d_microsteps'))
m.write('test_2e_microsteps')
print('> JSON: ', m.publish('test_2f_microsteps'))
time.sleep(1)
print()
print()
print('> 100 clockwise full steps...')
m.step_full(100, delay=0.0001, verbose=False)
print('> Get:', m.get('test_3a_full_steps'))
m.write('test_3b_microsteps')
print('> JSON: ', m.publish('test_3c_full_steps'))
time.sleep(1)
print()
print('> 100 counter clockwise full steps...')
m.step_full(-100, delay=0.0001, verbose=False)
print('> Get:', m.get('test_3d_full_steps'))
m.write('test_3e_microsteps')
print('> JSON: ', m.publish('test_3f_full_steps'))
time.sleep(1)
print()
for n in [100, 50, 10, 5, 1]:
    print('> {} clockwise full steps'.format(n))
    m.step_full(n, delay=0.0001, verbose=False)
    m.write('test_4a_{}_cw_steps'.format(n))
    print(m.publish(description='test_4a_{}_cw_steps'.format(n)))

    print('> {} counter clockwise full steps'.format(n))
    m.step_full(-1*n, delay=0.0001, verbose=False)
    m.write('test_4b_{}_cw_steps'.format(n))
    print(m.publish(description='test_4b_-{}_cw_steps'.format(n)))
    print('-'*20)
    time.sleep(1)

print()
print('All tests done.')
