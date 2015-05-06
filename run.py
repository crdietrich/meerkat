import argparse
import serial
import threading
from io import BufferedRWPair, TextIOWrapper
from time import sleep


temp_usb = '/dev/ttyAMA0'
BAUD_RATE = 9600
parser = argparse.ArgumentParser()
parser.add_argument('oxygen', help='The USB port of the oxygen sensor.')
parser.add_argument('salinity', help='The USB port of the salinity sensor.')
parser.add_argument('server_ip', help='The IP address of the lighthouse node.')
parser.add_argument('port', help='The port of the lighthouse node.')


def init_db():
	# TODO: initialize the sqlite database.
	pass


def create_connection(usb_port):
	print('Creating connection on {}'.format(usb_port))
	ser = serial.Serial(usb_port, BAUD_RATE)
	# disable_continuous_mode(ser)
	return TextIOWrapper(BufferedRWPair(ser, ser), newline='\r', encoding='ascii', line_buffering=True)


def disable_continuous_mode(conn: serial.Serial):
	# TODO: research if we need to send this command every time we connect to the sensors, or if it only
	# needs to be sent once to disable continuous mode. If only once we should move this code into a
	# separate python file.
	print('Disabling continuous mode...')
	conn.write(bytes('E\r', 'ascii'))

	if conn.inWaiting() > 0:
		# clear the buffer if there is anything waiting.
		print('Clearing buffer...')
		conn.read(conn.inWaiting())


def save_data(temperature, salinity, oxygen):
	# TODO save data to database (sqlite)
	pass


def push_data(temperature, salinity, oxygen, server_ip, server_port):
	payload = {'temperature': temperature, 'salinity': salinity, 'oxygen': oxygen}
	# TODO push data to lighthouse node.


def initialize_serial_connections(oxy_usb, sal_usb):
	temp_conn = create_connection(temp_usb)
	sal_conn = create_connection(sal_usb)
	oxy_conn = create_connection(oxy_usb)

	return temp_conn, sal_conn, oxy_conn


def run_loop(oxy_usb, sal_usb, server_ip, server_port):
	temp_conn, sal_conn, oxy_conn = initialize_serial_connections()

	# TODO: Catch serial.serialutil.SerialException on read?
	while True:
		temp.write('R\r')
		temp = temp_conn.readline()

		sal.write('R\r')
		sal = sal_conn.readline()
		
		# TODO: send temp and sal to oxy sensor first, then retrieve oxy value.
		# oxy.write(<salinity command here>)
		# oxy.write(<temp command here>)
		oxy.write('R\r')
		oxy = oxy_conn.readline()

		print('Temperature: {}, Dissolved Oxygen: {}, Salinity: {}'.format(temp, oxy, sal))
		
		save_data(temp, oxy, sal)
		push_data(temp, oxy, sal, server_ip, server_port)

		# TODO: Determine how often we should be grabbing data from sensors and pushing to other pi node.
		time.sleep(5)


if __name__ == '__main__':
	# TODO: Create supervisord script to keep run.py running.
	# TODO: Parse command line args for database connection info.
	args = parser.parse_args()
	run_loop(args.oxygen, args.salinity, args.server_ip, args.port)
