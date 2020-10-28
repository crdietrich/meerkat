# This is your main script.
import time
from DS3231 import DS3231
from machine import RTC, idle
from network import WLAN

wlan = WLAN(mode=WLAN.STA, antenna=WLAN.INT_ANT)
rtc = RTC()

def do_connect(ssid=None, password=None, timeout=3000, wait=True):
    if not wlan.isconnected():
        print('connecting to network...')
        try: 
            wlan.connect(ssid, auth=(WLAN.WPA2, password), timeout=timeout)
            while not wlan.isconnected() and wait:
                idle() # save power while waiting
            return True
        except Exception as e:
            print("Failed to connect to network")
            return False

def setRTCLocalTime():
    if do_connect(ssid='<your_ssid>', password='<your_ssid_password>', timeout=5000, wait=True):
        rtc.ntp_sync("pool.ntp.org")
        print('RTC Set from NTP to UTC:', rtc.now())
        wlan.disconnect()

if DS3231().loadTime():
    if not rtc.synced():
        setRTCLocalTime()
        DS3231().saveTime()

    print("time synced with DS3231: ", time.localtime())
else:
    setRTCLocalTime()   #try to sync with ntp server if DS3231 module not found
    print("time from RTC: ", time.localtime())
