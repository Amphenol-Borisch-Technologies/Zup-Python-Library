
from ABT_ZUp import *
# A ZUp is a list object containing 4 elements: [Address, Voltage, Amperage, Foldback]:
# - Address is an integer from 1 to _MAX_ZUPs, currently 31, indexed at _INDEX_ADDRESS, or 0.
# - Voltage is a float specific to the ZUp model, indexed at _INDEX_VOLTAGE, or 1.
# - Amperage is a float specific to the ZUp model, indexed at _INDEX_AMPERAGE, or 2.
# - Foldback is a string value where Foldback.upper() is in set {'FLD_ON', 'FLD_OFF'}, indexed at _INDEX_FOLDBACK, or 3.
#
# ZUps is a list of ZUp lists, containing 1 to _MAX_ZUPs elements, currently 31.
#   [[Address1, Voltage1, Amperage1, Foldback1], [Address2, Voltage2, Amperage2, Foldback2], [Address3, Voltage3, Amperage3, Foldback3]...
#   ...[Address31, Voltage31, Amperage31, Foldback31]].

ZUps_off(Addresses=[1,2,3,4,5,6], SerialPort='COM1', Baud=9600)

for V in range (1,20,1):
    ZUps_ON(ZUps=[ZUp(Address=1, Voltage=V, Amperage=1, Foldback='FLD_off'), 
                  ZUp(Address=2, Voltage=V, Amperage=1, Foldback='FLD_ON'), 
                  ZUp(Address=3, Voltage=V, Amperage=1, Foldback='FLD_off'), 
                  ZUp(Address=4, Voltage=V, Amperage=1, Foldback='FLD_ON'), 
                  ZUp(Address=5, Voltage=V, Amperage=1, Foldback='FLD_off'), 
                  ZUp(Address=6, Voltage=V, Amperage=1, Foldback='FLD_ON')], SerialPort='COM1', Baud=9600)

A = 1
for V in range(1,10,1):
    if(V %2 == 0):
        # V is an even number, so increment ZUps 2, 4 & 6.
        ZUps_ON(ZUps=[[2, (V-1)*2, A, 'FLD_off'], [4, (V-1)*2, A, 'FLD_off'], [6, (V-1)*2, A,' FLD_off']], SerialPort='COM1', Baud=9600)
    else:
        # V is an odd number, so increment ZUps 1, 3 & 5.
        ZUps_ON(ZUps=[[1, V, A, 'FLD_ON'], [3, V, A, 'FLD_ON'], [5, V, A, 'FLD_ON']], SerialPort='COM1', Baud=9600)

ZUps_off(Addresses=[1,2,3,4,5,6], SerialPort='COM1', Baud=9600)

V = 1
while V < 5.25:
    ZUps_ON(ZUps=[[1, V, 1, 'FLD_off']], SerialPort='COM1', Baud=9600)    
    V += 0.25

for Address in range(1,7,1):
    V,A = Address,Address
    ZUps_ON(ZUps=[[Address,V,A,'FLD_off']], SerialPort='COM1', Baud=9600)

ZUps_off(Addresses=[1,2,3,4,5,6], SerialPort='COM1', Baud=9600)

for Address in range(6,0,-1):
    V,A = Address,Address
    ZUps_ON(ZUps=[[Address,V,A,'FLD_off']], SerialPort='COM1', Baud=9600)

ZUps_off(Addresses=[1,2,3,4,5,6], SerialPort='COM1', Baud=9600)
