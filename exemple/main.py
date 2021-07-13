#  This is an exemple main file juste printing all values from the STC3100
#  Created by Valentin MONNOT
#  12/07/2021
#  MIT-License

import stc3100_i2c as stc3100
from machine import I2C
import time

i2c = I2C(pins=('P10','P11'))

stc = stc3100.STC3100(i2c=i2c,resolution=0, shunt_res=50)
stc.start()

time.sleep(1)

ret = stc.read_all()

ret[0] = round(ret[0],1)
ret[1] = round((ret[1]/1000),3)
ret[2] = round(ret[2],1)
ret[3] = round(ret[3],1)

print("Charge : " + str(ret[0]) + " mA.h\n")
print("Voltage : " + str(ret[1]) + " V\n")
print("Current : " + str(ret[2]) + " mA\n")
print("Temp : " + str(ret[3]) + " °C\n")


