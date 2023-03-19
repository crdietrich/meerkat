"""Data parsing tools"""

import json
import pandas as pd


## Data specific headers ##

#  Global Positioning System Fix Data
#  http://aprs.gids.nl/nmea/#gga
GGA_columns = ["nmea_type", "UTC_time", "latitude", "NS", "longitude", "EW", "quality", "n_satellites",
               "horizontal_dilution", "altitude", "M", "geoidal_separation", "M", 
               "age_sec_diff", "diff_id", "checksum"]

# GPS DOP and active satellites
# http://aprs.gids.nl/nmea/#gsa
GSA_columns = (["nmea_type", "mode", "mode_fix"] + 
               ["sv" + str(n) for n in list(range(12))] + 
               ["pdop", "hdop", "vdop", "checksum"])

# GPS DOP and active satellites
# http://aprs.gids.nl/nmea/#gsv
GSV_columns = (["nmea_type", "total_messages", "message_number"] +  
               ["total_sv_in_view", "sv_prn_number", "elev_degree", "azimuth", "snr"] * 4)

# Recommended minimum specific GPS/Transit data
# http://aprs.gids.nl/nmea/#rmc
RMC_columns = ["nmea_type", "UTC_time", "valid", "latitude", "NS", "longitude", "EW", "speed_knots",
               "true_course", "date", "variation", "variation_EW", "checksum"]

# Track made good and ground speed
# http://aprs.gids.nl/nmea/#vtg
VTG_columns = ["nmea_type", "track_made_good", "T", "NA", "NA", "speed_knots", "N", 
               "speed_km_hr", "K"]

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
    meta = json.loads(sbang[2:])
    df = pd.read_csv(fp,
                     delimiter=meta['delimiter'],
                     comment=meta['comment'],
                     quotechar='"')
    df['datetime64_ns'] = pd.to_datetime(df.timestamp)
    return meta, df
