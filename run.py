import argparse
import time

import serial
from io import BufferedRWPair, TextIOWrapper

from cso_parser import CsoParser
from sensors import AtlasI2C

# sensor class, preconfigured for Pi B+ v2
ai2c = AtlasI2C()

parser = argparse.ArgumentParser()
parser.add_argument('server_ip', help='The IP address of the lighthouse node.')
parser.add_argument('port', help='The port of the lighthouse node.')


def init_db():
    # TODO: initialize the sqlite database.
    pass

def save_data(temperature, salinity, oxygen, cso_now, cso_recent):
    # TODO save data to database (sqlite)
    pass


def push_data(temperature, salinity, oxygen, cso_now, cso_recent, server_ip, server_port):
    payload = {'temperature': temperature, 'salinity': salinity, 'oxygen': oxygen, 'cso_now': cso_now,
               'cso_recent': cso_recent}


# TODO push data to lighthouse node.

# def run_loop(oxy_usb, sal_usb, server_ip, server_port):
def run_loop(server_ip, server_port):

    init_db()
    cso_parser = CsoParser()
    #temp_conn, sal_conn, oxy_conn = initialize_serial_connections(oxy_usb, sal_usb)

    while True:

        s = ai2c.query_all()
        temp = s[1]
        do = s[2]
        ph = s[3]

        print("Time,Temp,DO,pH,EC,TDS,SAL,SG,Status")
        print(s)

        save_data(temp, do, ph, cso_parser.now_count, cso_parser.recent_count)
        push_data(temp, do, ph, cso_parser.now_count, cso_parser.recent_count)

        # TODO: Determine how often we should be grabbing data from sensors and pushing to other pi node.
        time.sleep(5)

if __name__ == '__main__':
    # TODO: Create supervisord script to keep run.py running.
    # TODO: Parse command line args for database connection info.
    args = parser.parse_args()
    # run_loop(args.oxygen, args.salinity, args.server_ip, args.port)
    run_loop(args.server_ip, args.port)
