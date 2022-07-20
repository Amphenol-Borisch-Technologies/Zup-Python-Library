"""
    TDK-Lambda Zup power supply programmatic control for the Corelis JTAG test system.
"""
import sys
import ast
import serial # https://pythonhosted.org/pyserial/#
from Zup import Zup

def main():
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

    for address in zups:
        zups[address].clear_registers()
        zups[address].set_under_voltage_protection(zups[address].UVP['min'])
        zups[address].set_over_voltage_protection(zups[address].OVP['MAX'])
    # Clears Zup communication & alarm registers.
    #  - It would seem sensible to include this in Zup.__init__(), but that would erase any existing register
    #    alarms when re-connecting to Zups, preventing appropriate actions to accomodate them.
    #    But for our purposes here clearing without first reading is preferable, as we don't care about
    #    prior behavior, but instead just want to get on with present/future behavior.
    # Set Zup UVPs/OVPs to their specific min/MAX values so we can most easily set voltages afterwards.
    # - Setting UVP/OVP is best performed by first setting UVP = UVP['min'], OVP = OVP['MAX'],
    #   then setting desired Voltage, then finally resetting UVP/OVP to desired values so
    #   UVP/OVP values don't interfere with setting Voltages.  More on this shortly.

    zup_configs = ast.literal_eval(sys.argv[1])
    for z in zup_configs:
        ZA, V, A = z[0], z[1], z[2] # Zup Address, Volts, Amperes
        zups[ZA].set_voltage(V)
        zups[ZA].set_amperage(A)
        # Selectively set voltages & amperages of the specific Zups actively needed.
        zups[ZA].set_under_voltage_protection(zups[ZA].get_voltage_set() * 0.90)
        zups[ZA].set_over_voltage_protection( zups[ZA].get_voltage_set() * 1.10)
        # Above sets UVPs/OVPs to 90%/110% of current set voltages.
        # - Note that below inequality *always* applies between UVP, Voltage & OVP:
        #         UVP['min'] ≤ UVP ⪅ Voltage*95% ⪅ Voltage ⪅ Voltage*105% ⪅ OVP ≤ OVP['MAX']
        #   - The ⪅ symbol denotes less than or approximately equal.
        #   - The ±5% difference is approximate, possibly due to roundoff in the Zup; safer to use ≥ ±7.5%.
        #   - Violating above inequality doesn't end well, hence set UVP/OVP to min/MAX, set desired Voltage,
        #     then reset UVP/OVP appropriately.

    for z in zup_configs: zups[z[0]].set_power('On')
    # Finally, power on specified Zup supplies as simultaneously as possible, in its own exclusive for/in loop.

    serial_port.close()
    # Lastly, we explicitly clean up after ourselves with the above statement.

if __name__ == '__main__':
    main()
