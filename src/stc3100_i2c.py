#  Here you can find a lib for STC3100 working on Pycom, tested on Lopy4 OEM on custom board
#  Created by Valentin MONNOT
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

VOLTAGE_SCALE    = 2.44  # In mV. See doc part 7.2
TEMP_SCALE       = 0.125 # In °C. //
CURRENT_SCALE    = 0.2   # In mA.h. See doc part 7.1


class STC3100:

    def __init__(self,address=STC_ADDR,i2c=None,resolution=0):

        self.address=address

        if i2c is None:
            raise ValueError('An I2C object is required') #i2c = machine.I2C(pins=('Pxx','Pxx'))
        
        self.i2c=i2c

        if resolution < 0 and resolution > 2:
            raise ValueError('Resolution should be 0 , 1 or 2')
            
        self.resolution = resolution*2 #Bits 1 and 2 of REG_MODE determine AD resolution. xx00x is 14bits xx01x is 13bits and xx10x is 12bits so x2

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
        charge = ubinascii.hexlify(self.i2c.readfrom_mem(self.address,REG_CHARGE_HIGH,1)).decode('ascii') #Read [8..15] bits
        charge += ubinascii.hexlify(self.i2c.readfrom_mem(self.address,REG_CHARGE_LOW,1)).decode('ascii') #Read [0..7] bits

        charge = int(charge,16)     #Hex to int
        charge = (charge/65535)*100 #Int to %

        return charge

    def read_voltage(self):
        voltage = ubinascii.hexlify(self.i2c.readfrom_mem(self.address,REG_VOLTAGE_HIGH,1)).decode('ascii') #Read [8..15] bits
        voltage += ubinascii.hexlify(self.i2c.readfrom_mem(self.address,REG_VOLTAGE_LOW,1)).decode('ascii')  #Read [0..7] bits

        voltage = int(voltage,16) #Hex to int
        voltage *= VOLTAGE_SCALE  #Int to mV

        return voltage

    def read_current(self):
        current = self.i2c.readfrom_mem(self.address,0x7,1).decode('ascii') #Read [8..15] bits
        if current == '?': #I don't know why but sometimes '?' is here when there should be a 0. 3.7A in idle on a lopy4 seems obviously wrong...
            current = '0'
        else : 
            current = ubinascii.hexlify(current)
        current += ubinascii.hexlify(self.i2c.readfrom_mem(self.address,REG_CURRENT_LOW,1)).decode('ascii')  #Read [0..7] bits
        print(current)
        current = int(current,16) #Hex to int
        print(current)
        current *= CURRENT_SCALE  #Int to mA.h

        return current

    def read_temp(self):
        temp = ubinascii.hexlify(self.i2c.readfrom_mem(self.address,REG_TEMP_HIGH,1)).decode('ascii') #Read [8..15] bits
        temp += ubinascii.hexlify(self.i2c.readfrom_mem(self.address,REG_TEMP_LOW,1)).decode('ascii')  #Read [0..7] bits

        temp = int(temp,16) #Hex to int
        temp *= TEMP_SCALE  #Int to mA.h

        return temp 

    def read_counter(self):
        counter = ubinascii.hexlify(self.i2c.readfrom_mem(self.address,REG_COUNTER_HIGH,1)).decode('ascii') #Read [8..15] bits
        counter += ubinascii.hexlify(self.i2c.readfrom_mem(self.address,REG_COUNTER_LOW,1)).decode('ascii')  #Read [0..7] bits

        counter = int(counter,16) #Hex to int

    def read_all(self):
        charge = self.read_charge()
        voltage = self.read_voltage()
        current = self.read_current()
        temp = self.read_temp()

        return array("f", (charge, voltage, current, temp))




        
