import serial
import threading
from io import BufferedRWPair, TextIOWrapper
from time import sleep


temp_usb = '/dev/ttyAMA0'
BAUD_RATE = 9600


def init_db():
	# TODO: initialize the sqlite database.
	pass


def create_connection(usb_port):
	ser = serial.Serial(usb_port, BAUD_RATE)
	disable_continuous_mode(ser)
	return TextIOWrapper(BufferedRWPair(ser, ser), newline='\r', encoding='ascii', line_buffering=True)


def disable_continuous_mode(conn: serial.Serial):
	# TODO: research if we need to send this command every time we connect to the sensors, or if it only
	# needs to be sent once to disable continuous mode. If only once we should move this code into a
	# separate python file.
	
	conn.write('E\r')

	if conn.inWaiting() > 0:
		# clear the buffer if there is anything waiting.
		conn.read(conn.inWaiting())


def save_data(temperature, salinity, oxygen):
	# TODO save data to database (sqlite)
	pass


def push_data(temperature, salinity, oxygen, server_ip, server_port):
	# TODO push data to lighthouse node.
	pass


def initialize_serial_connections(oxy_usb, sal_usb):
	temp_conn = create_connection(temp_usb)
	sal_conn = create_connection(sal_usb)
	oxy_conn = create_connection(oxy_usb)

	disable_continuous_mode(temp_conn)
	disable_continuous_mode(sal_conn)
	disable_continuous_mode(oxy_conn)

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
	# TODO: Parse command line args for Salinity and Dissolved oxygen serial ports, append them to args array.
	# TODO: Parse command line args for lighthouse ip address and port, append them to args array.
	# TODO: Parse command line args for database connection info.
	init_db()
	args = []
	temperature_thread = threading.Thread(target=run_loop, args=args)
	temperature_thread.start()
