"""
    "TDK", "TDK-Lambda" & "Zup" are registered trademarks of the TDK Corporation.
    "Python" is a registered trademark of the Python Software Foundation.
    pySerial Copyrighted by Chris Liechti.
    pytest Copyrighted by Holger Krekel and pytest-dev team.
    This script Copyright Amphenol Borisch Technologies, 2022
    - https://www.borisch.com/

    Example usage of  Zup class.
"""
import serial # https://pythonhosted.org/pyserial/#
from Zup import Zup

# For this example script, used below Zups:
# Address     Model:
# -------    --------------
#    1     Zup(20V-20A)
#    2     Zup(20V-10A)
#    3     Zup(20V-10A)
#    4     Zup(20V-10A)
#    5     Zup(20V-10A)
#    6     Zup(36V-6A)
serial_port = serial.Serial(port='COM1', baudrate=9600, bytesize=serial.EIGHTBITS,
                            parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE,
                            timeout=10, xonxoff=True, rtscts=False,
                            write_timeout=10, dsrdtr=False, inter_byte_timeout=None)

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

for address in zups: zups[address].clear_registers()
# Clears Zup communication & alarm registers.
# It would seem sensible to include this in Zup.__init__(), but that would erase any existing register
# alarms when re-connecting to Zups, preventing appropriate actions to accomodate them.
# But for our purposes here clearing without first reading is preferable, as we don't care about
# prior behavior, but instead just want to get on with present/future behavior.

for address in zups: zups[address].set_power('Off')
# Power all zup outputs off prior to configuring them any further.
# Powering off the zup objects in their own for/in loop like this ensures they're all powered off
# as simultaneously as possible, as is typically desirable.

for address in zups:
    zups[address].set_under_voltage_protection(zups[address].UVP['min'])
    zups[address].set_over_voltage_protection(zups[address].OVP['MAX'])
# Set Zup UVPs/OVPs to their specific min/MAX values so we can most easily set voltages afterwards.
# - Setting UVP/OVP is best performed by first setting UVP = UVP['min'], OVP = OVP['MAX'],
#   then setting desired Voltage, then finally resetting UVP/OVP to desired values so
#   UVP/OVP values don't interfere with setting Voltages.  More on this shortly.

zups[1].set_voltage(3.3)   ;  zups[1].set_amperage(1.0)
zups[2].set_voltage(6.0)   ;  zups[2].set_amperage(1.0)
zups[6].set_voltage(28.0)  ;  zups[6].set_amperage(1.5)
# Now selectively set voltages & amperages of the specific Zups actively needed.
# For this application, the Zup supplies with addresses 1, 2 & 6 are needed, so their voltages &
# amperages are re-configured while those with addresses 3, 4 & 5 are left configured with
# their pre-script voltages/amperages, but still de-powered from 2nd for/in loop above.

for address in (1,2,6):
    zups[address].set_under_voltage_protection(zups[address].get_voltage_set() * 0.90)
    zups[address].set_over_voltage_protection( zups[address].get_voltage_set() * 1.10)
# Above sets UVPs/OVPs to 90%/110% of current set voltages.
# - Note that below inequality *always* applies between UVP, Voltage & OVP:
#         UVP['min'] ≤ UVP ⪅ Voltage*95% ⪅ Voltage ⪅ Voltage*105% ⪅ OVP ≤ OVP['MAX']
#   - The ⪅ symbol denotes less than or approximately equal.
#   - The ±5% difference is approximate, possibly due to roundoff in the Zup; safer to use ≥ ±7.5%.
#   - Violating above inequality doesn't end well, hence set UVP/OVP to min/MAX, set desired Voltage,
#     then reset UVP/OVP appropriately.

for address in (1,2,6): zups[address].set_power('On')
# Finally, power on Zup supplies with addresses 1, 2 & 6 as simultaneously as possible,
# in their own exclusive for/in loop.

for address in (3,4,5):
    zups[address].set_voltage(4.0)
    zups[address].set_amperage(1.0)
for address in (3,4,5): zups[address].set_power('On')
i = 4
while i <= 6.0:
    for address in (3,4,5): zups[address].set_voltage(i)
    i += 0.1
while i >= 4.0:
    for address in (3,4,5): zups[address].set_voltage(i)
    i -= 0.1
# Occasionally it's useful to ramp supplies up/down to ensure that whatever they're powering continues
# working correctly with varying input voltages.  Here input varies as 5.0VDC ±20%.

for address in (3,4,5): zups[address].set_power('Off')
# zups[1], zups[2] & zups[6] will remain powered after this script terminates.

for address in zups: zups[address].set_remote_mode('Remote Unlatched')
serial_port.close()
# Lastly, we explicitly clean up after ourselves with the above 2 statements.
# - Finalizer Zup.__del__() attempts to execute Zup.set_remote_mode('Remote Unlatched')
#   to enable Zup front-panel controls.
# - However, Python's __del__() finalizer method isn't guaranteed to run, so it's best to explicitly
#   invoke Zup.set_remote_mode('Remote Unlatched') instead of depending on Zup.__del__().
