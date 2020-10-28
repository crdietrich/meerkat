from machine import I2C 
from machine import RTC
DS3231_I2C_ADDR = 104

def bcd2dec(bcd):
    return (((bcd & 0b11110000)>>4)*10 + (bcd & 0b00001111));

def dec2bcd(dec):
    t = dec // 10;
    o = dec - t * 10;
    return (t << 4) + o;

class DS3231:
    def __init__(self):
        self.ds3231 = I2C(0, I2C.MASTER, baudrate=100000, pins=('P23', 'P22')) #sda=P23, scl=P22
        self.rtc = RTC()
        
    def loadTime(self):
        if DS3231_I2C_ADDR in self.ds3231.scan():
            data = self.ds3231.readfrom_mem(DS3231_I2C_ADDR, 0, 7)
            ss=bcd2dec(data[0] & 0b01111111)
            mm=bcd2dec(data[1] & 0b01111111)
            if data[2] & 0b01000000 > 0:
                hh=bcd2dec(data[2] & 0b00011111)
                if data[2] & 0b00100000 >0:
                    hh+=12
            else:
                hh=bcd2dec(data[2] & 0b00111111)
            DD=bcd2dec(data[4] & 0b00111111)
            MM=bcd2dec(data[5] & 0b00011111)
            YY=bcd2dec(data[6])
            if data[5] & 0b10000000 > 0:
                YY=YY+2000
            else:
                YY=YY+1900
            self.rtc.init((YY,MM,DD,hh,mm,ss))
            return True
        else:
            print("DS3231 not found on I2C bus at %d" % DS3231_I2C_ADDR)
            return False


    def saveTime(self):
        (YY,MM,DD,hh,mm,ss,micro,tz) = self.rtc.now()
        self.ds3231.writeto_mem(DS3231_I2C_ADDR, 0,dec2bcd(ss));
        self.ds3231.writeto_mem(DS3231_I2C_ADDR, 1,dec2bcd(mm));
        self.ds3231.writeto_mem(DS3231_I2C_ADDR, 2,dec2bcd(hh));
        self.ds3231.writeto_mem(DS3231_I2C_ADDR, 4,dec2bcd(DD));
        if YY >= 2000:
            self.ds3231.writeto_mem(DS3231_I2C_ADDR, 5,dec2bcd(MM) | 0b10000000);
            self.ds3231.writeto_mem(DS3231_I2C_ADDR, 6,dec2bcd(YY-2000));
        else:
            self.ds3231.writeto_mem(DS3231_I2C_ADDR, 5,dec2bcd(MM));
            self.ds3231.writeto_mem(DS3231_I2C_ADDR, 6,dec2bcd(YY-1900));
