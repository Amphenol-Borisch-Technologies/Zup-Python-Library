"""
    TDK-Lambda Zup power supply programmatic control for the Corelis JTAG test system.
"""
import serial # https://pythonhosted.org/pyserial/#
from Zup import Zup

# For this script, used below Zups:
# Address     Model:
# -------    --------------
#    1     Zup(10V-20A)
#    2     Zup(10V-20A)
#    3     Zup(10V-20A)
#    4     Zup(20V-10A)
#    5     Zup(20V-10A)
#    6     Zup(36V-6A)
serial_port = serial.Serial(port='COM1', baudrate=9600, bytesize=serial.EIGHTBITS,
                            parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE,
                            timeout=2, xonxoff=True, rtscts=False,
                            write_timeout=0, dsrdtr=False, inter_byte_timeout=None)

zups = {}
for address in range(1,7,1): zups.update({address : Zup(address, serial_port)})
# Create and add 6 Zup class objects to dict 'zups'.
# 'zups' thus models a physical chain of 6 Zup supplies all connected to COM1, with addresses 1 to 6.
#
# Notes:
# - The Zup.__init__() initializer disables Zup front-panel controls, permitting only programmatic control
#   (like this script), preventing operator interference.
#   - It also prevents operator intervention, so keep that in mind!
# - Initializer __init__() deliberately doesn't issue any other Zup commands:
#   - Instantiating a Zup object literally only establishes communication with it.
#   - Whatever prior state a Zup has before __init__() executes remains entirely intact after execution:
#     - If a Zup's power was set to 5.0V/1.0A with output on before __init__() executes, it will be powered
#       on identically at 5.0V/1.0A after __init__().
#     - It may seem counter-intuitive, but this behavior is actually useful & preferable to performing
#       any other initializations during __init__().
#   - Use Zup class methods to individually configure specific Zup states; set power output off or on,
#     change voltage/amperage, etc.
#   - Or, Zup.configure() can be invoked to generically configure a Zup supply with multiple settings if desired.

for address in zups: zups[address].set_power('Off')
# Power all zup outputs off prior to configuring them any further.
# Powering off the zup objects in their own for/in loop like this ensures they're all powered off
# as simultaneously as possible, as is typically desirable.

for address in zups: zups[address].set_remote_mode('Remote Unlatched')
serial_port.close()
# Lastly, we explicitly clean up after ourselves with the above 2 statements.

