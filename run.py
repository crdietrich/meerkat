import argparse
import json
import time
import traceback
import requests

import gforms
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


def save_data():
    # TODO save data to database (sqlite)
    pass


def push_data(temperature, oxygen, ph, cso_now, cso_recent, url):
    payload = {'temperature': temperature, 'ph': ph, 'oxygen': oxygen, 'cso_now': cso_now,
               'cso_recent': cso_recent}
    print('POSTING to {} with data: {}'.format(url, payload))
    try:
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        requests.post(url, data=json.dumps(payload), headers=headers)
        print("=== POST Success ===")
    except Exception:
        traceback.print_exc()


def run_loop(server_ip, server_port):
    url = 'http://{}:{}/data'.format(server_ip, server_port)
    init_db()
    cso_parser = CsoParser()

    while True:
        s = ai2c.query_all()
        s = s + [cso_parser.now_count, cso_parser.recent_count]

        # save data to google drive
        print("POSTING to Gforms...")
        print("Time,Temp,DO,OR,pH,EC,TDS,SAL,SG,Status,cso_now,cso_recent")
        print(s)
        gforms.submit(s)
        print("=== Gform POST Success ===")

        # push data to the lighthouse pi
        temp = s[1]
        do = s[2]
        ph = s[3]

        push_data(temp, do, ph, cso_parser.now_count, cso_parser.recent_count, url)

        # save data locally
        # save_data(temp, do, ph, cso_parser.now_count, cso_parser.recent_count)

        # TODO: Determine how often we should be grabbing data from sensors and pushing to other pi node.
        time.sleep(60*60)

if __name__ == '__main__':
    # TODO: Create supervisord script to keep run.py running.
    # TODO: Parse command line args for database connection info.
    # args = parser.parse_args()
    # run_loop(args.server_ip, args.port)

    # # lighthouse pi in the field
    # ip = "25.16.55.200"
    # port = "8080"

    # Luke's pi for testing
    ip = "25.112.184.183"
    port = "7000"

    run_loop(server_ip=ip, server_port=port)
