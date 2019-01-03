# -*- coding: utf-8 -*-
"""Meerkat thermistor calculation methods 
and Semitec 103AT-2 thermistor driver
using ADS1x15 ADC"""
__author__ = "Colin Dietrich"
__copyright__ = "2018"
__license__ = "MIT"

from math import log


def steinhart_hart(r, a, b, c, degrees='celcius'):
    """Calculate temperature from a resistance based on the
    Steinhart-Hart equation.  Defaults to degres in Celcius
    output.

    Parameters
    ----------
    r : float, resistance of thermister
    a : float, coeffient
    b : float, coeffient
    c : float, coeffient
    degrees : str, type of degress - either 'celcius' or 'kelvin'

    Returns
    -------
    t : float, temperature in Kelvin
    """
    t = 1.0 / (a + b * log(r) + c * (log(r) ** 3))
    if degrees == 'celcius':
        t = KtoC(t)
    return t


def KtoC(k):
    """Convert temperature in Kelvin to Celsius

    Parameters
    ----------
    k : float, temperature in degrees Kelvin

    Returns
    -------
    float, temperature in degrees Celsius
    """
    return k - 273.15


def CtoK(k):
    """Convert temperature in Celcius to Kelvin

    Parameters
    ----------
    k : float, temperature in degrees Celsius

    Returns
    -------
    float, temperature in degrees Kelvin
    """
    return k + 273.15


def compose_array(t1, t2, t3, r1, r2, r3, degrees='celcius', verbose=False):
    """Compose a matrix of coeffients for the Steinhart-Hart
    Equation.  Defaults to degres in Celcius for inputs.

    Parameters
    ----------
    t1, t2, t3 : float, temperatures in degrees C
    r1, r2, r3 : float, resistances in ohms
    degrees : str, type of degress - either 'celcius' or 'kelvin'
    verbose : print debug statements

    Returns
    -------
    list : nested list of 3 rows and 4 columns (a0, a1, a2, T)
    """

    array = []
    for (t, r) in zip([t1, t2, t3], [r1, r2, r3]):
        if degrees == 'celcius':
            t = CtoK(t)
        a0 = 1
        a1 = log(r)
        a2 = log(r) ** 3
        at = 1 / t
        if verbose:
            print('{:6.2f} {:>7} {:>7.4f} {:>9.4f} {:>4.3E}'.format(t, r, a1,
                                                                    a2, at))
        array.append([a0, a1, a2, at])
    return array

def gauss(A):
    """Solve a linear system of equations with Gaussian Elimination
    Taken almost wholesale from:  
    https://martin-thoma.com/solving-linear-equations-with-gaussian-elimination/
    
    Parameters
    ----------
    A : nested list of 3 rows and 4 columns (a0, a1, a2, T)
    
    Returns
    -------
    list of floats, coefficients for a0, a1, a2
    """
    
    # prevent inplace changing of source A
    _A = [x.copy() for x in A]
    n = len(_A)
    
    for i in range(0, n):
        # Search for maximum in this column
        maxEl = abs(_A[i][i])
        maxRow = i
        for k in range(i+1, n):
            if abs(_A[k][i]) > maxEl:
                maxEl = abs(_A[k][i])
                maxRow = k

        # Swap maximum row with current row (column by column)
        for k in range(i, n+1):
            tmp = _A[maxRow][k]
            _A[maxRow][k] = _A[i][k]
            _A[i][k] = tmp

        # Make all rows below this one 0 in current column
        for k in range(i+1, n):
            c = -_A[k][i]/_A[i][i]
            for j in range(i, n+1):
                if i == j:
                    _A[k][j] = 0
                else:
                    _A[k][j] += c * _A[i][j]

    # Solve equation Ax=b for an upper triangular matrix A
    x = [0 for _ in range(n)]
    for i in range(n-1, -1, -1):
        x[i] = _A[i][n]/_A[i][i]
        for k in range(i-1, -1, -1):
            _A[k][n] -= _A[k][i] * x[i]
    return x

class Semitec103AT(object):
    def __init__(self):
        self.cal_ts = list(range(-50, 115, 5))
        self.cal_rs = [_t * 1000 for _t in[329.5, 247.7, 188.5, 144.1, 111.3, 86.43, 67.77, 53.41, 42.47, 33.90,
                                              27.28, 22.05, 17.96, 14.69, 12.09, 10.00, 8.313, 6.940, 5.827, 4.911,
                                              4.160, 3.536, 3.020, 2.588, 2.228, 1.924, 1.668, 1.451, 1.266, 1.108,
                                              0.9731, 0.8572, 0.7576]]

    def find_nearest(self, r):
        """Find nearest resistances to a given resistance

        Parameters
        ----------
        r : float, resistance in ohms

        Returns
        -------
        list of floats, t1, t2, t3, r1, r2, r3
        Where: tn is temperature at n
               rn is resistance in ohms at n
        """

        _t = []
        _r = []
        n = min(range(len(self.cal_rs)), key=lambda _: abs(self.cal_rs[_] - r))
        for di in [-1, 0, 1]:
            i = n + di
            _t.append(self.cal_ts[i])
            _r.append(self.cal_rs[i])
        return _t + _r

    def find_hi_low(self, t1, t2):
        """Find mid temperature in thermistor calibration table

        Parameters
        ----------
        t1 : float, lower temperature in degrees C
        t2 : float, upper temperature in degrees C

        Returns
        -------
        list of floats, t1, t2, t3, r1, r2, r3
        Where: tn is temperature at n
               rn is resistance in ohms at n
        """

        temp = list(range(t1, t2, 5))
        mid = temp[len(temp) // 2]
        tr = dict(zip(self.cal_ts, self.cal_rs))
        return [t1, mid, t2, tr[t1], tr[mid], tr[t2]]
