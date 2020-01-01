# -*- coding: utf-8 -*-
"""
Created on Tue Oct  4 08:31:03 2016

@author: Colin
"""
# Reading gps data in MicroPython

Using a XXXX, the chip built into the Adafruit Ultimate GPS v3, we read UART serial data from pins (Y1,Y2).

First off, the incoming datatype bytes.
# 47
a = b'$GPRMC,153002.000,A,4744.0225,N,12218.7865,W,0.08,21.99,041016,,,D*'

# 54
a = b'GPRMC,141858.000,A,5749.8040,N,01200.6997,E,0.05,54.38,131006,,,A*'

We convert to unicode string.

b = a.decode('utf-8')

# and calc the CRC on the string:
AFTER the '$' character
to
INCLUDING the '*' character

if b[0] == '$':
    c = b[1:]
else:
    c = b


def crc(line):
    """Calculate the cyclic redundancy check (CRC) for a string
    Parameters
    ----------
    line : str, characters to calculate crc
    Returns
    -------
    crc : str, in hex notation
    """

    crc = ord(line[0:1])
    for n in range(1,len(line)-1):
        crc = crc ^ ord(line[n:n+1])
    return '%X' % crc


d = crc(c)


# Example
#print NMEA_CRC("GPRMC,141858.000,A,5749.8040,N,01200.6997,E,0.05,54.38,131006,,,A*")
# returns "54"
# then try without the $
# print NMEA_CRC("GPRMC,141858.000,A,5749.8040,N,01200.6997,E,0.05,54.38,131006,,,A*")
# returns "54"
#original is $GPRMC,141858.000,A,5749.8040,N,01200.6997,E,0.05,54.38,131006,,,A*54
#- Edited by Mr Dove 19.10.2006, 13:05 -