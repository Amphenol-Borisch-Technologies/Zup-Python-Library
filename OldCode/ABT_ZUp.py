# Reference 'TDK-Lambda ZUp Power Supplies User Manual, IA549-04-01R'.
# - Available at https://product.tdk.com/en/system/files?file=dam/doc/product/power/switching-power/prg-power/instruction_manual/ZUp-uSerialPort-manual.pdf.
# - Copied to 'P:\Test\Engineers\JTAG\TDK-Lambda ZUp Power Supplies\TDK-Lambda ZUp Power Supplies User Manual, IA549-04-01R.pdf'.
#
# Purpose of this Python library is to eliminate occasional ZUp programming glitches, wherein ZUp supplies don't turn on and/or off as programmed:
# - Occasionally some ZUp supplies fail to power on or off as programmed by Rafael's Windows batch files.
# - When failing to power on, the Boundary Scan test will fail.
# - When failing to power off, technicians may remove a CCA from the fixture jig while still partly powered.
# - And it's always sub-optimal for a CCA to have some but not all of its power supplies applied to it.
#
# Another purpose is to allow reading ZUp status registers & model IDs:
# - This allows checking correct application of voltage & current; 5.0V @ 1.0A was programmed, but what's actually
#   being output by the ZUp?  Actual Voltages/Amperages can be read from each ZUp & compared to Set Voltages/Amperages.
# - Querying status allows checking the ZUp's Alarm & Error Codes registers, which indicate if programming or
#   communication errors occurred.
# - Lastly, querying ZUp model ID allows verification of voltage/current within ZUp model specifications prior to programming.
#   Can't program a ZUp 20-10 at 36V/10A; limits are 20V/10A.
#   Can't program a ZUp 36-6  at 36V/10A; limits are 36V/6A.
#   Instead, raise a ValueError to inform programmer of exceeding ZUp specifications.
#
# FWIW, suspect most of the on/off glitches are due to 'TDK-Lambda ZUp Power Supplies User Manual, IA549-04-01R', paragraph 5.6.1:
#    - The average command processing time of the ZUp Serues is 15mSec.
#      It is not recommended to send strings of commands to the ZUp power supply without considering the processing time.
#    - For query commands ( ? , ! ) wait until the ZUp reply message has been completed before sending a new command.
#    - 10mSec minimum delay is required before sending: ADRxx: command.
#    - Additional 30mSec after: ADRxx: command.
# - There's no simple method to implement 10, 15 or 30mSec processing delays with a Windows batch file, so Rafael eventually
#   settled on programming the ZUps at 2400 Baud, which appears mostly slow enough to provide processing delays, and to mostly work.
# - Power on/off glitches appear more common at any Baud rate > 2400.
# - The obvious solution is to slow the ZUp's Baud rate to its minimum of 300, but at < 2400 Baud, ZUp supplies
#   don't turn on/off highly simultaneously; there's a sub-optimal & noticeable time lag between each one
#   activating/deactivating.
# - It's best for a CCA to apply all its supplies as simultaneously as possible, which can't be done at < 2400 Baud,
#   and can't be reliably done at >= 2400 Baud with a batch file.  Rock, hard place...
# Fortunately, Python's time library has a highly accurate .sleep() method, which is used herein to correctly implement command delays.
# This allows the maximum ZUp Baud rate of 9600, which activates/deactivates the ZUp supplies as simultaneously as possible.
# Stack Overflow discusses time.sleep() accuracy/resolution to 1mSec, sufficient to implement 10, 15 & 30 mSec processing delays.
#  - https://stackoverflow.com/questions/1133857/how-accurate-is-pythons-time-sleep.
#
# Note that ZUps_ON executes in atomic, 'all or nothing' sections, wherein each section is completed successfully, or ZUps_ON raises an Error and aborts.
# This is to protect the UUT being powered, and to ensure each section works correctly, else execution is halted.
# - Goal is to prevent turning some ZUps on but not others, leaving the UUT in an invalid, potentially destructive, power state.
# - ZUps_ON's verifications only check for valid Addresses, Voltages and Amperages; they won't prevent user errors.
#   - That is, if a user incorrectly requests a UUT's +3.3V supply be powered to +15V, ZUps_ON will happily do so.  Oops!
#   - Verifications do check each ZUp supply meets it's requested Voltage & Amperage specifications though.
#     If the above UUT's +3.3V supply connects to a ZUp 6V-33A (which cannot ower +15V) an error will occur, and 
#     the +3.3V supply won't be powered to +15V.  Whew!
#   - Verifications should also weed out typographical errors, as long as they exceed valid ZUp Voltage/Amperage specifications.
#
# Finally, UVP & OVP either don't program correctly or read back correctly; they consistently read back at 0.1V lower than programmed.
# - Programming ':UVP02.7;' & ':OVP03.3;' should result in 'UP02.7' & 'OP03.3' when queried with ':UVP?; & ':OVP?;'.
# - That is, programming UVP & OVP to 2.7V & 3.3V respectively should result in reading 2.7V & 3.3V back from the ZUp.
#   But, both read back at 0.1V lower than programmed; 'UP02.6' & 'OP03.2'
# - Unsure why, but this 0.1V lower programming or reading error is consistent across 20V-20A, 20V-10A & 36V-6A ZUp
#   models with a range of UVP & OVP values from 1V to 20V.
# - Could potentially compensate by programming UVP & OVP to 0.1V greater than desired, but since programming
#   may be correct and reading erroneous, will pass.
#
# Phillip Smelt, 11/22/2021.

import serial # https://pythonhosted.org/pyserial/#
import time
_DEBUG = False
_CRLF = '\r\n'
_INDEX_ADDRESS, _INDEX_VOLTAGE, _INDEX_AMPERAGE, _INDEX_FOLDBACK = 0, 1, 2, 3
_ZUp_VOL_TOLERANCE = 10
# - 10 = +/-10% tolerance, used for both UVP/OVP (Under-Voltage Protection/Over-Voltage Protection) and verifying Actual Voltage.
#   Minimum UVP/OVP per 'TDK-Lambda ZUp Power Supplies User Manual, IA549-04-01R' paragraph 4.4.5 is +/-5% tolerance, but appears too tight; 
#   at +/-5%, Actual Voltage intermittently programmed incorrectly, so went with +/-10%, which consistently programs correctly.
# - Could've passed in the UVP/OVP values in ZUps_ON(), but then UVP/OVP would have to be correctly pre-calculated, so they wouldn't 
#   exceed their limits, which seemed too onerous to the programmer invoking ZUps_ON().
# - +/-10% seemsed reasonable for both UVP/OVP and verifying Actual Voltages.
_ZUp_CUR_TOLERANCE = 5
# 5 = +5% tolerance, used for Current maximum and verifying Actual Amperage.
# Recommended CUR per paragraph 5.5.3.4 is 105% of desired CUR limit.


def ZUps_ON(*, ZUps, SerialPort, Baud):
    # A ZUp is a list object containing 4 elements: [Address, Voltage, Amperage, Foldback]:
    # - Address is an integer from 1 to _MAX_ZUps, currently 31, indexed at _INDEX_ADDRESS, or 0.
    # - Voltage is a float specific to the ZUp model, indexed at _INDEX_VOLTAGE, or 1.
    # - Amperage is a float specific to the ZUp model, indexed at _INDEX_AMPERAGE, or 2.
    # - Foldback is a string value where Foldback.upper() is in set {'FLD_ON', 'FLD_OFF'}, indexed at _INDEX_FOLDBACK, or 3.
    #
    #   ZUps is a list of ZUp lists, containing 1 to _MAX_ZUps elements, currently 31.
    #   [[Address1, Voltage1, Amperage1, Foldback1], [Address2, Voltage2, Amperage2, Foldback2], [Address3, Voltage3, Amperage3, Foldback3]...
    #   ...[Address31, Voltage31, Amperage31, Foldback31]].
    Addresses = _ZUps_GetAddresses(ZUps)
    _ZUps_VerifyAddresses(Addresses)
    _ZUps_VerifyFoldbacks(ZUps)
    _ZUps_VerifyBaud(Baud)
    PortSerial = _ZUps_GetPortSerial(SerialPort, Baud)
    _ZUps_VerifySetVAs(ZUps, PortSerial)
    _ZUps_PowerVAs(ZUps, PortSerial)
    _ZUps_VerifyActualVAs(ZUps, PortSerial)
    PortSerial.close()
    return None


def ZUps_off(*, Addresses, SerialPort, Baud):
    _ZUps_VerifyAddresses(Addresses)
    _ZUps_VerifyBaud(Baud)
    PortSerial = _ZUps_GetPortSerial(SerialPort, Baud)
    _ZUps_SetPower(Addresses, PortSerial, 'off')
    _ZUps_VerifyPower(Addresses, PortSerial, 'off')
    _ZUps_CleanUp(Addresses, PortSerial)
    PortSerial.close()
    return None


def ZUp(*, Address, Voltage, Amperage, Foldback):
    # ZUp() is an optional convenience function to permit invocation of ZUps_ON() with ZUps that have named arguments.
    # Example:
    #   ZUps_ON(ZUps=[[1, 3.3, 1.0, 'FLD_off'], [2, 5.0, 1.0, 'FLD_off'], [3, 15.0, 1.0, 'FLD_off'], [4, 15.0, 1.0, 'FLD_off'], [5, 28.0, 1.0, 'FLD_off']], SerialPort='COM1', Baud=9600)
    # Is equivalent to:
    #   ZUps_ON(ZUps=[ZUp(Address=1, Voltage=3.3,  Amperage=1.0,  Foldback='FLD_off'),
    #                 ZUp(Address=2, Voltage=5.0,  Amperage=1.0,  Foldback='FLD_off'),  
    #                 ZUp(Address=3, Voltage=15.0, Amperage=1.0,  Foldback='FLD_off'),  
    #                 ZUp(Address=4, Voltage=15.0, Amperage=1.0,  Foldback='FLD_off'),  
    #                 ZUp(Address=5, Voltage=28.0, Amperage=1.0,  Foldback='FLD_off')], SerialPort='COM1', Baud=9600)
    return [Address, Voltage, Amperage, Foldback]


def _ZUps_GetAddresses(ZUps):
    Addresses = []
    for ZUp in ZUps:
        Addresses.append(ZUp[_INDEX_ADDRESS])
    return Addresses


def _ZUps_VerifyAddresses(Addresses):
    Failures = ''
    _MAX_ZUps = 31
    if len(Addresses) not in range(1, _MAX_ZUps + 1, 1):
        Failures += 'Number of Addresses must be in range [1..' + str(_MAX_ZUps) + '].' + _CRLF + _CRLF
    for Address in Addresses:
        if Address not in range(1, _MAX_ZUps + 1, 1):
            Failures += 'Address must be an integer in range [1..' + str(_MAX_ZUps) + '].' + _CRLF + _CRLF
    if Failures != '':
        raise ValueError(Failures)
    else:
        return None


def _ZUps_VerifyFoldbacks(ZUps):
    Failures = ''
    for ZUp in ZUps:
        if str(ZUp[_INDEX_FOLDBACK]).upper() not in ['FLD_ON', 'FLD_OFF']:
            Failures += 'ZUp Foldback "' + str(ZUp[_INDEX_FOLDBACK]).upper() + '" unknown.' + _CRLF
            Failures += 'ZUp Foldback.upper() must be in set {"FLD_ON", "FLD_OFF"}.' + _CRLF 
            Failures += '   Address ' + str(ZUp[_INDEX_ADDRESS]) + '.' + _CRLF + _CRLF
    if Failures != '':
        raise ValueError(Failures)
    else:
        return None    


def _ZUps_VerifyBaud(Baud):
    if Baud not in [300, 600, 1200, 2400, 4800, 9600]:     
        raise ValueError('Baud rate must be an integer in set {300, 600, 1200, 2400, 4800, 9600}.' + _CRLF + _CRLF)
    else:
        return None


def _ZUps_GetPortSerial(SerialPort, Baud):
    return serial.Serial(port=SerialPort, baudrate=Baud, bytesize=serial.EIGHTBITS,
                         parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE,
                         timeout=30, xonxoff=True, rtscts=False,
                         write_timeout=30, dsrdtr=False, inter_byte_timeout=None)


def _ZUp_GetModel(ZUp, PortSerial):
    # ABT current ZUp models return below strings:
    #   'Nemic-Lambda ZUp(10V-20A)\r\n'
    #   'Nemic-Lambda ZUp(20V-10A)\r\n'
    #   'Nemic-Lambda ZUp(20V-20A)\r\n'
    #   'Nemic-Lambda ZUp(36V-6A)\r\n'
    # 'TDK-Lambda ZUp Power Supplies User Manual, IA549-04-01R' paragraph 5.6.1 specifies minimum 10mSec delay
    # prior to ADR command, and 30mSec delay after.
    _ZUp_WriteCommand(':MDL?;', PortSerial)
    MDL = _ZUp_ReadResponse(PortSerial)
    return MDL[MDL.index('(') + 1:MDL.index(')')]
    # Return '36V-6A' for 'Nemic-Lambda ZUp(36V-6A)\r\n'.


def _ZUp_FormatAddress(Address):
    strAddress = str(Address)
    strAddress = '0' + strAddress if Address < 10 else strAddress
    # Addresses must be character strings of length 2, so prepend '0' if needed; '01', '02', '03'...'09'.
    return strAddress


def _ZUps_VerifySetVAs(ZUps, PortSerial):
    Failures = ''
    for ZUp in ZUps:
        _ZUp_WriteCommand(':ADR' + _ZUp_FormatAddress(ZUp[_INDEX_ADDRESS]) + ';', PortSerial)
        MDL = _ZUp_GetModel(ZUp, PortSerial)
        V, A = float(MDL[0:MDL.index('V')]), float(MDL[MDL.index('-') + 1:MDL.index('A')])
        # V, A = 36.0, 6.0 when MDL is '36V-6A'.
        if not (0 <= ZUp[_INDEX_VOLTAGE] <= V):
            # 'TDK-Lambda ZUp Power Supplies User Manual, IA549-04-01R', paragraph 5.5.3.1 recommends up to 100% of rated voltage.
            Failures += 'ZUp model ' + MDL + ' Programmed Voltage outside range:' + _CRLF
            Failures += '   Programmed Voltage: ' + str(ZUp[_INDEX_VOLTAGE]) + '.' + _CRLF
            Failures += '   Address ' + str(ZUp[_INDEX_ADDRESS]) + '.' + _CRLF + _CRLF
        if not (0 <= ZUp[_INDEX_AMPERAGE] <= A * (1 + _ZUp_CUR_TOLERANCE)):
            # 'TDK-Lambda ZUp Power Supplies User Manual, IA549-04-01R', paragraph 5.5.3.4 recommends up to 105% of rated current.
            Failures += 'ZUp model ' + MDL + ' Programmed Amperage outside range:' + _CRLF
            Failures += '   Programmed Amperage: ' + str(ZUp[_INDEX_AMPERAGE]) + '.' + _CRLF
            Failures += '   Address ' + str(ZUp[_INDEX_ADDRESS]) + '.' + _CRLF + _CRLF
    if Failures != '':
        PortSerial.close()
        raise ValueError(Failures)
    else:
        return None


def _ZUps_SetPower(Addresses, PortSerial, DesiredState):
    for Address in Addresses:
        _ZUp_WriteCommand(':ADR' + _ZUp_FormatAddress(Address) + ';', PortSerial)
        if DesiredState.lower() == 'off':
            _ZUp_WriteCommand(':OUT0;', PortSerial)
        else: # DesiredState.upper() == 'ON'
            _ZUp_WriteCommand(':OUT1;', PortSerial)
    return None


def _ZUps_VerifyPower(Addresses, PortSerial, ExpectedState):
    Failures = ''
    for Address in Addresses:
        _ZUp_WriteCommand(':ADR' + _ZUp_FormatAddress(Address) + ';', PortSerial)
        _ZUp_WriteCommand(':STA?;', PortSerial)
        OSR = _ZUp_ReadResponse(PortSerial)
        # Above read of Operation Status Register returns a string in format:
        #   'OS00010000\r\n'
        #    01234567901234
        # The 5th bit is off/on status, 0 for off, 1 for on; above shows on.
        if   (OSR[5:6] == '0') and (ExpectedState.upper() == 'ON'):
            Failures += 'Power Supply Address ' + str(Address) + ' failed to turn ON!' + _CRLF
            Failures += _ZUp_ReadStatus(Address, PortSerial) + _CRLF + _CRLF        
        elif (OSR[5:6] == '1') and (ExpectedState.lower() == 'off'):
            Failures += 'Power Supply Address ' + str(Address) + ' failed to turn off!' + _CRLF
            Failures += _ZUp_ReadStatus(Address, PortSerial) + _CRLF + _CRLF  
    if Failures != '':
        PortSerial.close()
        raise RuntimeError(Failures)
    else:
        return None


def _ZUps_CleanUp(Addresses, PortSerial):
    for Address in Addresses:
        _ZUp_WriteCommand(':ADR' + _ZUp_FormatAddress(Address) + ';', PortSerial)
        _ZUp_WriteCommand(':RMT1;', PortSerial)   # RMT1 allows operator to manually toggle Remote mode.     
        _ZUp_WriteCommand(':DCL;', PortSerial)    # DCL clears communication buffer & Operation/Alarm/Programming registers.
        _ZUp_WriteCommand(':FLD2;', PortSerial)   # Disable Foldback Protection.
        _ZUp_WriteCommand(':AST0;', PortSerial)   # AutoSet 0 prevents the ZUp from re-powering to last programmed V & A after being turned off/on.
    return None


def _ZUps_VerifyActualVAs(ZUps, PortSerial):
    time.sleep(1)
    # There's an apparent lag between a ZUp being activated and it's ':VOL?;' command returning the correct programmed voltage.
    # Without above sleep delay, Actual Voltage was occasionally measuring < Set Voltage, by more than _ZUp_VOL_TOLERANCE of 10%.    
    Failures = ''
    for ZUp in ZUps:
        _ZUp_WriteCommand(':ADR' + _ZUp_FormatAddress(ZUp[_INDEX_ADDRESS]) + ';', PortSerial)
        _ZUp_WriteCommand(':VOL?;', PortSerial)
        AV = _ZUp_ReadResponse(PortSerial)
        V = float(AV[2:len(AV)-2])
        # V = 0.992 when AV = 'AV00.992\r\n'.
        _ZUp_WriteCommand(':CUR?;', PortSerial)
        AA = _ZUp_ReadResponse(PortSerial)
        A = float(AA[2:len(AA)-2])
        # A = 1.50 when AA = 'AA01.50\r\n'.
        if not (ZUp[_INDEX_VOLTAGE] * (1 - _ZUp_VOL_TOLERANCE / 100) <= V <= ZUp[_INDEX_VOLTAGE] * (1 + _ZUp_VOL_TOLERANCE / 100)):
            Failures += 'Power Supply Address ' + str(ZUp[_INDEX_ADDRESS]) + ' outside +/-' + str(_ZUp_VOL_TOLERANCE) + '% default tolerance!' + _CRLF
            Failures += 'Measures ' + str(V) + 'V.' + _CRLF
            Failures += _ZUp_ReadStatus(ZUp[_INDEX_ADDRESS], PortSerial) + _CRLF + _CRLF            
        if not (0 <= A <= ZUp[_INDEX_AMPERAGE] * (1 + _ZUp_CUR_TOLERANCE)):
            Failures += 'Power Supply Address ' + str(ZUp[_INDEX_ADDRESS]) + ' exceeds Amperage!' + _CRLF
            Failures += 'Measures ' + str(A) + 'A.' + _CRLF
            Failures += _ZUp_ReadStatus(ZUp[_INDEX_ADDRESS], PortSerial) + _CRLF + _CRLF
        if _DEBUG:
            print('Address: ' + str(ZUp[_INDEX_ADDRESS]))
            print(_ZUp_ReadStatus(ZUp[_INDEX_ADDRESS], PortSerial) + _CRLF + _CRLF)
    if Failures != '':
        PortSerial.close()
        raise RuntimeError(Failures)
    else:
        return None


def _ZUps_PowerVAs(ZUps, PortSerial):
    for ZUp in ZUps:
        _ZUp_WriteCommand(':ADR' + _ZUp_FormatAddress(ZUp[_INDEX_ADDRESS]) + ';', PortSerial)
        _ZUp_WriteCommand(':RMT2;', PortSerial)      # RMT1 allows operator to manually toggle Remote mode.     
        _ZUp_WriteCommand(':DCL;', PortSerial)       # DCL clears communication buffer & Operation/Alarm/Programming registers.
        _ZUp_WriteCommand(':AST0;', PortSerial)      # AutoSet 0 prevents the ZUp from powering to last programmed V & A after being turned off/on.
        if  str(ZUp[_INDEX_FOLDBACK]).upper() == 'FLD_ON':
            _ZUp_WriteCommand(':FLD1;', PortSerial)  # Enable Foldback Protection.       
        else:                                        # str(ZUp[_INDEX_FOLDBACK]).upper() == 'FLD_OFF'
            _ZUp_WriteCommand(':FLD2;', PortSerial)  # Disable Foldback Protection.
        _ZUp_WriteCommand(':SRV0;', PortSerial)      # Disable Over-Voltage Protection service requests.
        _ZUp_WriteCommand(':SRT0;', PortSerial)      # Disable Over-Temperature Protection service requests.
        _ZUp_WriteCommand(':SRF0;', PortSerial)      # Disable Foldback Protection service requests.

        MDL = _ZUp_GetModel(ZUp, PortSerial)
        # VOL string formatting per 'TDK-Lambda ZUp Power Supplies User Manual, IA549-04-01R' paragraph 5.5.3.1.
        V, VOL = ZUp[_INDEX_VOLTAGE], ''
        if   (MDL == '6V-33A') or (MDL == '6V-66A') or (MDL == '6V-132A'):
            VOL = _Format(V, 1, 3)    
        elif (MDL == '10V-20A') or (MDL == '10V-40A') or (MDL == '10V-80A') or (MDL == '20V-10A') or (MDL == '20V-20A') or (MDL == '20V-40A'):
            VOL = _Format(V, 2, 3)    
        elif (MDL == '36V-6A') or (MDL == '36V-12A') or (MDL == '36V-24A') or (MDL == '60V-3.5A') or (MDL == '60V-7A') or (MDL == '60V-14A') or (MDL == '80V-2.5A') or (MDL == '80V-5A'):
            VOL = _Format(V, 2, 2)    
        else: # (MDL == '120V-1.8A') or (MDL == '120V-3.6A')
            VOL = _Format(V, 3, 2)    

        # CUR string formatting per 'TDK-Lambda ZUp Power Supplies User Manual, IA549-04-01R' paragraph 5.5.3.4.
        A, CUR = ZUp[_INDEX_AMPERAGE], ''
        if   (MDL == '6V-33A') or (MDL == '6V-66A') or (MDL == '10V-40A') or (MDL == '10V-80A') or (MDL == '20V-40A'):
            CUR = _Format(A, 2, 2)
        elif (MDL == '6V-132A'):
            CUR = _Format(A, 3, 2)    
        elif (MDL == '10V-20A') or (MDL == '20V-10A') or (MDL == '20V-20A') or (MDL == '36V-12A') or (MDL == '36V-24A') or (MDL == '60V-14A'):
            CUR = _Format(A, 2, 3)    
        elif (MDL == '36V-6A') or (MDL == '60V-3.5A') or (MDL == '60V-7A') or (MDL == '80V-5A') or (MDL == '120V-3.6'):
            CUR = _Format(A, 1, 3)    
        else: # (MDL == '80V-2.5A') or (MDL == '120V-1.8A')
            CUR = _Format(A, 1, 4)     

        # UVP string formatting per 'TDK-Lambda ZUp Power Supplies User Manual, IA549-04-01R' paragraph 5.5.3.13.
        # Assuming _ZUp_VOL_TOLERANCE = 10 as programmed, then uv will always be <= UVP maximums, for all ZUps.
        uv = ZUp[_INDEX_VOLTAGE] * (1 - _ZUp_VOL_TOLERANCE / 100)
        UVP, UVPmin = '', ''
        if   (MDL == '6V-33A') or (MDL == '6V-66A') or (MDL == '6V-132A') or (MDL == '10V-20A') or (MDL == '10V-40A') or (MDL == '10V-80A'):
            UVP, UVPmin = _Format(uv, 1, 2), _Format(0, 1, 2)  
        elif (MDL == '120V-1.8A') or (MDL == '120V-3.6A'):
            UVP, UVPmin = _Format(uv, 3, 1), _Format(0, 3, 1)       
        else: # (MDL == '20V-10A') or (MDL == '20V-20A') or (MDL == '20V-40A') or 
              # (MDL == '36V-6A') or (MDL == '36V-12A') or (MDL == '36V-24A') or 
              # (MDL == '60V-3.5A') or (MDL == '60V-7A') or (MDL == '60V-14A') or 
              # (MDL == '80V-2.5A') or (MDL == '80V-5A'):
            UVP, UVPmin = _Format(uv, 2, 1), _Format(0, 2, 1)  

       # Following code implements OVP string formatting per 'TDK-Lambda ZUp Power Supplies User Manual, IA549-04-01R' paragraph 5.5.3.11.
       # Assuming _ZUp_VOL_TOLERANCE = 10 as programmed, then ov will always be <= OVP maximums, for all ZUps.
       # However, must accommodate minimal ov, OVP when V is ≈ 0V.
        ov = ZUp[_INDEX_VOLTAGE] * (1 + _ZUp_VOL_TOLERANCE / 100)
        OVP, OVPmax = '', ''
        if   (MDL == '6V-33A') or (MDL == '6V-66A') or (MDL == '6V-132A'):
            ov = 0.2 if ov < 0.2 else ov
            OVP, OVPmax = _Format(ov, 1, 2), _Format(7.50, 1, 2)                 
        elif (MDL == '10V-20A') or (MDL == '10V-40A') or (MDL == '10V-80A'):
            ov = 0.5 if ov < 0.5 else ov
            OVP, OVPmax = _Format(ov, 2, 1), _Format(13.0, 2, 1) 
        elif (MDL == '20V-10A') or (MDL == '20V-20A') or (MDL == '20V-40A'):
            ov = 1.0 if ov < 1.0 else ov
            OVP, OVPmax = _Format(ov, 2, 1), _Format(24.0, 2, 1) 
        elif (MDL == '36V-6A') or (MDL == '36V-12A') or (MDL == '36V-24A'):
            ov = 1.8 if ov < 1.8 else ov
            OVP, OVPmax = _Format(ov, 2, 1), _Format(40.0, 2, 1) 
        elif (MDL == '60V-3.5A') or (MDL == '60V-7A') or (MDL == '60V-14A'):
            ov = 3.0 if ov < 3.0 else ov
            OVP, OVPmax = _Format(ov, 2, 1), _Format(66.0, 2, 1) 
        elif (MDL == '80V-2.5A') or (MDL == '80V-5A'):
            ov = 4.0 if ov < 4.0 else ov
            OVP, OVPmax = _Format(ov, 2, 1), _Format(88.0, 2, 1) 
        else: # (MDL == '120V-1.8A') or (MDL == '120V-3.6A')
            ov = 6.0 if ov < 6.0 else ov
            OVP, OVPmax = _Format(ov, 3, 1), _Format(132.0, 3, 1) 

        UVP, UVPmin, OVP, OVPmax, VOL, CUR = ':UVP' + UVP, ':UVP' + UVPmin, ':OVP' + OVP, ':OVP' + OVPmax, ':VOL' + VOL, ':CUR' + CUR
        # Pre-pend ':UVP', ':OVP' etc.
        UVP, UVPmin, OVP, OVPmax, VOL, CUR = UVP + ';', UVPmin + ';', OVP + ';', OVPmax + ';', VOL + ';', CUR + ';'
        # Post-pend ';'.

        _ZUp_WriteCommand(UVPmin, PortSerial)
        # Avoid errors; initially set UVP to minimum, so it must be <= desired VOL, will reset to desired UVP after setting desired VOL.
        _ZUp_WriteCommand(OVPmax, PortSerial)
        # Avoid errors; initially set OVP to maximum, so it must be >= desired VOL, will reset to desired OVP after setting desired VOL.
        _ZUp_WriteCommand(':CUR!;', PortSerial)
        SA = _ZUp_ReadResponse(PortSerial)
        if ZUp[_INDEX_AMPERAGE] > float(SA[2:len(SA)-2]):  # Example formats: 'SA3.000\r\n' or 'SA07.50\r\n'.
            _ZUp_WriteCommand(CUR, PortSerial)
            # Desired CUR is > Set CUR, so increase it now to prevent erroring when setting VOL.  If not, will decrease it after setting VOL. 

        _ZUp_WriteCommand(VOL, PortSerial)
        _ZUp_WriteCommand(':OUT1;', PortSerial)
        time.sleep(0.250)
        # - Now turn on ZUp power supply, although it may've already been on.  Allow 250mSec for voltage & current to stabilize; may require more.
        # - By allowing already powered ZUps to have their VOLs & CURs dynamically changed without first de-powering, ZUps_ON() can ramp 
        #   voltages/currents up/down as desired.
  
        _ZUp_WriteCommand(CUR, PortSerial)  # Now set true desired CUR, although may've already been set previously.
        _ZUp_WriteCommand(OVP, PortSerial)  # Now set true desired OVP.
        _ZUp_WriteCommand(UVP, PortSerial)  # Now set true desired UVP.

        if _DEBUG:
            print(UVP, UVPmin, OVP, OVPmax, VOL, CUR, ZUp[_INDEX_ADDRESS])
    return None


def _Format(valReal, digitsLeading, digitsTrailing):
    frmt = '{:' + str(digitsLeading) + '.' + str(digitsTrailing) + 'f}'
    valFormat = frmt.format(round(valReal, digitsTrailing))
    while len(valFormat) < digitsLeading + digitsTrailing + 1:
        valFormat = '0' + valFormat
    return valFormat


def _ZUp_WriteCommand(Command, PortSerial):
    if Command[0:4] == ':ADR':
        time.sleep(0.015)
        PortSerial.write(Command.encode('utf-8'))
        time.sleep(0.035)
    else: # All other ZUp commands.
        PortSerial.write(Command.encode('utf-8'))
        time.sleep(0.020)    
    # Python's pySerial library requires UTF-8 byte encoding/decoding, not string.
    # If _ZUp_WriteCommand() ever changes encoding/decoding, change both here & in _ZUp_ReadResponse().
    # Per 'TDK-Lambda ZUp Power Supplies User Manual, IA549-04-01R', paragraph 5.6.1:
    #   - 10mSec minimum delay is required before sending ADR command.
    #   - 30mSec delay required after sending ADR command.
    #   - 15mSec *average* command processing time for the ZUp Series.
    # Add 5 mSec safety margin to each delay, may need to adjust.
    return None


def _ZUp_ReadResponse(PortSerial):
    return PortSerial.readline().decode('utf-8')
    # Yes, inefficient to have a one line function, but allows a single place to update the ZUp read implementation.
    # At some point, the encoding/decoding may change, or may want to add error handling.
    # Or may switch from pySerial to another Python serial library.
    # If _ZUp_ReadResponse()'s encoding/decoding does change, must also update in _ZUp_WriteCommand().


def _ZUp_ReadStatus(Address, PortSerial):
    _ZUp_WriteCommand(':ADR' + _ZUp_FormatAddress(Address) + ';', PortSerial)
    _ZUp_WriteCommand(':VOL?;', PortSerial)
    AV = _ZUp_ReadResponse(PortSerial)
    _ZUp_WriteCommand(':CUR?;', PortSerial)
    AA = _ZUp_ReadResponse(PortSerial)
    _ZUp_WriteCommand(':STA?;', PortSerial)
    OS = _ZUp_ReadResponse(PortSerial)
    _ZUp_WriteCommand(':ALM?;', PortSerial)
    AL = _ZUp_ReadResponse(PortSerial)
    _ZUp_WriteCommand(':STP?;', PortSerial)
    PS = _ZUp_ReadResponse(PortSerial)    
    _ZUp_WriteCommand(':RMT?;', PortSerial)
    RM = _ZUp_ReadResponse(PortSerial)
    _ZUp_WriteCommand(':MDL?;', PortSerial)
    MD = _ZUp_ReadResponse(PortSerial)
    _ZUp_WriteCommand(':REV?;', PortSerial)
    RV = _ZUp_ReadResponse(PortSerial)
    _ZUp_WriteCommand(':VOL!;', PortSerial)
    VS = _ZUp_ReadResponse(PortSerial)
    _ZUp_WriteCommand(':CUR!;', PortSerial)
    CS = _ZUp_ReadResponse(PortSerial)    
    _ZUp_WriteCommand(':FLD?;', PortSerial)
    FL = _ZUp_ReadResponse(PortSerial)
    _ZUp_WriteCommand(':OVP?;', PortSerial)
    OV = _ZUp_ReadResponse(PortSerial)    
    _ZUp_WriteCommand(':UVP?;', PortSerial)
    UV = _ZUp_ReadResponse(PortSerial)
    _ZUp_WriteCommand(':AST?;', PortSerial)
    AS = _ZUp_ReadResponse(PortSerial)
    # Per 'TDK-Lambda ZUp Power Supplies User Manual, IA549-04-01R', paragraph 5.6.3,   
    # ZUp appends '\r\n' to it's responses, so below string has a carriage return/linefeed
    # between each '+' concatenation, which prints out nicely onscreen.
    return AV + AA + OS + AL + PS + RM + MD + RV + VS + CS + FL + OV + UV + AS
