# Meerkat - A Data Acquisition Library for Raspberry Pi and MicroPython

### Features  

* Pure Python API to I2C devices
* Raspberry Pi and MicroPython - code written on one platform will run on the other without modification.  
* Data output to .csv with JSON header or pure JSON
* Parser to convert .csv to Pandas DataFrame
* Standardized timestamps and timestamp parsing  
* Metadata description of devices in JSON
* Object oriented class structure allows easy REPL use
* Base methods separated from device drivers for reusability and extension

### Requirements  
Raspberry Pi 3 - Python 3, Jupyter and Pandas.
MicroPython - Only larger memory microcontrollers such as the FiPy and OpenMV M7 are supported.

### Supported Devices  
| Interface Type | Implemented Device | Module | Status | 
| -------------- | ------------------ | ------ | ------ |
| Power Relay                          | Sparkfun Qwiic Single Relay | relay.py   | Done |
| DC & Stepper Motor                   | Grove Motor Driver v1.3     | motor.py   | Done |
| Ambient Temperature                  | MCP9808                     | mcp9808.py | Done |
| DC Current & Power                   | INA219                      | ina219.py  | Done |
| Acceleration & Gyro                  | MPU6050                     | mpu6050.py | Done |
| Analog to Digital                    | ADS1115                     | ads.py     | Done |
| pH, Conductivity                     | Atlas Sensors               | atlas.py   | Done |


### Examples  

The `examples` directory contains detailed Jupyter Notebook examples and the `tests` folder has python scripts for testing on MicroPython.


### Contributing  

Contributions are welcome! Please read our `Code of Conduct
<https://www.contributor-covenant.org/version/1/4/code-of-conduct/>`_
before contributing to help this project stay welcoming.
