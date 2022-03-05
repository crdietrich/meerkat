"""Sensirion SCD4x CO2 sensor Examples
Chapter references (chr x.x) to Datasheet version '1.1 - April 2021'
2021 Colin Dietrich"""

from meerkat import scd4x
from meerkat.base import time

co2 = scd4x.SCD4x(bus_n=1)

print('SCD4x Serial Number:', co2.get_serial_number())
print('Single Shot Blocking Measurement:', co2.measure_single_shot_blocking())
print('-'*40)
print('JSON Output:')
print('-'*40)

for n in range(8):
    d = co2.publish(description='test1-'+str(n))
    print(d)
    time.sleep(10)
print('-'*40)
