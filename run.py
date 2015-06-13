import argparse
import json
import time
import traceback
import requests
import atexit
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone
from os.path import sep, isfile

import config
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
PUSH_STATUS = 1
GFORM_STATUS = 1

cso_parser = CsoParser()

scheduler = BackgroundScheduler()
scheduler.configure(timezone=timezone('US/Pacific'))
JOB = None
RUN = True

atexit.register(quit)

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

def buffer_data(data):
    """Put collected data into a buffer for pushing.
    List format from run_loop and gforms.submit"""

    TEMP_BUFFER.append(data[1])
    OXYGEN_BUFFER.append(data[2])
    PH_BUFFER.append(data[3])
    CSO_NOW = data[10]
    CSO_RECENT = data[11]
    print("buffer_data >> Success")

def gform_data(data):
    """Push the data to a Google Form for online saving"""

    try:
        r = gforms.submit(data)
        GFORM_STATUS = 1
        print("gform_data >> " + str(r.reason) + " " + str(r.status_code))
    except:
        GFORM_STATUS = 0
        print("gform_data >> " + str(r.reason) + " " + str(r.status_code))

def record(path_filename, data):
    """Write data to file at the specified location.  open() will make the file
    if the called file does not exist - no need to check time or file creation
    """

    f = open(path_filename, 'a')
    data = str(data)
    f.write(data)
    f.close()

def save_data(data_type, data):
    """Accepts a string for the data type (stream, tjson, anything)
    add a data_type description to log filename, as in 'date - type log.csv'
    Will write a new file every day."""

    today = time.strftime("20%y_%m_%d")
    path_filename = config.data_directory + sep + today + " - " + str(data_type) + " data.csv"
    if isfile(path_filename) == False:
        record(path_filename, config.header + config.newline)
    record(path_filename, str(data) + config.newline)

# Push the data currently set to 11:05, see config.py
@scheduler.scheduled_job(trigger='cron', **config.push_data_kwargs)
def push_data():
    """Push data to the lighthouse pi"""

    payload = {'temperature': get_temp(), 'ph': get_ph(), 'oxygen': get_oxygen(), 'cso_now': CSO_NOW,
               'cso_recent': CSO_RECENT}
    print("push_data >> POSTING to {} with data: {}".format(URL, payload))
    try:
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        r = requests.post(URL, data=json.dumps(payload), headers=headers)
        PUSH_STATUS = 1
        print("push_data >> ", + str(r.reason) + " " + str(r.status_code))
    except Exception:
        PUSH_STATUS = 0
        print("push_data >> ", + str(r.reason) + " " + str(r.status_code))
        traceback.print_exc()
    else:
        TEMP_BUFFER = []
        OXYGEN_BUFFER = []
        PH_BUFFER = []
        print("push_data >> Sensor Buffers Cleared")

def quit():
    """Stop everything, likely keyboard interrupt"""
    cso_parser.stop()

def run_loop():
    """Collect sensor & cso data, push to multiple locations"""

    JOB = scheduler.start()
    try:
        while RUN:
            print("="*40)
            now = time.strftime("%Y/%m/%d %H:%M:%S")
            print("run_loop >> Begin Sensor Polling at " + now)

            # get sensor and CSO data
            data = ai2c.query_all()
            data += [cso_parser.now_count, cso_parser.recent_count, cso_parser.status]

            # put the sensor data into a local buffer for pushing to the lighthouse
            buffer_data(data)

            # save data to google drive
            data += [PUSH_STATUS]
            gform_data(data=data)

            # save the data to local disk
            data += [GFORM_STATUS]
            save_data(data_type="dsensor", data=(",").join([str(s) for s in data]))

            now = time.strftime("%Y/%m/%d %H:%M:%S")
            print("run_loop >> END Sensor Polling at " + now)

            # collect data at set sample rate
            print("run_loop >> Sleeping for " + str(config.sensor_dt) + " seconds...")
            time.sleep(config.sensor_dt)

    except KeyboardInterrupt:
        scheduler.shutdown(wait=False)


if __name__ == '__main__':
    # TODO: comand line arg parsing
    URL = 'http://{}:{}/data'.format(config.ip, config.port)
    run_loop()
