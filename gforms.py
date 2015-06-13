"""Push data from an IoT source to Google Sheets
Colin Dietrich 2015
Basic ideas from:
https://www.reddit.com/r/learnprogramming/comments/32xd4s/how_can_i_use_python_to_submit_a_google_form_or/

Note: If you get a InsecurePlatformWarning:
pip install requests[security]
"""

import requests

def submit(data):

    # could put in config file, but too project specific
    formkey = "100Qn1AFWNQvxoRt-4MTNm2IfwXpYhsd6X8dZ23SDRo0"
    post_url = "https://docs.google.com/forms/d/"
    post_url_suffix = "/formResponse"
    url = post_url + formkey + post_url_suffix

    payload = {
    "entry.1572910906": data[0],        # Sensor_Time
    "entry.439473034": data[1],         # Temp
    "entry.41883386": data[2],          # DO
    "entry.1859154242": data[3],        # OR
    "entry.2101029771": data[4],        # pH
    "entry.758465889": data[5],         # EC
    "entry.85226853": data[6],          # TDS
    "entry.75712232": data[7],          # SAL
    "entry.1168665858": data[8],        # SG
    "entry.788526394": str(data[9]),    # Status
    "entry.1224600998": data[10],       # CSO_now
    "entry.2060957626": data[11],       # CSO_recent
    "entry.417012738": data[12],        # CSO_status
    "entry.1508779644": data[13]        # push_status
    }

    r = requests.post(url=url, data=payload)
    return r

