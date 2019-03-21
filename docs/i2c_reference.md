## Raspberry Pi3 Package Setup  
#### Update, remove Firefox and install Chromium  
Firefox crashes too much on 16.04 ARM, replace it with Chromium.  
$ sudo apt-get update
$ sudo apt-get purge firefox
$ sudo apt-get install chromium-browser

#### Upgrade pip for python3
$ python3 -m pip install --upgrade pip

#### Install RealVNC  
Install via .deb download from:  
https://www.realvnc.com/en/connect/download/vnc/raspberrypi/

Setup nvc-server to start on boot:
https://learn.adafruit.com/adafruit-raspberry-pi-lesson-7-remote-control-with-vnc/running-vncserver-at-startup
but replace 'tightvnc' with 'realvnc'


## MicroPython I2C Command Reference  
Copied from:  
https://docs.micropython.org/en/latest/library/machine.I2C.html  

```
from machine import I2C

i2c = I2C(freq=400000)          # create I2C peripheral at frequency of 400kHz
                                # depending on the port, extra parameters may be required
                                # to select the peripheral and/or pins to use

i2c.scan()                      # scan for slaves, returning a list of 7-bit addresses

i2c.writeto(42, b'123')         # write 3 bytes to slave with 7-bit address 42
i2c.readfrom(42, 4)             # read 4 bytes from slave with 7-bit address 42

i2c.readfrom_mem(42, 8, 3)      # read 3 bytes from memory of slave 42,
                                #   starting at memory-address 8 in the slave
i2c.writeto_mem(42, 2, b'\x10') # write 1 byte to memory of slave 42
                                #   starting at address 2 in the slave

```

## Raspberry Pi I2C Command Reference  


### Command Reference  
i2cdetect[]
https://linux.die.net/man/8/i2cdetect  

https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/plain/Documentation/i2c/smbus-protocol  

http://wiki.erazor-zone.de/wiki:linux:python:smbus:doc  


https://www.kernel.org/doc/Documentation/i2c/smbus-protocol

### Setup  
```
import smbus  
bus = smbus.SMBus(1)
bus_addr = 0x63  # = dec 99
```

### Commands  
#### write_quick  

* Send only the read/write byte

Command:  
```
bus.write_quick(bus_addr)
```

Action:  
Setup Write to 0x63 + ACK  

![write_quick](./images/i2c_write_quick.jpg)

#### read_byte

* Read one byte from i2c bus device, without specifying the internal device register  

Command:  
```
bus.read_byte(bus_addr)  
```

Action:  
Read 0x63 + ACK  
Reply byte (255 in this example) + NAK  

![read_byte](./images/i2c_read_byte.jpg)  

#### write_byte  

* Send a single byte to the i2c device  

Command:  
```
bus.write_byte(bus_addr, ord('R'))  
```  

Action:  
Write 0x63 + ACK  
R (0x52) + ACK  

![write_byte](./images/i2c_write_byte.jpg)  

#### read_byte_data  

 * Read byte data transaction, send one byte and read one byte reply from device  

Command:  
 ```
 bus.read_byte_data(bus_addr, ord('R'))  
 ```  

Action:  
Write 0x63 + ACK  
Write 'R' (0x52) + ACK  
Read 0x63 + ACK
Read '254' (0xFE) + NAK  

![read_byte_data](./images/i2c_read_byte_data.jpg)  

#### write_byte_data  

* Write byte data transaction, send one byte then a second byte to the device

Command:  
```
bus.write_byte_data(bus_addr, ord('R'), 2)  
```  

Action:  
Write 0x63 + ACK  
Write 'R' (0x52) + ACK
Write '2' (0x02) + ACK

![write_byte_data](./images/i2c_write_byte_data.jpg)

#### read_word_data  

* Read word data transaction  

Command:  
```  
bus.read_word_data(bus_addr, ord('R'))  
```  
Response:  
```
33022
```

Action:  
Write 0x63 + ACK  
Write 'R' (0x52) + ACK  
Read 0x63 + ACK
Read '254' (0xFE) + ACK  
Read '0' (0x00) + NAK

![read_word_data](./images/i2c_read_word_data.jpg)

#### write_word_data  

* Write word data transaction  

Command:  
```
bus.write_word_data(bus_addr, ord('R'), 23456)
```

Note:  

```
>>> hex(23456)  
0x5ba0  
```

Action:  
Write 0x63 + ACK  
Write 'R' (0x52) + ACK  
Write '160' (0xA) + ACK  
Write '[' (0x5B) + NAK

![write_word_data](,/images/i2c_write_word_data.jpg)  

### process_call  

* Process call transaction  

Command:  
```  
bus.process_call(bus_addr, ord('R'), 4)  
```  

Action:  
Action:  
Write 0x63 + ACK  
Write 'R' (0x52) + ACK  
Write '4' (0x04) + ACK  
Write '0' (0x00) + NAK
Read '254' (0xFE) + ACK  
Read '0' (0x00) + NAK  

![process_call](./images/i2c_process_call.jpg)  

## io Library  
```
import io
bus = 1
file_read = io.open("/dev/i2c-"+str(bus), "rb", buffering=0)
file_write = io.open("/dev/i2c-"+str(bus), "rb", buffing=0)
```
