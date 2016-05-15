# pi_INA219
Python TI INA219 current/power sensor

Requires Adafruit_GPIO for i2c access, not tested with pure python version.

Basic terminal use:
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
# Terminal Use Examples

Collect unlimited samples at 0.5 second interval and print to the terminal:
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

Collect 3 samples at 10 second interval and save to directory /home/pi/data/:
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



