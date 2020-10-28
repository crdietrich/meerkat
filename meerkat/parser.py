"""Data parsing tools"""

import json
import pandas as pd


def pad_header(column_list, target_len):
    unnamed_columns = list(range(len(column_list), target_len))
    unnamed_columns = ["c" + str(c) for c in unnamed_columns]
    return column_list[:target_len] + unnamed_columns 

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
        columns = f.readline()
        row_0 = f.readline()
        
    column_n = len(row_0.split(","))
    column_names = pad_header(column_list=columns.strip().split(","),
                              target_len=column_n)
    
    meta = json.loads(sbang[2:])
    df = pd.read_csv(fp,
                     delimiter=meta['delimiter'],
                     comment=meta['comment'],
                     names=column_names,
                     header=0)
    df['datetime64_ns'] = pd.to_datetime(df[meta['time_format']])

    return meta, df
