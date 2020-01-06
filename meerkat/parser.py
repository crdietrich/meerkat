"""Data parsing tools"""

import json
import pandas as pd


def csv_resource(fp):
    """Parse a .csv file generated with Meerkat

    Parameters
    ----------
    fp : filepath to saved data

    Returns
    -------
    meta : dict, metadata describing data
    df : Pandas DataFrame, data recorded from device(s) described in meta
    """

    with open(fp, 'r') as f:
        sbang = f.readline()
    meta = json.loads(sbang[2:])
    df = pd.read_csv(fp,
                     delimiter=meta['delimiter'],
                     comment=meta['comment'])
    df['datetime64_ns'] = pd.to_datetime(df[meta['time_format']])

    return meta, df
