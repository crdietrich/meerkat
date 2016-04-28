# pi_INA219
Python TI INA219 current/power sensor

Requires Adafruit_GPIO for i2c access, not tested with pure python version.

Basic terminal use:
```
python terminal.py
```

Collect unlimited samples at 0.5 second interval:
```
python terminal.py -n inf -i 0.5
```

Collect 5 samples at 1 second interval and save to directory /home/pi/data/:
```
python terminal.py -s /home/pi/data/ -i 1
```



