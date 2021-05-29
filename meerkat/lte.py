""" Meerkat Pycom LTE module
Note: Use global variables, if in each function you delare a new reference,
functionality is broken.

Refactored from post by user mattliddle at:
https://forum.pycom.io/topic/3021/gpy-with-hologram-io-sim?page=1
"""

import socket
import time
import pycom
from network import LTE


lte_modem = LTE()

def LTE_init(verbose=False):
    """Connect to LTE network using hologram.io SIM. If network connection
    is already in use, returns the LTE device's connection, otherwise will
    set up a new connection.

    Parameters
    ----------
    verbose : bool, print debug statements

    Returns
    -------
    network.LTE object with an active Internet connection
    """
    if lte_modem.isconnected():
        if verbose: print('LTE Modem already connected.')
        return

    # Modem does not connect successfully without first being reset.
    print('Resetting LTE modem ... ', end="")
    lte_modem.send_at_cmd('AT^RESET')
    if verbose: print('Resetting Done.')

    time.sleep(1)
    # While the configuration of the CGDCONT register survives resets,
    # the other configurations don't. So just set them all up every time.
    if verbose: print('Configuring LTE ', end='')
    lte_modem.send_at_cmd('AT+CGDCONT=1,"IP","hologram"')  # Changed this from origninal
    if verbose: print(".", end='')
    lte_modem.send_at_cmd('AT!="RRC::addscanfreq band=4 dl-earfcn=9410"') # changed band from 28 to 4. I dont know what earfcn=9410 is;
    if verbose: print(".", end='')
    lte_modem.send_at_cmd('AT+CFUN=1')
    if verbose: print('Ok')

    # If correctly configured for carrier network, attach() should succeed.
    if not lte_modem.isattached():
        if verbose: print("Attaching to LTE network ", end='')
        lte_modem.attach()
        lte_modem.init(debug=False)
        rsrpq = None
        fsm = None

        # if not, print the LTE state... maybe record this later
        while not lte_modem.isattached():
            if verbose:
                rsrpq2 = lte_modem.send_at_cmd('AT+CESQ').strip()
                if rsrpq2 != rsrpq:
                    rsrpq = rsrpq2
                    print(time.time(), rsrpq)
                fsm2 = lte_modem.send_at_cmd('AT!="fsm"').strip()
                if fsm != fsm2:
                    fsm=fsm2
                    print(time.time(), fsm)
            time.sleep(0.1)

    # Once attached, connect() should succeed.
    if not lte_modem.isconnected():
        if verbose: print("Connecting on LTE network ", end='')
        lte_modem.connect()
        while(True):
            if lte_modem.isconnected():
                if verbose: print(" OK")
                break
            if verbose: print('.', end='')
            time.sleep(1)

    # Once connect() succeeds, any call requiring Internet access will
    # use the active LTE connection.
    return lte_modem

def LTE_end(verbose=False):
    """Clean disconnection of the LTE network. This is required for
    future successful connections without a complete power cycle between.

    Parameters
    ----------
    verbose : bool, print debug statements
    """
    if verbose: print("Disonnecting LTE ... ", end='')
    lte_modem.disconnect()
    if verbose: print("OK")
    time.sleep(1)
    if verbose: print("Detaching LTE ... ", end='')
    lte_modem.dettach()
    if verbose: print("OK")

def LTE_deinit():
    """Deinitialize the LTE modem"""
    lte_modem.deinit()
