# Development Workflow  

1. Prototype on Raspberry Pi  
    * branch off `develop` `dev_x` where `x` is the driver name
2. Test driver class on MicroPython  
    * continue to use branch `dev_x`
3. Apply code style and package-wide refactors on Linux Laptop
    * Use GitKraken to manage branches
    * Use PyCharm for code and style tests
    
# I2C Base Classes

## Supported Hardware  
1. Raspberry Pi - Raspbian Linux  
2. Adafruit QT Py  
    a. QT Py - SAMD21 Dev  
    b. QT Py ESP32-S2  
    c. QT Py ESP32-S3  
    d. QT Py RP2040  
3. Raspberry Pi Pico W  
4. Sparkfun Thing Plus RP2040  
5. OpenMV boards  

## Examples and Tests  
Due to the each sensor outputing data contingent on the environment it's in, tests are qualitative. The exception is the Digital to Analog Converter loopback to Analog to Digitial converter which should return results within the accuracy and precision of both devices. For Linux, the Notebooks provide more detailed review and plotting functionality. The test scripts allow MicroPython applications to verify sensor and driver functions in a more limited way. 

1. ADC DAC loopback
2. Per-sensor Notebook Example
3. Per-sensor script outputs

## Driver Usage Pattern  
1. Import board specific `system I2C class`
2. Assign pins or bus number to `system I2C class`
3. `meerkat.base` determines system and imports appropriate wrapper class
4. Wrapper class is passed instance of `system I2C class`
5. Wrapper class is is passed as attribute to driver class
6. Driver class uses standard wrapper class attributes           

## JSON Data Generation Pattern  
1. `meerkat.base.__init__` detects sys.platform
2. `meerkat.base.__init__` imports platform json as json alias
3. `meerkat.base.__init__` defines Base class with `to_json` method  
4. `meerkat.base.__init__` defines Base class with `json_dumps` method  
5. `meerkat.data.__init__` uses meerkat.base.Base method `json_dumps` to output JSON data  
6. `meerkat.data.__init__` uses meerkat.base.Base method `to_json` to output JSON metadata  

## Driver Code Usage  
1. from meerkat.base import I2C
    * board specific I2C wrapper
    * uses sys.platform to conditionally import correct wrapper

## Code Structure  
```
meerkat/
    base/
        __init__.py
        i2c_circuitpython.py
        i2c_pi.py
        i2c_quickwire.py
        tools.py
    data/
        __init__.py
        parser.py
        timepiece.py
    driver/
        __init__.py
        (sensor specific driver modules)
```