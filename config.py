"""Configuration Values"""

# rate at which to collect sample data, in seconds
sensor_dt = 60

# location to save data to
data_directory = "/home/pi/data"

# header for local data savig
header = ("Time,Temp,DO,OR,pH,EC,TDS,SAL,SG,sensor_status,"
         +"CSO_now,CSO_recent,CSO_status,push_status,gform_status")

# in case a specific os target requires something specific
from os import linesep
newline = linesep

# push cron parameters
push_data_kwargs = {"hour":21,
                    "minute":5
                    }

# push ip:port destinations
# # lighthouse pi in the field
# ip = "25.16.55.200"
# port = "8080"

# Luke's pi for testing
ip = "25.112.184.183"
port = "7000"
