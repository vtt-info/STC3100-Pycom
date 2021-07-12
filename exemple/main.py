#  This is an exemple main file juste printing all values from the STC3100
#  Created by Valentin MONNOT
#  12/07/2021
#  MIT-License

import stc3100_i2c as stc3100
from machine import I2C
import utime

i2c = I2C(pins=('P10','P11'))

stc = stc3100.STC3100(i2c=i2c,resolution=0)
stc.start()

utime.sleep_ms(550) #Reading time for 14bits +50ms for safety see docs

ret = stc.read_all()

ret[0] = round(ret[0],0)
ret[1] = round((ret[1]/1000),3)
ret[2] = round(ret[2],1)
ret[3] = round(ret[3],1)

print("Charge : " + str(ret[0]) + " %\n")
print("Voltage : " + str(ret[1]) + " V\n")
print("Current : " + str(ret[2]) + " mA.h\n")
print("Temp : " + str(ret[3]) + " °C\n")


