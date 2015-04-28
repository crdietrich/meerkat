import serial
import threading

print('Starting server...')

temperature_usb = '/dev/ttyAMA0'
BAUD_RATE = 9600
temperature_ser = serial.Serial(temperature_usb, BAUD_RATE)

temperature_ser.write(b'T100.00')
