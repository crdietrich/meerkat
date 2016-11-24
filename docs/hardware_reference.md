# Reference

## NMEA Sentences

### $GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47

Where:
    GGA             Global Positioning System Fix Data
    123519          Fix taken at 12:35:19 UTC
    4807.038        Latitude 48 deg 07.038'
    N               Latitude direction is North
                        N = North
                        S = South
    01131.000       Longitude 11 deg 31.000'
    E               Longitude direction is East
                        E = East
                        W = West
    1               Fix quality: 0 = invalid
                                1 = GPS fix (SPS)
                                2 = DGPS fix
                                3 = PPS fix
                                4 = Real Time Kinematic
                                5 = Float RTK
                                6 = estimated (dead reckoning) (2.3 feature)
                                7 = Manual input mode
                                8 = Simulation mode
    08              Number of satellites being tracked
    0.9             Horizontal dilution of position
    545.4           Altitude above mean sea level
    M               Altitiude units in Meters
    46.9            Height of geoid (mean sea level) above WGS84 ellipsoid
    M               Height of geoid units in Meters
    (empty field)   Time in seconds since last DGPS update
    (empty field)   DGPS station ID number
    *47             checksum data, always begins with *
     

### $GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*6A

Where:
    RMC             Recommended Minimum sentence C
    123519          Fix taken at 12:35:19 UTC
    A               Status A=active or V=Void.
    4807.038        Latitude 48 deg 07.038'
    N               Latitude direction is North
                        N = North
                        S = South
    01131.000       Longitude 11 deg 31.000'
    E               Longitude direction is East
                        E = East
                        W = West
    022.4           Speed over the ground in knots
    084.4           Track angle in degrees True
    230394          Date - 23rd of March 1994
    003.1           Magnetic Variation
    W               Magnetic Variation direction is East
                        N = North
                        S = South
                        E = East
                        W = West
    *6A             The checksum data, always begins with *
