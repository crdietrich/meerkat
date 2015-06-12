import argparse
import json
import time
import traceback
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone
import requests

import gforms
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

scheduler = BackgroundScheduler()
scheduler.configure(timezone=timezone('US/Pacific'))

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
    TEMP_BUFFER.append(temperature)
    OXYGEN_BUFFER.append(oxygen)
    PH_BUFFER.append(ph)
    CSO_NOW = cso_now
    CSO_RECENT = cso_recent


# Push the data at 11:05
@scheduler.scheduled_job(trigger='cron', hour=21, minute=5)
def push_data():
    payload = {'temperature': get_temp(), 'ph': get_ph(), 'oxygen': get_oxygen(), 'cso_now': CSO_NOW,
               'cso_recent': CSO_RECENT}
    print('POSTING to {} with data: {}'.format(URL, payload))
    try:
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        requests.post(URL, data=json.dumps(payload), headers=headers)
        print("=== POST Success ===")
    except Exception:
        traceback.print_exc()
    else:
        TEMP_BUFFER = []
        OXYGEN_BUFFER = []
        PH_BUFFER = []


def run_loop():
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

        print("Time,Temp,DO,pH,EC,TDS,SAL,SG,Status")
        print(s)

        save_data(temp, do, ph, cso_parser.now_count, cso_parser.recent_count)

        # Collect data once an hour.
        time.sleep(60 * 60)


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
    URL = 'http://{}:{}/data'.format(ip, port)
    
    scheduler.start()
    run_loop()
