import serial
import threading

print('Starting server...')

temperature_usb = '/dev/ttyAMA0'
BAUD_RATE = 9600
temperature_ser = serial.Serial(temperature_usb, BAUD_RATE)

def process_line(line):
	print('Temp: {}'.format(line))

def temperature_loop():
	line = ""
	# TODO: Catch serial.serialutil.SerialException on read?
	while True:
		data = temperature_ser.read().decode('ascii')
		
		if(data == "\r"):
			process_line(line)
			line = ""
		else:
			line = line + data

temperature_thread = threading.Thread(target=temperature_loop)
temperature_thread.start()


"""
 TODO:
	Add command line args for USB ports for Salinity and Dissolved Oxygen sensors.
	
	On startup disable continuous send mode on each sensor.
	
	Create run loop that reads each value individually then pushes data to other pi node.

	Inside run loop send temperature and salinity values to dissolved oxygen sensor before reading.
	
	Determine how often we should be grabbing data from sensors and pushing to other pi node.

	Create sqllite database to store data in.

	Create method for extracting CSV of data.

	Create supervisord script to keep run.py running.
"""
