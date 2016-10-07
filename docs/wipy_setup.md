# WiPy setup

Working with the WiPy 
Copied for access while messing with network configurations

## Steps
1. Connect to WiPy over wifi
2. Login using FTP
3. Set boot credentials to log on to local network
4. Connect over local network

## References

### General setup details:
[https://www.pycom.io/gettingstarted/](https://www.pycom.io/gettingstarted/)

### WLAN step by step
[https://docs.pycom.io/wipy/wipy/tutorial/wlan.html](https://docs.pycom.io/wipy/wipy/tutorial/wlan.html)

WLAN step by step
=================

The WLAN is a system feature of the WiPy, therefore it is always enabled
(even while in ``machine.SLEEP``), except when deepsleep mode is entered.

In order to retrieve the current WLAN instance, do::

   >>> from network import WLAN
   >>> wlan = WLAN() # we call the constructor without params

You can check the current mode (which is always ``WLAN.AP`` after power up)::

   >>> wlan.mode()

.. warning::
    When you change the WLAN mode following the instructions below, your WLAN
    connection to the WiPy will be broken. This means you will not be able
    to run these commands interactively over the WLAN.

    There are two ways around this::
     1. put this setup code into your :ref:`boot.py file<wipy_filesystem>` so that it gets executed automatically after reset.
     2. :ref:`duplicate the REPL on UART <wipy_uart>`, so that you can run commands via USB.

Connecting to your home router
------------------------------

The WLAN network card always boots in ``WLAN.AP`` mode, so we must first configure
it as a station::

   from network import WLAN
   wlan = WLAN(mode=WLAN.STA)


Now you can proceed to scan for networks::

    nets = wlan.scan()
    for net in nets:
        if net.ssid == 'mywifi':
            print('Network found!')
            wlan.connect(net.ssid, auth=(net.sec, 'mywifikey'), timeout=5000)
            while not wlan.isconnected():
                machine.idle() # save power while waiting
            print('WLAN connection succeeded!')
            break

Assigning a static IP address when booting
------------------------------------------

If you want your WiPy to connect to your home router after boot-up, and with a fixed
IP address so that you can access it via telnet or FTP, use the following script as /flash/boot.py::

   import machine
   from network import WLAN
   wlan = WLAN() # get current object, without changing the mode

   if machine.reset_cause() != machine.SOFT_RESET:
       wlan.init(WLAN.STA)
       # configuration below MUST match your home router settings!!
       wlan.ifconfig(config=('192.168.178.107', '255.255.255.0', '192.168.178.1', '8.8.8.8'))

   if not wlan.isconnected():
       # change the line below to match your network ssid, security and password
       wlan.connect('mywifi', auth=(WLAN.WPA2, 'mywifikey'), timeout=5000)
       while not wlan.isconnected():
           machine.idle() # save power while waiting

.. note::

   Notice how we check for the reset cause and the connection status, this is crucial in order
   to be able to soft reset the WiPy during a telnet session without breaking the connection.

Local file system and FTP access
--------------------------------

There is a small internal file system (a drive) on the WiPy, called ``/flash``,
which is stored within the external serial flash memory.  If a micro SD card
is hooked-up and mounted, it will be available as well.

When the WiPy starts up, it always boots from the ``boot.py`` located in the
``/flash`` file system.

The file system is accessible via the native FTP server running in the WiPy.
Open your FTP client of choice and connect to:

**url:** ``ftp://192.168.1.1``, **user:** ``micro``, **password:** ``python``

See :ref:`network.server <network.server>` for info on how to change the defaults.
The recommended clients are: Linux stock FTP (also in OSX), Filezilla and FireFTP.
For example, on a linux shell::

   $ ftp 192.168.1.1

The FTP server on the WiPy doesn't support active mode, only passive, therefore,
if using the native unix ftp client, just after logging in do::

    ftp> passive

Besides that, the FTP server only supports one data connection at a time. Check out
the Filezilla settings section below for more info.
   
1. Power WiPy and connecto to WiPy wifi.
1. Open PyMakr and confirm connection over wifi works using:
**url:** ``ftp://192.168.1.1``, **user:** ``micro``, **password:** ``python``	
1. Create a connection profile in Filezilla:
	ip, user, password as above
	General tab > encryption = ''Only use plain FTP (insecure)''
	Transfer tab > max connections = 1
1. Open FTP connection to wipy
1. 


## UART serial duplicate
Duplicate the Python REPL on the USB serial port
	from machine import UART
	import os
	uart = UART(0, 115200)
	os.dupterm(uart)
	
## SD card loading arbitrary python code
from machine import SD
import os
sd = SD(pins=('GP10', 'GP11', 'GP15'))
os.mount(sd, '/sd')