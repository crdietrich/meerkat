# Serial Terminal Setup  

## Windows 10/11  
(TODO)

## Linux  
Instructions below use `/dev/ttyACM0` as the example serial port address.

1. Plug MicroPython board into USB port
2. Do a broad check of attached devices using `dmesg` > `$ dmesg | grep tty`
3. Comfirm the USB serial port is part of the `dialout` group: `ls -l /dev/ttyACM0`
4. Check if the current user is part of the `dialout` group: `$ id`
5. If not, add them: `$ sudo adduser USERNAME dialout`
6. Check again if the current user is part of the `dialout` group: `$ id`

### Linux screen  
1. Install screen if needed: `$ sudo apt install screen`
2. Confirm serial connection baud rate of board, for exampe `115200` 
3. Start screen using baud rate: `$ screen /dev/ttyACM0 115200`
4. To end serial connection, use `ctrl+c` (the control key + c )
5. Restarting the session after leaving it might hang the adaptor, unplug and plug it back in if so.

### Linux References  
https://www.cyberciti.biz/faq/find-out-linux-serial-ports-with-setserial/  
https://stackoverflow.com/questions/6301840/how-to-stop-a-screen-process-in-linux  
