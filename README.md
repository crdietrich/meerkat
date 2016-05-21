# pyINA219

A Python class for accessing the TI INA219 current/power sensor via i2c.

Need to know how much power your project consumes?  Tracking energy use is important for many small projects and especially battery powered ones.  The TI INA219 provides a simple package to track consumption, this package provides tools to get the bus voltage, current, power and energy use over time.

Measurements are made when polled and stored locally, energy measurements are the latest power measurement multiplied by the time since the last measurement.  In that respect it is a Right Integration, higher accuracy is achieved by increased sample number.  The target use case sample rates are probably 10Hz and below.

```
Python 2.7.3 (default, Mar 18 2014, 05:13:23)
>>> from ina219 import INA219
>>> device = INA219()
>>> device.get_energy_simple()
>>> device.bus_voltage
4.984
>>> device.bus_voltage, device.i, device.p  # Volts, Amps, Watts
(4.984, 0.2855, 1.4229319999999999)
>>> device.units  # Units of energy reported
'J'
>>> device.e  # energy consumed since last measurement
0
>>> device.get_energy_simple()
>>> device.e
94.7875849419462
>>> device.e_total
94.7875849419462
>>> device.get_energy_simple()
>>> device.e
41.283171379789536
>>> device.e_total
136.07075632173576
```

A command line script is available for stand alone power profiling via shell or ssh, with all measurements time stamped with the system local time.  See below for examples.

Details:

- Tested with RaspberryPi, default Python 2.7 in Raspbian Wheezy
- Requires Adafruit_GPIO for i2c access, not tested with their pure python version

Possible extensions:

- Chip power calculation
- Beaglebone support/testing
- Wipy or similar MicroPython support/testing

*Extra Warning:*

*This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  This code should not be used in any life-critical systems.*


## Terminal Use Examples

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

#### Unlimited samples at 0.5 second interval and print to the terminal:
```
$ python terminal.py -n inf -i 0.5

INA219 Voltage, Power & Energy Measurement
Using default I2C address 0x40
Number of samples = infinity
Sample interval = 0.5 s
Energy units = J
--------------------------------------------------------------------------
   unix time s elapsed s     bus V   shunt A   power W  energy J   total J
1463846421.602     0.000     4.984     0.325     1.618     0.000     0.000
1463846422.104     0.502     4.948     0.383     1.894     0.951     0.951
1463846422.607     1.005     4.988     0.310     1.545     0.776     1.728
1463846423.109     1.507     4.976     0.316     1.571     0.789     2.517
1463846423.611     2.010     4.996     0.264     1.318     0.662     3.179
1463846424.113     2.512     5.000     0.267     1.334     0.670     3.849
1463846424.616     3.014     4.996     0.264     1.321     0.663     4.512
...
```

#### 3 samples at 10 second interval and saved to directory /home/pi/data/:
```
 $ python terminal.py -i 10 -n 3 -s /home/pi/data

INA219 Voltage, Power & Energy Measurement
Using default I2C address 0x40
Saving to: /home/pi/data/2016_05_21_16_02_34_INA219.csv
Number of samples = 3
Sample interval = 10.0 s
Samples collected in 30.0 s
Energy units = J
--------------------------------------------------------------------------
   unix time s elapsed s     bus V   shunt A   power W  energy J   total J
1463846564.537     0.000     4.984     0.305     1.520     0.000     0.000
1463846574.549    10.012     4.996     0.274     1.367    13.685    13.685
1463846584.561    20.024     4.988     0.313     1.561    15.626    29.312
```
Data is saved to .csv format:
```
INA219 Voltage, Power & Energy Measurement
Using default I2C address 0x40
Saving to: /home/pi/data/2016_05_21_16_02_34_INA219.csv
Number of samples = 3
Sample interval = 10.0 s
Samples collected in 30.0 s
Energy units = J
--------------------------------------------------------------------------
unix_time_s,elapsed_time_s,bus_voltage_V,shunt_current_A,power_W,sample_energy_Jtotal_energy_J
1463846564.537,0.000,4.98400,0.30500,1.52012,0.00000,0.00000
1463846574.549,10.012,4.99600,0.27360,1.36691,13.68549,13.68549
1463846584.561,20.024,4.98800,0.31290,1.56075,15.62608,29.31157
```

#### 5 samples at 10 second interval using watt-hours for energy:
```
$ python terminal.py -n 5 -i 10 -u Wh

INA219 Voltage, Power & Energy Measurement
Using default I2C address 0x40
Number of samples = 5
Sample interval = 10.0 s
Samples collected in 50.0 s
Energy units = Wh
--------------------------------------------------------------------------
   unix time s elapsed s     bus V   shunt A   power W energy Wh  total Wh
1463846723.493     0.000     4.992     0.264     1.316     0.000     0.000
1463846733.504    10.012     4.996     0.257     1.284     0.004     0.004
1463846743.516    20.023     4.996     0.272     1.360     0.004     0.007
1463846753.528    30.035     4.992     0.267     1.333     0.004     0.011
1463846763.540    40.047     5.000     0.266     1.331     0.004     0.015
```

#### Default sample number, 4, at 4 Hz and graph from 0 to 1.8 W:
```
$ python terminal.py -i 0.25 -g 1.8
INA219 Voltage, Power & Energy Measurement
Using default I2C address 0x40
Number of samples = 4
Sample interval = 0.25 s
Samples collected in 1.0 s
Energy units = J
--------------------------------------------------------------------------
   unix time s elapsed s     bus V   shunt A   power W  energy J   total J
1463846919.658     0.000     5.000     0.263     1.314     0.000     0.000 |
1463846919.910     0.252     4.996     0.259     1.294     0.326     0.326 | ===
1463846920.163     0.504     4.996     0.254     1.268     0.320     0.646 | ===
1463846920.415     0.756     4.996     0.265     1.324     0.334     0.980 | ====
```

#### Measurement when a line of data is read from the serial port:
Wiring diagram and Arduino example sketch are in the [ArduinoSerialCounter](/ArduinoSerialCounter/) folder.

```
$ python terminal.py -p /dev/ttyAMA0 -b 9600
INA219 Voltage, Power & Energy Measurement
Using default I2C address 0x40
Serial port open: /dev/ttyAMA0 @ 9600 kbps
Number of samples = 4
Sample interval = as received from serial port
Energy units = J
--------------------------------------------------------------------------
   unix time s elapsed s     bus V   shunt A   power W  energy J   total J
1463846974.601     0.000     4.972     0.309     1.538     0.000     0.000 || Arduino>>6
1463846974.852     0.250     4.976     0.305     1.519     0.381     0.381 || Arduino>>7
1463846975.102     0.501     4.988     0.318     1.586     0.397     0.778 || Arduino>>8
1463846975.353     0.752     4.984     0.330     1.643     0.412     1.190 || Arduino>>9
```
Using ArduinoSerialCounter.ino on an Arduino Mega 2560 connected to a Raspberry Pi on Serial1.

#### Measurement when a line of data is read from the serial port and graph from 0 to 1.8 W:

```
$ python terminal.py -p /dev/ttyAMA0 -b 9600 -g 1.8
INA219 Voltage, Power & Energy Measurement
Using default I2C address 0x40
Serial port open: /dev/ttyAMA0 @ 9600 kbps
Number of samples = 4
Sample interval = as received from serial port
Energy units = J
--------------------------------------------------------------------------
   unix time s elapsed s     bus V   shunt A   power W  energy J   total J
1463847014.188     0.000     4.984     0.319     1.592     0.000     0.000 |            || Arduino>>4
1463847014.439     0.251     4.968     0.349     1.735     0.435     0.435 | =========  || Arduino>>5
1463847014.689     0.501     4.976     0.309     1.538     0.385     0.820 | ======     || Arduino>>6
1463847014.939     0.752     4.972     0.317     1.578     0.396     1.216 | =======    || Arduino>>7
```
