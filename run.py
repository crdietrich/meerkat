import argparse
import json
import time
import traceback
import requests

from cso_parser import CsoParser
from sensors import AtlasI2C

# sensor class, preconfigured for Pi B+ v2
ai2c = AtlasI2C()

parser = argparse.ArgumentParser()
parser.add_argument('server_ip', help='The IP address of the lighthouse node.')
parser.add_argument('port', help='The port of the lighthouse node.')

URL = None
TEMP_BUFFER = []
OXYGEN_BUFFER = []
PH_BUFFER = []
CSO_NOW = None
CSO_RECENT = None


def get_temp():
    if len(TEMP_BUFFER):
        return sum(TEMP_BUFFER) / len(TEMP_BUFFER)
    else:
        return 0

def get_oxygen():
    if len(OXYGEN_BUFFER):
        return sum(OXYGEN_BUFFER) / len(OXYGEN_BUFFER)
    else:
        return 0

def get_ph():
    if len(PH_BUFFER) > 0:
        return sum(PH_BUFFER) / len(PH_BUFFER)
    else:
        return 0

def init_db():
    # TODO: initialize the sqlite database.
    pass


def save_data(temperature, oxygen, ph, cso_now, cso_recent):
    # TODO save data to database (sqlite)
    pass


def push_data(temperature, oxygen, ph, cso_now, cso_recent, url):
    payload = {'temperature': temperature, 'ph': ph, 'oxygen': oxygen, 'cso_now': cso_now,
               'cso_recent': cso_recent}
    print('POSTING to {} with data: {}'.format(url, payload))
    try:
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        requests.post(url, data=json.dumps(payload), headers=headers)
    except Exception:
        traceback.print_exc()


def run_loop():
    init_db()
    cso_parser = CsoParser()

    while True:
        s = ai2c.query_all()
        temp = s[1]
        do = s[2]
        ph = s[3]

        print("Time,Temp,DO,pH,EC,TDS,SAL,SG,Status")
        print(s)

        save_data(temp, do, ph, cso_parser.now_count, cso_parser.recent_count)

        # Collect data once an hour.
        time.sleep(60 * 60)

if __name__ == '__main__':
    # TODO: Create supervisord script to keep run.py running.
    # TODO: Parse command line args for database connection info.
    args = parser.parse_args()
    URL = 'http://{}:{}/data'.format(args.server_ip, args.port)
    run_loop()
