# pi_INA219
Python TI INA219 current/power sensor

Requires Adafruit_GPIO for i2c access, not tested with pure python version.

Terminal usage:
```
$ python terminal.py -h
usage: terminal.py [-h] [-n NUMBER] [-i INTERVAL] [-u UNITS] [-s SAVE]
                   [-a ADDRESS] [-p PORT] [-b BAUD] [-g GRAPH]

pi_INA219 Terminal

optional arguments:
  -h, --help            show this help message and exit
  -n NUMBER, --number NUMBER
                        Number of samples to take, int for number or 'inf' for
                        an infinite / continuous collection [default: 4]
  -i INTERVAL, --interval INTERVAL
                        Time between samples in seconds [default: 1.0]
  -u UNITS, --units UNITS
                        Units to report, available: 'J', 'Wh', 'kWh' [default:
                        'J']
  -s SAVE, --save SAVE  Directory to save data to
  -a ADDRESS, --address ADDRESS
                        I2C address of INA219 on bus. [default: 0x40]
  -p PORT, --port PORT  Serial port address to open [Raspberry Pi hardware
                        port is: /dev/ttyAMA0]
  -b BAUD, --baud BAUD  Serial port baud rate in kbps
  -g GRAPH, --graph GRAPH
                        Append a simple bar plot of power to the terminal
                        output with scale fromzero to the number GRAPH in
                        Watts
```
## Terminal Use Examples

###Unlimited samples at 0.5 second interval and print to the terminal:
```
$ python terminal.py -n inf -i 0.5

INA219 Voltage, Power & Energy Measurement
Using default I2C address 0x40
Number of samples = infinity
Sample interval = 0.5 s
Energy units = J
--------------------------------------------------------------------------
   unix time s elapsed s     bus V   shunt A   power W instant J   total J
1463339655.433     0.000     1.000     0.000     0.000     0.000     0.000
1463339655.935     0.502     4.996     0.261     1.305     0.654     0.654
1463339656.438     1.005     5.000     0.252     1.260     0.633     1.287
1463339656.940     1.507     4.980     0.319     1.590     0.798     2.085
1463339657.442     2.009     4.976     0.325     1.618     0.812     2.897

```

###3 samples at 10 second interval and saved to directory /home/pi/data/:
```
$ python terminal.py -i 10 -n 3 -s /home/pi/data

INA219 Voltage, Power & Energy Measurement
Using default I2C address 0x40
Saving to: /home/pi/data/2016_05_15_19_21_02_INA219.csv
Number of samples = 3
Sample interval = 10.0 s
Samples collected in 30.0 s
Energy units = J
--------------------------------------------------------------------------
   unix time s elapsed s     bus V   shunt A   power W instant J   total J
1463340072.019     0.000     1.000     0.000     0.000     0.000     0.000
1463340082.031    10.012     4.984     0.337     1.680    16.819    16.819
1463340092.034    20.015     4.952     0.405     2.007    20.072    36.891
```
Data is saved to .csv format:
```
INA219 Voltage, Power & Energy Measurement
Using default I2C address 0x40
Saving to: /home/pi/data/2016_05_15_19_21_02_INA219.csv
Number of samples = 3
Sample interval = 10.0 s
Samples collected in 30.0 s
Energy units = J
--------------------------------------------------------------------------
unix_time_s,elapsed_time_s,bus_voltage_V,shunt_current_A,power_W,sample_energy_Jtotal_energy_J
1463340072.019,0.000,1.00000,0.00000,0.00000,0.00000,0.00000
1463340082.031,10.012,4.98400,0.33710,1.68011,16.81891,16.81891
1463340092.034,20.015,4.95200,0.40520,2.00655,20.07200,36.89091
```

###5 samples at 10 second interval using watt-hours for energy:
```
$ python terminal.py -n 5 -i 10 -u Wh

INA219 Voltage, Power & Energy Measurement
Using default I2C address 0x40
Number of samples = 5
Sample interval = 10.0 s
Samples collected in 50.0 s
Energy units = Wh
--------------------------------------------------------------------------
   unix time s elapsed s     bus V   shunt A   power Winstant Wh  total Wh
1463346048.001     0.000     1.000     0.000     0.000     0.000     0.000
1463346058.013    10.012     4.992     0.316     1.576     0.004     0.004
1463346068.025    20.024     5.004     0.270     1.349     0.004     0.008
1463346078.034    30.033     4.988     0.308     1.538     0.004     0.012
1463346088.046    40.045     4.996     0.262     1.311     0.004     0.016
```

###Default sample number, 4, at 4 Hz and graph from 0 to 1.8 W:
```
$ python terminal.py -i 0.25 -g 1.8

INA219 Voltage, Power & Energy Measurement
Using default I2C address 0x40
Number of samples = 4
Sample interval = 0.25 s
Samples collected in 1.0 s
Energy units = J
--------------------------------------------------------------------------
   unix time s elapsed s     bus V   shunt A   power W instant J   total J
1463346562.679     0.000     1.000     0.000     0.000     0.000     0.000 |
1463346562.931     0.252     5.000     0.268     1.339     0.335     0.335 | ====
1463346563.183     0.504     5.000     0.266     1.329     0.335     0.670 | ====
1463346563.435     0.756     4.980     0.321     1.599     0.403     1.073 | =======
```

###Measurement when a line of data is read from the serial port:
```
$ python terminal.py -p /dev/ttyAMA0 -b 9600

INA219 Voltage, Power & Energy Measurement
Using default I2C address 0x40
Serial port open: /dev/ttyAMA0 @ 9600 kbps
Number of samples = 4
Sample interval = as received from serial port
Energy units = J
--------------------------------------------------------------------------
   unix time s elapsed s     bus V   shunt A   power W instant J   total J
1463354221.460     0.000     1.000     0.000     0.000     0.000     0.000 || Arduino>>8
1463354221.711     0.252     5.004     0.281     1.405     0.352     0.352 || Arduino>>9
1463354221.962     0.502     5.004     0.268     1.342     0.336     0.688 || Arduino>>0
1463354222.212     0.753     4.992     0.264     1.318     0.330     1.018 || Arduino>>1
```
Using ArduinoSerialCounter.ino on an Arduino Mega 2560 connected to a Raspberry Pi on Serial1.

###Measurement when a line of data is read from the serial port and graph from 0 to 1.8 W:
```
$ python terminal.py -p /dev/ttyAMA0 -b 9600 -g 1.8

INA219 Voltage, Power & Energy Measurement
Using default I2C address 0x40
Serial port open: /dev/ttyAMA0 @ 9600 kbps
Number of samples = 4
Sample interval = as received from serial port
Energy units = J
--------------------------------------------------------------------------
   unix time s elapsed s     bus V   shunt A   power W instant J   total J
1463356311.459     0.000     1.000     0.000     0.000     0.000     0.000 |            || Arduino>>0
1463356311.711     0.252     4.996     0.278     1.389     0.348     0.348 | ====       || Arduino>>1
1463356311.961     0.502     4.996     0.278     1.387     0.348     0.696 | ====       || Arduino>>2
1463356312.212     0.753     5.004     0.268     1.341     0.336     1.032 | ====       || Arduino>>3
```

