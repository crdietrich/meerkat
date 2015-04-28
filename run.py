import serial
import threading

print('Starting server...')

temperature_usb = '/dev/ttyAMA0'
BAUD_RATE = 38400
temperature_ser = serial.Serial(temperature_usb, BAUD_RATE)

def process_line(line):
	print('Need to process line: {}'.format(line))

def temperature_loop():
	line = ""
	while True:
		data = temperature_ser.read()
		if(data == "\r"):
			process_line(line)
			line = ""
		else:
			line = line + data

temperature_thread = threading.Thread(target=temperature_loop)
temperature_thread.start()
