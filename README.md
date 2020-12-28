# Meerkat - A Data Acquisition Library for Raspberry Pi and MicroPython

### Features  

* Pure Python API to I2C devices
* Data output to JSON or CSV with JSON header
* Standardized timestamps string formats
* Data timestamping and GPS tagging of data  
* Metadata description of devices in JSON
* Parser to convert CSV output to Pandas DataFrame
* Object oriented class structure for REPL use
* Code written for Raspberry Pi and MicroPython will run on both
* Base methods separated from device drivers for reusability and extension

### Supported Python Platforms  
Python 3, Jupyter and Pandas  

* Raspberry Pi Model 3
* Raspberry Pi Model 4  

MicroPython  

* FiPy (should work on all PyCom boards)  
* OpenMV Cam M7 (tested with OV7725)
* Note: CircuitPython is NOT supported due to it [missing ujson libraries](https://circuitpython.readthedocs.io/en/latest/docs/library/index.html)  

### Supported Sensors and Devices  
| Type | Device | Module | I2C Address |  
| ---- | ------ | ------ | ----------- |  
| 1 Channel Relay        | [Sparkfun Qwiic Single Relay](https://jap.hu/electronic/relay_module_i2c.html) | relay.py    | 0x18 |  
| 8 Channel Relay        | [Peter Jakab 8 Channel Relay](https://jap.hu/electronic/relay_module_i2c.html) | mcp23008.py | 0x20 |  
| DC & Stepper Motor     | [Grove Motor Driver v1.3](http://wiki.seeedstudio.com/Grove-I2C_Motor_Driver_V1.3/) | motor.py   | 0x0F |  
| Ambient Temperature    | [MCP9808](https://www.adafruit.com/product/1782)   | mcp9808.py | 0x18 |  
| DC Current & Power     | [INA219](https://www.adafruit.com/product/904)     | ina219.py  | 0x40 |  
| Acceleration & Gyro    | [MPU6050](https://www.adafruit.com/product/3886)   | mpu6050.py | 0x68 |  
| Analog to Digital      | [ADS1115](https://www.adafruit.com/product/1085)   | ads.py     | 0x48 |  
| pH, Conductivity       | [Atlas Sensors](https://www.atlas-scientific.com/) | atlas.py   | 0x61, 0x62, 0x63, 0x64 |  
| Temperature, Humidity, Pressure, VOC Gas | [Bosch BME680](https://www.sparkfun.com/products/14570) | bme680.py  | 0x77 |  
| GPS                    | [PA1010D](https://www.adafruit.com/product/4415)   | pa1010d.py | 0x10 |  
| RTC                    | [DS3221](https://www.adafruit.com/product/3013)    | ds3231.py  | 0x68 |  

### Examples  

The `examples` directory contains usage in Jupyter Notebooks and the `tests` folder contains scripts that will run on MicroPython or Linux.

### Contributing  

Contributions are welcome! Please read our [Code of Conduct](https://www.contributor-covenant.org/version/1/4/code-of-conduct/).
