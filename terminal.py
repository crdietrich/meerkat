"""Command line tool for collecting data from the TI INA219 ic2 chip
"""

from ina219 import INA219

import sys
from getopt import getopt, GetoptError
from time import time, sleep
from atexit import register


def usage():
    print("use command argument -h or --help for details")


def save_start():
    pass


def save_end():
    pass


def close():
    pass

register(close)

args_in = sys.argv[1:]

i = INA219()

inf = False
dt = 2
n = 4
min_dt = 0.05

try:
    opts, args = getopt(args_in,
                        "hn:i:u:s:",
                        ["help", "number", "interval", "units", "save"])
except GetoptError:
    usage()
    sys.exit(2)

for opt, arg in opts:
    # print("opt, arg = ", opt, arg)
    if opt in ("-h", "--help"):
        usage()
        sys.exit()

    elif opt in ("-n", "--number"):
        if arg == "inf":
            inf = True
        else:
            try:
                n = int(arg)
            except ValueError:
                usage()
                sys.exit()
            if n < 1:
                inf = True

    elif opt in ("-i", "--interval"):
        try:
            arg = float(arg)
        except ValueError:
            usage()
            sys.exit()
        if arg < min_dt:
            print("sample interval %s seconds too low" % arg)
            usage()
            sys.exit()
        else:
            dt = arg

    elif opt in ("-u", "--units"):
        if arg in i.available_units:
            i.set_energy_units(arg)
        else:
            print("unknown unit passed")
            usage()
            sys.exit()

    elif opt in ("-s", "--save"):
        print("saving to = %s" % arg)

print("INA219 Voltage, Power & Energy Measurement")
print("Number of samples = %s" % n)
print("Sample interval = %s" % dt)
print("Energy units = %s" % i.units)
print("Energy use over %s seconds at %ss interval" % (dt*n, dt))
print("------------------------------------------")
print("Assuming constant load, should be linear...")
print("time (s),power (W),sample_energy (%s),total_energy (%s)" % (i.units, i.units))
i.get_energy_simple()
t0 = time()
_n = 1
while True:
    try:
        if not inf:
            if _n > n:
                break
        print(_n, n)
        _n += 1
        sleep(dt)
        i.get_energy_simple()
        t = time()
        t_elapsed = t - t0
        print("%s,%0.3f,%0.5f,%0.5f,%0.5f" % (t, t_elapsed, i.p, i.e, i.e_total))
    except KeyboardInterrupt:
        break

