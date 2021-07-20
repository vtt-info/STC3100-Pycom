#  Here you can find a lib for STC3100 working on Pycom, tested on Lopy4 OEM on custom board
#  Created by Valentin MONNOT based on https://github.com/st-sw/STC3100_GenericDriver
#  12/07/2021
#  MIT-License

import time, ubinascii
from array import array
#R/W registers
REG_MODE    = 0x0
REG_CTRL    = 0x1

#Read only registers
REG_CHARGE_LOW   = 0x2
REG_CHARGE_HIGH  = 0x3
REG_COUNTER_LOW  = 0x4
REG_COUNTER_HIGH = 0x5
REG_CURRENT_LOW  = 0x6
REG_CURRENT_HIGH = 0x7
REG_VOLTAGE_LOW  = 0x8
REG_VOLTAGE_HIGH = 0x9
REG_TEMP_LOW     = 0xA
REG_TEMP_HIGH    = 0xB

REG_ID0          = 0x18  # "Part type ID = 10h"
REG_ID1          = 0x19  # Unique id, must read 6 bytes
REG_ID7          = 0x1F  # Device ID CRC

#Address
STC_ADDR         = 0x70  # Default I2C address

#Scale

VOLTAGE_SCALE    = 2.44  # In mV. Cf. Doc part 7.2
TEMP_SCALE       = 0.125 # In °C. Cf. Doc part 7.2
CURRENT_SCALE    = 48210 # Cf. https://github.com/st-sw/STC3100_GenericDriver
CHARGE_SCALE     = 27443 # //

class STC3100:

    def __init__(self,address=STC_ADDR,i2c=None,resolution=0,shunt_res=30):

        self.address=address

        if i2c is None:
            raise ValueError('An I2C object is required') #i2c = machine.I2C(pins=('Pxx','Pxx'))
        
        self.i2c=i2c

        if resolution < 0 and resolution > 2:
            raise ValueError('Resolution should be 0 , 1 or 2')

        self.resolution = resolution*2 #Bits 1 and 2 of REG_MODE determine AD resolution. xx00x is 14bits xx01x is 13bits and xx10x is 12bits so x2

        if shunt_res < 10 and shunt_res > 50:
            raise ValueError('Shunt resistor should be between 10 and 50 mOhms')

        self.shunt_res = shunt_res

        data = 24 + self.resolution #send to REG_MODE 11xx0 start + calibration

        self.i2c.writeto_mem(self.address,REG_MODE,data) #Calibration

        time.sleep(0.5) #Max time used by AD for converting

        self.i2c.writeto_mem(self.address,REG_MODE,0) #Shutting down

    def start(self):
        data = 16 + self.resolution #send to REG_MODE 10xx0 to start
        self.i2c.writeto_mem(self.address,REG_MODE,data) #Start...

    def stop(self):
        self.i2c.writeto_mem(self.address,REG_MODE,0) #Stop...

    def reset(self):
        self.i2c.writeto_mem(self.address,REG_CTRL,2) #Reset...

    def read_charge(self):
        charge = ubinascii.hexlify(self.i2c.readfrom_mem(self.address,REG_CHARGE_LOW,2)).decode('ascii') #Read
        charge = charge[2:] + charge [:2] #Invert

        charge = int(charge,16)     #Hex to int
        
        charge = (charge * (CHARGE_SCALE/self.shunt_res)) / 4096 #Cf. https://github.com/st-sw/STC3100_GenericDriver

        return charge

    def read_voltage(self):
        voltage = ubinascii.hexlify(self.i2c.readfrom_mem(self.address,REG_VOLTAGE_LOW,2)).decode('ascii') #Read
        voltage = voltage[2:] + voltage[:2] #Invert

        voltage = int(voltage,16) #Hex to int
        voltage &= 0x0fff
        voltage *= VOLTAGE_SCALE  #Int to mV

        return voltage

    def read_current(self):
        current = ubinascii.hexlify(self.i2c.readfrom_mem(self.address, REG_CURRENT_LOW,2)).decode('ascii') #Read
        current = current[2:] + current[:2]
        current = int(current,16) #Hex to int

        current &= 0x3fff #Mask unused bits
                                                                    #
        if current >= 0x2000:                                       # Cf. https://github.com/st-sw/STC3100_GenericDriver
            current -= 0x4000                                       #
            current *= -1                                           #
                                                                    #
        current = (current * (CURRENT_SCALE/self.shunt_res)) / 4096 #

        return current

    def read_temp(self):
        temp = ubinascii.hexlify(self.i2c.readfrom_mem(self.address,REG_TEMP_LOW,2)).decode('ascii') #Read [8..15] bits
        temp = temp[2:] + temp [:2] #Invert

        temp = int(temp,16) #Hex to int
        temp &= 0x0fff
        temp *= TEMP_SCALE  #Int to °C

        return temp 

    def read_counter(self):
        counter = ubinascii.hexlify(self.i2c.readfrom_mem(self.address,REG_COUNTER_LOW,2)).decode('ascii')
        counter = counter[2:] + counter[:2] #Invert

        counter = int(counter,16) #Hex to int

    def read_all(self):
        data = ubinascii.hexlify(self.i2c.readfrom_mem(self.address,REG_CHARGE_LOW,10)).decode('ascii')
        print(data)
        charge = data[2:4] + data[:2]
        current = data[10:12] + data[8:10]
        voltage = data[14:16] + data[12:14]
        temp = data[18:] + data[16:18]

        #Process

        charge = int(charge,16)     #Hex to int
        charge = (charge * (CHARGE_SCALE/self.shunt_res)) / 4096 #Cf. https://github.com/st-sw/STC3100_GenericDriver

        current = int(current,16) #Hex to int
        current &= 0x3fff #Mask unused bits
                                                                    #
        if current >= 0x2000:                                       # Cf. https://github.com/st-sw/STC3100_GenericDriver
            current -= 0x4000                                       #
            current *= -1                                           #
                                                                    #
        current = (current * (CURRENT_SCALE/self.shunt_res)) / 4096 #

        voltage = int(voltage,16) #Hex to int
        voltage &= 0x0fff
        voltage *= VOLTAGE_SCALE  #Int to mV

        temp = int(temp,16) #Hex to int
        temp &= 0x0fff
        temp *= TEMP_SCALE  #Int to °C

        return array("f", (charge, voltage, current, temp))

    #Should always return 0x10 as it is the device id
    def read_part_id(self):
        return ubinascii.hexlify(self.i2c.readfrom_mem(STC_ADDR,REG_ID0,1)).decode('ascii')

    def read_unique_id(self):
        data = ubinascii.hexlify(self.i2c.readfrom_mem(STC_ADDR,REG_ID1,6)).decode('ascii')
        data = data[10:] + data[8:10] + data [6:8] + data [4:6] + data[2:4] + data [:2] 

        return data

    def read_crc_id(self):
        return ubinascii.hexlify(self.i2c.readfrom_mem(STC_ADDR,REG_ID7,1)).decode('ascii')
