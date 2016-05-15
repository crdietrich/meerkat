# Command line tool for the TI INA219 current/power measurement chip
# Copyright (c) 2015 Colin Dietrich
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from ina219 import INA219

import os
import sys
import argparse
from time import time, sleep, strftime
from atexit import register


# terminal use defaults
inf = False
dt = 1.0
n = 4
min_dt = 0.05
print_dt = ""
pn = ""
file_path = ""
f = None
fp = None
f_save = False
instanced = False
graph = False
graph_max = 50  # units = Watt
graph_size = 10  # units = chars
port_monitor = False
port = None
baud = None
port_tx = False
serial_port = False
data = ""
extras = ""


def usage():
    """Usage command"""
    print("use command argument -h or --help for details")


def plotter(x, x_max, x_min=0.0, chars=10, plot_char="="):
    """Make an ascii plot of 1d data

    Parameters
    ----------
    x : float, number to plot
    x_max : float, max value to plot
    x_min : float, minimum value to plot, defaults to 0
    chars : int, number of characters to use for plot
    plot_char : str, character to use for bar portion of plot

    Returns
    -------
    str, of length chars
    """

    x_max = float(x_max)
    x_min = float(x_min)

    if x > x_max:
        return "#" * int(round(x_max))
    if x <= 0:
        a = 0
    else:
        a = int(((x - x_min) / (x_max - x_min)) * chars)
    return plot_char * a + " " * (chars - a)


def save_start(d):
    """Check the location for file saving is ok, in lew of more complete solutions
    i.e.
    http://stackoverflow.com/questions/9532499/check-whether-a-path-is-valid-in-python-without-creating-a-file-at-the-paths-ta/34102855#34102855
    """

    global f
    global fp
    global f_save

    fp = strftime('%Y_%m_%d_%H_%M_%S')
    fp = d + "/" + fp + "_INA219.csv"
    fp = os.path.normpath(fp)

    f_save = True
    f = open(fp, 'w')


def end():
    """Close open files"""
    try:
        f.close()
    except AttributeError:
        pass

    try:
        serial_port.close()
    except:
        pass

# register file close
register(end)

parser = argparse.ArgumentParser(description="pi_INA219 Terminal")
parser.add_argument("-n", "--number", help=("Number of samples to take, int for number or 'inf' for an infinite"
                                            " / continuous collection [default: 4]"))
parser.add_argument("-i", "--interval", help="Time between samples in seconds [default: 1.0]")
parser.add_argument("-u", "--units", help="Units to report, available: 'J', 'Wh', 'kWh' [default: 'J']")
parser.add_argument("-s", "--save", help="Directory to save data to")
parser.add_argument("-a", "--address", help="I2C address of INA219 on bus. [default: 0x40]")
parser.add_argument("-p", "--port", help="Serial port address to open [Raspberry Pi hardware port is: /dev/ttyAMA0]")
parser.add_argument("-b", "--baud", help="Serial port baud rate in kbps")
# parser.add_argument("-tx", "--tx", help="Commands to send for serial response")
parser.add_argument("-g", "--graph", help=("Append a simple bar plot of power to the terminal output with scale from"
                                           "zero to the number GRAPH in Watts"))
args = parser.parse_args()

if args.address:
    # for a non-default i2c address
    # TODO: test second ina219 at different address
    # so far tested only by passing default "0x40" as arg
    _address = int(args.address, 16)
    i = INA219(address=_address)
    instanced = True
    extras += "Using I2C address %s\n" % hex(_address)
else:
    i = INA219()
    extras += "Using default I2C address 0x40\n"

if args.number:
    if args.number == "inf":
        inf = True
    else:
        try:
            n = int(args.number)
        except ValueError:
            usage()
            sys.exit()
        if n < 1:
            inf = True

if args.interval:
    try:
        arg = float(args.interval)
    except ValueError:
        usage()
        sys.exit()
    if arg < min_dt:
        print("Sample interval %s seconds too low" % arg)
        usage()
        sys.exit()
    else:
        dt = arg

if args.graph:
    graph = True
    graph_max = float(args.graph)

if args.port and args.baud:
    # serial port power profiling
    # note: no error checking
    import serial
    port = args.port
    baud = args.baud
    serial_port = serial.Serial(port=port, baudrate=baud)
    port_monitor = True

if args.tx:
    # TODO: command to send to serial port
    port_tx = args.tx

if args.units:
    if args.units in i.available_units:
        i.set_energy_units(args.units)
    else:
        print("Unknown unit passed")
        usage()
        sys.exit()

if args.save:
    save_start(args.save)
    if not f_save:
        usage()
        sys.exit()
        # print("Saving to = %s" % _fp)

dt_header = "Sample interval = " + str(dt) + " s\n"

if inf:
    pn = "infinity"
    t_total = ""

else:
    pn = n
    t_total = "Samples collected in " + str(dt * n) + " s\n"

if fp is not None:
    extras += "Saving to: %s\n" % fp

header_terminal = ("unix time s".rjust(14) +
                   "elapsed s".rjust(10) +
                   "bus V".rjust(10) +
                   "shunt A".rjust(10) +
                   "power W".rjust(10) +
                   ("instant " + i.units).rjust(10) +
                   ("total " + i.units).rjust(10))

header_save = ("unix_time_s,elapsed_time_s,"
               "bus_voltage_V,shunt_current_A,"
               "power_W,sample_energy_" + i.units +
               "total_energy_" + i.units)

if port_monitor:
    extras += "Serial port open: %s @ %s kbps\n" % (port, baud)
    dt_header = "Sample interval = as received from serial port\n"
    t_total = ""

if port_tx:
    extras += "Sending serial port command: %s\n" % port_tx

header_common = ("INA219 Voltage, Power & Energy Measurement\n" +
                 extras +
                 "Number of samples = " + str(pn) + "\n" +
                 dt_header +
                 t_total +
                 "Energy units = " + i.units + "\n" +
                 "-" * len(header_terminal))

print(header_common)
print(header_terminal)

# begin sampling
t0 = 0
_n = 0
i_power = 0
t_elapsed = 0.0

while True:
    try:
        if not inf:
            if _n == n:
                break

        if port_monitor:
            if port_tx:
                serial_port.write(port_tx)
            try:
                data = serial_port.readline().decode("utf-8").strip()
            except UnicodeDecodeError:
                continue
        else:
            sleep(dt)

        i.get_energy_simple()
        t = time()
        if _n == 0:
            t0 = t
        else:
            t_elapsed = t - t0

        s = "{:.3f}".format(t)
        for _item in [t_elapsed, i.bus_voltage, i.i, i.p, i.e, i.e_total]:
            s = s + "{:10.3f}".format(_item)

        if graph:
            if _n == 0:
                i_power = 0
            else:
                i_power = i.p
            s = s + " | " + plotter(x=i_power, x_max=graph_max, x_min=1.0, chars=graph_size)

        if port_monitor:
            s = s + " || " + data

        print(s)

        if f_save:
            if _n == 0:
                f.write(header_common + "\n")
                f.write(header_save + "\n")

            s = ("%0.3f,%0.3f,%0.5f,%0.5f,%0.5f,%0.5f,%0.5f"
                 % (t, t_elapsed, i.bus_voltage, i.i, i.p, i.e, i.e_total))
            if port_monitor:
                s = s + " || " + data
            f.write(s + "\n")

        _n += 1
    except KeyboardInterrupt:
        break
