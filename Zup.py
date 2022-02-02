"""
    "TDK™", "TDK-Lambda™" & "Zup™" are registered trademarks of the TDK Corporation.
    "Python™" is a registered trademark of the Python Software Foundation.
    pySerial Copyrighted by Chris Liechti.
    pytest Copyrighted by Holger Krekel and pytest-dev team.
    This script Copyright Amphenol Borisch Technologies, 2022
    - https://www.borisch.com/

    Zup class.
"""
import time
import serial # https://pypi.org/project/pyserial/ & https://pyserial.readthedocs.io/en/latest/pyserial.html

class Zup(object):
    """ Class to programmatically control TDK-Lambda Zup Power Supplies via their serial ports.
        - Reference  Zup Manual 'TDK-Lambda Zup Power Supplies User Manual, IA549-04-01R', especially Chapter 5, 'RS232 & RS485 Remote Control':
           - https://product.tdk.com/system/files/dam/doc/product/power/switching-power/prg-power/instruction_manual/zup-user-manual.pdf
        - Requires pySerial library:
          - https://pypi.org/project/pyserial/
          - https://pyserial.readthedocs.io/en/latest/pyserial.html
    """
    listening_addresses = {}
    ADDRESS_RANGE = range(1, 32, 1)
    BAUD_RATES = (300, 600, 1200, 2400, 4800, 9600)
    FORMATS = {'1.2'  : '{:0>4.2f}',
               '1.3'  : '{:0>5.3f}',
               '1.4'  : '{:0>6.4f}',
               '2.1'  : '{:0>4.1f}',
               '2.2'  : '{:0>5.2f}',
               '2.3'  : '{:0>6.3f}',
               '3.1'  : '{:0>5.1f}',
               '3.2'  : '{:0>6.2f}'}

    # Zup Manual Table 5.5.3.  VOL['MAX'] allowed to be up to 105% of rated voltage.
    VOLs = {'ZUP6-XY'   : {'min': 0.0, 'MAX':   6.300,  'Format': FORMATS['1.3']},
            'ZUP10-XY'  : {'min': 0.0, 'MAX':  10.500,  'Format': FORMATS['2.3']},
            'ZUP20-XY'  : {'min': 0.0, 'MAX':  21.000,  'Format': FORMATS['2.3']},
            'ZUP36-XY'  : {'min': 0.0, 'MAX':  37.80,   'Format': FORMATS['2.2']},
            'ZUP60-XY'  : {'min': 0.0, 'MAX':  63.00,   'Format': FORMATS['2.2']},
            'ZUP80-XY'  : {'min': 0.0, 'MAX':  84.00,   'Format': FORMATS['2.2']},
            'ZUP120-XY' : {'min': 0.0, 'MAX': 126.00,   'Format': FORMATS['3.2']}}

    # Zup Manual Table 5.5.4.  CUR['MAX'] allowed to be up to 105% of rated current.
    CURs = {'ZUP6-33'   : {'min': 0.0, 'MAX':  34.65,   'Format': FORMATS['2.2']},
            'ZUP6-66'   : {'min': 0.0, 'MAX':  69.30,   'Format': FORMATS['2.2']},
            'ZUP6-132'  : {'min': 0.0, 'MAX': 138.60,   'Format': FORMATS['3.2']},
            'ZUP10-20'  : {'min': 0.0, 'MAX':  21.000,  'Format': FORMATS['2.3']},
            'ZUP10-40'  : {'min': 0.0, 'MAX':  42.00,   'Format': FORMATS['2.2']},
            'ZUP10-80'  : {'min': 0.0, 'MAX':  84.00,   'Format': FORMATS['2.2']},
            'ZUP20-10'  : {'min': 0.0, 'MAX':  10.500,  'Format': FORMATS['2.3']},
            'ZUP20-20'  : {'min': 0.0, 'MAX':  21.000,  'Format': FORMATS['2.3']},
            'ZUP20-40'  : {'min': 0.0, 'MAX':  42.00,   'Format': FORMATS['2.2']},
            'ZUP36-6'   : {'min': 0.0, 'MAX':   6.300,  'Format': FORMATS['1.3']},
            'ZUP36-12'  : {'min': 0.0, 'MAX':  12.600,  'Format': FORMATS['2.3']},
            'ZUP36-24'  : {'min': 0.0, 'MAX':  25.200,  'Format': FORMATS['2.3']},
            'ZUP60-3.5' : {'min': 0.0, 'MAX':   3.675,  'Format': FORMATS['1.3']},
            'ZUP60-7'   : {'min': 0.0, 'MAX':   7.350,  'Format': FORMATS['1.3']},
            'ZUP60-14'  : {'min': 0.0, 'MAX':  14.700,  'Format': FORMATS['2.3']},
            'ZUP80-2.5' : {'min': 0.0, 'MAX':   2.6250, 'Format': FORMATS['1.4']},
            'ZUP80-5'   : {'min': 0.0, 'MAX':   5.250,  'Format': FORMATS['1.3']},
            'ZUP120-1.8': {'min': 0.0, 'MAX':   1.8900, 'Format': FORMATS['1.4']},
            'ZUP120-3.6': {'min': 0.0, 'MAX':   3.780,  'Format': FORMATS['1.3']}}

    # Zup Manual Table 5.5.11.
    OVPs = {'ZUP6-XY'   : {'min': 0.2, 'MAX':   7.50,   'Format': FORMATS['1.2']},
            'ZUP10-XY'  : {'min': 0.5, 'MAX':  13.0,    'Format': FORMATS['2.1']},
            'ZUP20-XY'  : {'min': 1.0, 'MAX':  24.0,    'Format': FORMATS['2.1']},
            'ZUP36-XY'  : {'min': 0.8, 'MAX':  40.0,    'Format': FORMATS['2.1']},
            'ZUP60-XY'  : {'min': 3.0, 'MAX':  66.0,    'Format': FORMATS['2.1']},
            'ZUP80-XY'  : {'min': 4.0, 'MAX':  88.0,    'Format': FORMATS['2.1']},
            'ZUP120-XY' : {'min': 6.0, 'MAX': 132.0,    'Format': FORMATS['3.1']}}

    # Zup Manual Table 5.5.13.  UVP['MAX'] ≈  95% * VOL['MAX'].
    UVPs = {'ZUP6-XY'   : {'min': 0.0, 'MAX':   5.98,   'Format': FORMATS['1.2']},
            'ZUP10-XY'  : {'min': 0.0, 'MAX':   9.97,   'Format': FORMATS['1.2']},
            'ZUP20-XY'  : {'min': 0.0, 'MAX':  19.9,    'Format': FORMATS['2.1']},
            'ZUP36-XY'  : {'min': 0.0, 'MAX':  35.9,    'Format': FORMATS['2.1']},
            'ZUP60-XY'  : {'min': 0.0, 'MAX':  59.8,    'Format': FORMATS['2.1']},
            'ZUP80-XY'  : {'min': 0.0, 'MAX':  79.8,    'Format': FORMATS['2.1']},
            'ZUP120-XY' : {'min': 0.0, 'MAX': 119.8,    'Format': FORMATS['3.1']}}

    def __init__(self, address: int, serial_port: serial) -> None:
        """ Initializer for Zup class
            Inputs:        address: int, address of TDK-Lambda ZUP Power Supply
                           serial_port: pySerial serial object, RS-232 or RS-485 serial port connecting PC to ZUP Power Supplies
            Outputs:       None
            ZUP commands:  :RMT2;
            Nuances:       - ':RMT2;' disables Zup front-panel operator controls:
                             - Prevents all operator interference/intervention, apart from powering Zup off.
                             - Permits only programmatic control of the Zup supply.
                           - Initializer __init__() deliberately doesn't issue any other Zup commands:
                             - Instantiating a Zup object literally only establishes communication with it.
                             - Whatever prior state a Zup has before __init__() executes remains entirely intact after execution.
                             - Use Zup class methods to change Zup states.
                             - Use Zup.configure() to configure Zup with power off, voltage/amperage zeroed and options disabled.
        """
        if type(address) != int:
            raise TypeError('Invalid address, must be an integer.')
        if address not in Zup.ADDRESS_RANGE:
            raise ValueError('Invalid address, must be in range ' + str(Zup.ADDRESS_RANGE) + '.')
        if serial_port.baudrate not in Zup.BAUD_RATES:
            raise ValueError('Invalid baud rate, must be in list ' + str(Zup.BAUD_RATES) + '.')
        self.serial_port = serial_port
        self.address = address                           # Integer in range [1..31]
        self.set_remote_mode('Remote Latched')           # Disable Zup front panel controls; permit only programmatic control henceforth.
        mdl = self.get_model()                           # Assuming mdl ='Nemic-Lambda ZUP(36V-6A)':
        mdl = mdl[mdl.index('(') + 1 : mdl.index(')')]   # mdl = 36V-6A
        v = mdl[ : mdl.index('V')]                       # v = '36'
        a = mdl[mdl.index('-') + 1 : mdl.index('A')]     # a = '6'
        mdl = 'ZUP{}-{}'.format(v, a)                    # mdl = 'ZUP36-6'
        self.CUR = Zup.CURs[mdl]                         # self.CUR = {'min': 0.0, 'MAX':  6.300,  'Format': FORMATS['1.3']}
        mdl = 'ZUP{}-XY'.format(v)                       # mdl = 'ZUP36-XY'
        self.VOL = Zup.VOLs[mdl]                         # self.VOL = {'min': 0.0, 'MAX': 37.80,   'Format': FORMATS['2.2']}
        self.OVP = Zup.OVPs[mdl]                         # self.OVP = {'min': 0.8, 'MAX': 40.0,    'Format': FORMATS['2.1']}
        self.UVP = Zup.UVPs[mdl]                         # self.UVP = {'min': 0.0, 'MAX': 35.9,    'Format': FORMATS['2.1']}
        return None

    def __del__(self) -> None:
        """ Finalizer for Zup class
            Inputs:        None
            Outputs:       None
            ZUP commands:  :RMT1;
            Nuances:       - ':RMT1;' enables both Zup front-panel operator controls & programmatic control.
                             - Permits all operator interference/intervention.
                             - Permits also programmatic control of the Zup supply, so programmatic control can be resumed if desired.
                             - Appears Python __del__() finalizers aren't guaranteed to execute, so despite good intentions, best
                               to explicitly call Zup.set_remote_mode('Remote Unlatched').
        """
        if not self.serial_port.is_open:
            self.serial_port.open()                  # Reopen in case client app already closed serial_port.
        self.set_remote_mode('Remote Unlatched')     # Enable Zup front panel controls; permit both programmatic & front-panel control henceforth.
        return None

    def __str__(self) -> str:
        """ Printable string representation for Zup class
            Inputs:        None
            Outputs:       str, ZUP Model
            ZUP command:  :MDL?;
        """
        return self.get_model()

    def configure(self) -> None:
        """ Executes following Zup class methods sequentially:
            clear_registers()
            set_power('Off')
            set_autostart('Off')
            set_foldback('Cancel')
            set_service_request_over_voltage('Off')
            set_service_request_over_temperature('Off')
            set_service_request_foldback('Off')
            set_under_voltage_protection(self.UVP['min'])
            set_over_voltage_protection(self.OVP['MAX'])
            set_voltage(0)
            set_amperage(0)
            set_remote_mode('Remote Latched')
        """
        self.clear_registers()
        self.set_power('Off')
        self.set_autostart('Off')
        self.set_foldback('Cancel')
        self.set_service_request_over_voltage('Off')
        self.set_service_request_over_temperature('Off')
        self.set_service_request_foldback('Off')
        self.set_under_voltage_protection(self.UVP['min'])
        self.set_over_voltage_protection(self.OVP['MAX'])
        # Minumum under-voltage & maximum over-voltage effectively disable under/over-voltage protections, AKA UVP & OVP.
        self.set_voltage(0)
        self.set_amperage(0)
        self.set_remote_mode('Remote latched')
        return None

    def set_amperage(self, amperes: float) -> None:
        """ Programs ZUP amperage
            Inputs:       amperes: float, desired amperage
            Outputs:      None
            ZUP command:  :CUR{amperes};
        """
        if type(amperes) not in (int, float):
            raise TypeError('Invalid amperage, must be a real number.')
        if not (self.CUR['min'] <= amperes <= self.CUR['MAX']):
            raise ValueError('Invalid amperage, must always be in range [{}..{}].'.format(self.CUR['min'], self.CUR['MAX']))
        amperes = self.CUR['Format'].format(amperes)
        self._write_command(':CUR{};'.format(amperes))
        return None

    def get_amperage_actual(self) -> float:
        """ Reads ZUP amperage, actual
            Inputs:       None
            Outputs:      float, actual amperage
            ZUP command:  :CUR?;
        """
        self._write_command(':CUR?;')
        aa = self._read_response()    # aa = 'AA1.234'.
        aa = aa.replace('AA', '')     # aa = '1.234'
        return float(aa)        # return 1.234

    def get_amperage_set(self) -> float:
        """ Reads ZUP amperage, programmed
            Inputs:       None
            Outputs:      float, programmed amperage
            ZUP command:  :CUR!;
        """
        self._write_command(':CUR!;')
        sa = self._read_response()    # sa = 'SA1.234'.
        sa = sa.replace('SA', '')     # sa = '1.234'
        return float(sa)        # return 1.234

    def set_voltage(self, volts: float) -> None:
        """ Programs ZUP voltage
            Inputs:       volts: float, desired voltage
            Outputs:      None
            ZUP command:  :VOL{volts};
            Nuances:      - Setting Voltage is best performed by first setting UVP = UVP['min'], OVP = OVP['MAX'],
                            then setting desired Voltage, so UVP/OVP don't interfere with Voltage.
                          - Note that below inequality *always* applies between UVP, Voltage & OVP:
                            - UVP ⪅ Voltage*95% ⪅ Voltage ⪅ Voltage*105% ⪅ OVP.
                            - The ⪅ symbol denotes less than or approximately equal.
                            - The ±5% difference is approximate, possibly due to roundoff in the Zup.
        """
        if type(volts) not in (int, float):
            raise TypeError('Invalid voltage, must be a real number.')
        if not (self.VOL['min'] <= volts <= self.VOL['MAX']):
            raise ValueError('Invalid voltage, must *always* be in range [{}..{}].'.format(self.VOL['min'], self.VOL['MAX']))
        if not (self.get_under_voltage_protection() / 0.95 <= volts <= self.get_over_voltage_protection() / 1.05):
            raise ValueError('Invalid voltage, must *presently* be in range [{}..{}].'.format(self.get_under_voltage_protection() / 0.95, self.get_over_voltage_protection() / 1.05))
        volts = self.VOL['Format'].format(volts)
        self._write_command(':VOL{};'.format(volts))
        return None

    def get_voltage_actual(self) -> float:
        """ Reads ZUP voltage, actual
            Inputs:       None
            Outputs:      float, actual voltage
            ZUP command:  :VOL?;
        """
        self._write_command(':VOL?;')
        av = self._read_response()   # av = 'AV05.12'.
        av = av.replace('AV', '')    # av = '05.12'
        return float(av)          # return 5.12

    def get_voltage_set(self) -> float:
        """ Reads ZUP voltage, actual
            Inputs:       None
            Outputs:      float, programmed voltage
            ZUP command:  :VOL!;
        """
        self._write_command(':VOL!;')
        sv = self._read_response()   # sv = 'SV05.00'.
        sv = sv.replace('SV', '')    # sv = '05.00'
        return float(sv)          # return 5.00

    def set_under_voltage_protection(self, volts: float)  -> None:
        """ Programs ZUP under-voltage limit
            Inputs:       volts: float, desired minimum voltage
            Outputs:      None
            ZUP command:  :UVP{volts};
            Nuances:      - Setting Voltage is best performed by first setting UVP = UVP['min'], OVP = OVP['MAX'],
                            then setting desired Voltage, so UVP/OVP don't interfere with Voltage.
                          - Note that below inequality *always* applies between UVP, Voltage & OVP:
                            - UVP ⪅ Voltage*95% ⪅ Voltage ⪅ Voltage*105% ⪅ OVP.
                            - The ⪅ symbol denotes less than or approximately equal.
                            - The ±5% difference is approximate, possibly due to roundoff in the Zup.
        """
        if type(volts) not in (int, float):
            raise TypeError('Invalid under-voltage, must be a real number.')
        if not (self.UVP['min'] <= volts <= self.UVP['MAX']):
            raise ValueError('Invalid under-voltage, must *always* be in range [{}..{}].'.format(self.UVP['min'], self.UVP['MAX']))
        if not (self.UVP['min'] <= volts <= self.get_voltage_set() * 0.95):
            raise ValueError('Invalid under-voltage, must *presently* be in range [{}..{}].'.format(self.UVP['min'], self.get_voltage_set() * 0.95))
        volts = self.UVP['Format'].format(volts)
        self._write_command(':UVP{};'.format(volts))
        return None

    def get_under_voltage_protection(self) -> float:
        """ Reads ZUP under-voltage programmed limit
            Inputs:       None
            Outputs:      float, programmed under-voltage
            ZUP command:  :UVP?;
        """
        self._write_command(':UVP?;')
        up = self._read_response()   # up = 'UP04.5'.
        up = up.replace('UP', '')    # up = '04.5'
        return float(up)          # return 4.5

    def set_over_voltage_protection(self, volts: float) -> None:
        """ Programs ZUP over-voltage limit
            Inputs:       volts: float, desired maximum voltage
            Outputs:      None
            ZUP command:  :OVP{volts};
            Nuances:      - Setting Voltage is best performed by first setting UVP = UVP['min'], OVP = OVP['MAX'],
                            then setting desired Voltage, so UVP/OVP don't interfere with Voltage.
                          - Note that below inequality *always* applies between UVP, Voltage & OVP:
                            - UVP ⪅ Voltage*95% ⪅ Voltage ⪅ Voltage*105% ⪅ OVP.
                            - The ⪅ symbol denotes less than or approximately equal.
                            - The ±5% difference is approximate, possibly due to roundoff in the Zup.
        """
        if type(volts) not in (int, float):
            raise TypeError('Invalid over-voltage, must be a real number.')
        if not (self.OVP['min'] <= volts <= self.OVP['MAX']):
            raise ValueError('Invalid over-voltage, must *always* be in range [{}..{}].'.format(self.OVP['min'], self.OVP['MAX']))
        if not (self.get_voltage_set() * 1.05 <= volts <= self.OVP['MAX']):
            raise ValueError('Invalid over-voltage, must *presently* be in range [{}..{}].'.format(self.get_voltage_set() * 1.05, self.OVP['MAX']))

        volts = self.UVP['Format'].format(volts)
        self._write_command(':OVP{};'.format(volts))
        return None

    def get_over_voltage_protection(self) -> float:
        """ Reads ZUP over-voltage programmed limit
            Inputs:       None
            Outputs:      float, programmed over-voltage
            ZUP command:  :OVP?;
        """
        self._write_command(':OVP?;')
        op = self._read_response()   # op = 'OP05.5'.
        op = op.replace('OP', '')    # op = '05.5'
        return float(op)          # return 5.5

    def set_power(self, state: str) -> None:
        """ Programs ZUP Power state
            Inputs:        state: str in ('Off, 'On')
            Outputs:       None
            ZUP commands:  :OUT0; if 'Off'
                           :OUT1; if 'On'
        """
        state = Zup._validate_binary_state(state)
        if state == 'Off':
            self._write_command(':OUT0;')
        else: # state == 'On'
            self._write_command(':OUT1;')
        return None

    def power_on(self) -> bool:
        """ Reads ZUP Power state
            Inputs:       None
            Outputs:      bool, True if Power on, False if Power off
            ZUP command:  :OUT?;
        """
        self._write_command(':OUT?;')
        return self._read_response() == 'OT1'

    def get_status(self) -> str:
        """ Reads ZUP Status
            Inputs:       None
            Outputs:      str, core ZUP Status
            ZUP command:  :STT?;
        """
        self._write_command(':STT?;')
        return self._read_response()

    def get_statuses(self) -> list:
        """ Reads ZUP Statuses
            Inputs:        None
            Outputs:       list[tuple], [(command, response), (command, response)...(command, response)]
            ZUP commands:  :MDL?;, :REV?;
                           :VOL!;, :VOL?;, :UVP?;, :OVP?;
                           :CUR!;, :CUR?;
                           :FLD?;, :RMT?;, :AST?;
                           :STA?;, :STP?;, :ALM?;
                           :SRV?;, :SRT?;, :SRF?;
        """
        return self.issue_commands_read_responses((':MDL?;',':REV?;',
                                                   ':VOL!;',':VOL?;',':UVP?;',':OVP?;',
                                                   ':CUR!;',':CUR?;',
                                                   ':FLD?;',':RMT?;',':AST?;',
                                                   ':STA?;',':STP?;',':ALM?;',
                                                   ':SRV?;',':SRT?;',':SRF?;'))

    def issue_commands_read_responses(self, commands: tuple) -> list:
        """ Writes ZUP commands & reads applicable responses
            Inputs:        commands: tuple
                           Example:  (':DCL;', ':MDL?', ':REV?')
            Outputs:       commands_responses: list[tuple]; [(command, response), (command, response)...(command, response)]
                           Example:  [(':DCL;','Response N/A'), (':MDL?','Nemic-Lambda ZUP(20V-10A)'), (':REV?','Ver 20-10 1.1')]
            ZUP commands:  Any desired in 'TDK-Lambda Zup Power Supplies User Manual, IA549-04-01R'.
        """
        commands_responses = []
        for command in commands:
            self._write_command(command)
            response = 'N/A' if command[4:5] not in ('?', '!') else self._read_response()
            commands_responses.append((command, response))
        return commands_responses

    def set_autostart(self, state: str) -> None:
        """ Programs ZUP Autostart state
            Inputs:        state: str in ('Off, 'On')
            Outputs:       None
            ZUP commands:  :AST0; if 'Off'
                           :AST1; if 'On'
        """
        state = Zup._validate_binary_state(state)
        if state == 'Off':
            self._write_command(':AST0;')
        else: # state == 'On'
            self._write_command(':AST1;')
        return None

    def autostart_on(self) -> bool:
        """ Reads ZUP Autostart state
            Inputs:       None
            Outputs:      bool, True if Autostart on, False if Autostart off
            ZUP command:  :AST?;
        """
        self._write_command(':AST?;')
        return self._read_response() == 'AS1'

    def set_foldback(self, state: str) -> None:
        """ Programs ZUP Foldback state
            Inputs:        state: str in ('Release', 'Arm', 'Cancel')
            Outputs:       None
            ZUP commands:  :FLD0; if 'Release'
                           :FLD1; if 'Arm'
                           :FLD2; if 'Cancel'
        """
        state = state.title()
        if state not in ('Release', 'Arm', 'Cancel'):
            raise ValueError('Invalid Foldback state, must be in (''Release'', ''Arm'', ''Cancel'').')
        if   state == 'Release':
            self._write_command(':FLD0;')
        elif state == 'Arm':
            self._write_command(':FLD1;')
        else: # state = 'Cancel'
            self._write_command(':FLD2;')
        return None

    def foldback_on(self) -> bool:
        """ Reads ZUP Foldback state
            Inputs:       None
            Outputs:      bool, True if Foldback armed, False if Foldback canceled
            ZUP command:  :FLD?;
        """
        self._write_command(':FLD?;')
        return self._read_response() == 'FD1'

    def get_model(self) -> str:
        """ Reads ZUP Model info
            Inputs:       None
            Outputs:      str, ZUP Model
            ZUP command:  :MDL?;
        """
        self._write_command(':MDL?;')
        return self._read_response()

    def get_revision(self) -> str:
        """ Reads ZUP Firmware revision
            Inputs:       None
            Outputs:      str, ZUP Firmware revision
            ZUP command:  :REV?;
        """
        self._write_command(':REV?;')
        return self._read_response()

    def clear_registers(self) -> None:
        """ Clears ZUP communication buffer & Operational, Alarm & Programming registers
            Inputs:       None
            Outputs:      None
            ZUP command:  :DCL;
        """
        self._write_command(':DCL;')
        return None

    def get_register_alarm(self) -> str:
        """ Reads ZUP Alarm status register
            Inputs:       None
            Outputs:      str, Alarm status register content
            ZUP command:  :ALM?;
        """
        self._write_command(':ALM?;')
        return self._read_response()

    def get_register_operation(self) -> str:
        """ Reads ZUP Operational status register
            Inputs:       None
            Outputs:      str, Operational status register content
            ZUP command:  :STA?;
        """
        self._write_command(':STA?;')
        return self._read_response()

    def get_register_program(self) -> str:
        """ Reads ZUP Programming status register
            Inputs:       None
            Outputs:      str, Programming status register content
            ZUP command:  :STP?;
        """
        self._write_command(':STP?;')
        return self._read_response()

    def set_remote_mode(self, state: str) -> None:
        """ Programs ZUP Remote state
            Inputs:        state: str in ('Local', 'Remote Unlatched', 'Remote Latched')
            Outputs:       None
            ZUP commands:  :RMT0; if 'Local'
                           :RMT1; if 'Remote Unlatched'
                           :RMT2; if 'Remote Latched'
        """
        state = state.title()
        if state not in ('Local', 'Remote Unlatched', 'Remote Latched'):
            raise ValueError('Invalid remote state, must be in (''Local'', ''Remote Unlatched'', ''Remote Latched'').')
        if   state == 'Local':
            self._write_command(':RMT0;')
        elif state == 'Remote Unlatched':
            self._write_command(':RMT1;')
        else: # state = 'Remote Latched'
            self._write_command(':RMT2;')
        return None

    def remote_latched(self) -> bool:
        """ Reads ZUP Remote latched state
            Inputs:       None
            Outputs:      bool, True if Remote latched, False if Remote unlatched
            ZUP command:  :RMT?;
        """
        self._write_command(':RMT?;')
        return self._read_response() == 'RM2'

    def set_service_request_over_voltage(self, state: str) -> None:
        """ Programs ZUP Service Request over-voltage state
            Inputs:        state: str in ('Off, 'On')
            Outputs:       None
            ZUP commands:  :SRV0; if 'Off'
                           :SRV1; if 'On'
            - Class Zup doesn't implement Service Requests; instead rely upon explicitly querying the Zups for correct operating status, and/or Zup operators
              noticing if Zups don't function correctly.
            - For this library to correctly implement Service Requests, client applications would need to subscribe to notifications of Service Requests,
              and perform event handling routines to respond to arising Service Requests.
            
            From 'TDK-Lambda Genesys Power Supplies User Manual, 83-507-013':
             - Since Service Request messages may be sent from any supply at any time,
               there is a chance they can collide with other messages from other supplies.
             - Your controller software has to be sophisticated enough to read messages that
               may come at any time, and to recover if messages are corrupted by collisions.
             - If you need Service Request messaging, please contact TDK-Lambda for assistance.
               We can provide several special communication commands and settings that will help with this.
        """
        state = Zup._validate_binary_state(state)
        if state == 'Off':
            self._write_command(':SRV0;')
        else: # state == 'On'
            self._write_command(':SRV1;')
        return None

    def service_request_over_voltage_on(self) -> bool:
        """ Reads ZUP Service Request over-voltage state
            Inputs:       None
            Outputs:      bool, True if Service Request enabled, False if disabled
            ZUP command:  :SRV?;
        """
        self._write_command(':SRV?;')
        return self._read_response() == ':QV1;'

    def set_service_request_over_temperature(self, state: str) -> None:
        """ Programs ZUP Service Request over-temperature state
            Inputs:        state: str in ('Off, 'On')
            Outputs:       None
            ZUP commands:  :SRT0; if 'Off'
                           :SRT1; if 'On'
            - Class Zup doesn't implement Service Requests; instead rely upon explicitly querying the Zups for correct operating status, and/or Zup operators
              noticing if Zups don't function correctly.
            - For this library to correctly implement Service Requests, client applications would need to subscribe to notifications of Service Requests,
              and perform event handling routines to respond to arising Service Requests.
            
            From 'TDK-Lambda Genesys Power Supplies User Manual, 83-507-013':
             - Since Service Request messages may be sent from any supply at any time,
               there is a chance they can collide with other messages from other supplies.
             - Your controller software has to be sophisticated enough to read messages that
               may come at any time, and to recover if messages are corrupted by collisions.
             - If you need Service Request messaging, please contact TDK-Lambda for assistance.
               We can provide several special communication commands and settings that will help with this.
        """
        state = Zup._validate_binary_state(state)
        if state == 'Off':
            self._write_command(':SRT0;')
        else: # state == 'On'
            self._write_command(':SRT1;')
        return None

    def service_request_over_temperature_on(self) -> bool:
        """ Reads ZUP Service Request over-temperature state
            Inputs:       None
            Outputs:      bool, True if Service Request enabled, False if disabled
            ZUP command:  :SRT?;
        """
        self._write_command(':SRT?;')
        return self._read_response() == ':QT1;'

    def set_service_request_foldback(self, state: str) -> None:
        """ Programs ZUP Service Request Foldback state
            Inputs:        state: str in ('Off, 'On')
            Outputs:       None
            ZUP commands:  :SRF0; if 'Off'
                           :SRF1; if 'On'
            - Class Zup doesn't implement Service Requests; instead rely upon explicitly querying the Zups for correct operating status, and/or Zup operators
              noticing if Zups don't function correctly.
            - For this library to correctly implement Service Requests, client applications would need to subscribe to notifications of Service Requests,
              and perform event handling routines to respond to arising Service Requests.
            
            From 'TDK-Lambda Genesys Power Supplies User Manual, 83-507-013':
             - Since Service Request messages may be sent from any supply at any time,
               there is a chance they can collide with other messages from other supplies.
             - Your controller software has to be sophisticated enough to read messages that
               may come at any time, and to recover if messages are corrupted by collisions.
             - If you need Service Request messaging, please contact TDK-Lambda for assistance.
               We can provide several special communication commands and settings that will help with this.
        """
        state = Zup._validate_binary_state(state)
        if state == 'Off':
            self._write_command(':SRF0;')
        else: # state == 'On'
            self._write_command(':SRF1;')
        return None

    def service_request_foldback_on(self) -> bool:
        """ Reads ZUP Service Request Foldback state
            Inputs:       None
            Outputs:      bool, True if Service Request enabled, False if disabled
            ZUP command:  :SRF?;
        """
        self._write_command(':SRF?;')
        return self._read_response() == ':QF1;'

    def _write_command(self, command: str) -> None:
        """ Internal method to write ZUP commands through pySerial serial object
            Not intended for external use.
        """
        if (self.serial_port.port not in Zup.listening_addresses) or (Zup.listening_addresses[self.serial_port.port] != self.address):
            Zup.listening_addresses.update({self.serial_port.port : self.address})
            # Zups only need to be addressed at the begininng of a command sequence.
            # The most recently addressed Zup remains in "listen" mode until a different
            # Zup is addressed.
            # If the currently addressed & listening Zup is also the Zup object
            # being commanded, then skip re-addressing it, avoiding delay.
            time.sleep(0.015)
            adr = '{:0>2d}'.format(self.address)  # adr in set {'01', '02', '03'...'31'}
            cmd = ':ADR{};'.format(adr)
            self.serial_port.write(cmd.encode('utf-8'))
            time.sleep(0.035)
            # pySerial library requires UTF-8 byte encoding/decoding, not string.
            # Per Zup Manual, paragraph 5.6.1:
            #   - 10mSec minimum delay is required before sending ADR command.
            #   - 15mSec *average* command processing time for the Zup Series.
            #   - 30mSec delay required after sending ADR command.
            # Add 5 mSec safety margin to each delay, may need to adjust.
        self.serial_port.write(command.encode('utf-8'))
        time.sleep(0.020)
        return None

    def _read_response(self) -> str:
        """ Internal method to read ZUP responses through Pyserial serial object
            Not intended for external use.
        """
        rl = self.serial_port.readline().decode('utf-8')
        return rl.replace('\r\n', '')
        # pySerial library requires UTF-8 byte encoding/decoding, not string.
        # Per Zup Manual, paragraph 5.6.3, Zups append '\r\n' to their responses; remove them.

    @staticmethod
    def _validate_binary_state(state: str) -> str:
        """ Internal method to error check ('Off', 'On') states
            Not intended for external use.
        """
        if type(state) != str:
            raise TypeError('Invalid state, must be a str.')
        state = state.title()
        if state not in ('Off', 'On'):
            raise ValueError('Invalid state, must be in (''Off'', ''On'').')
        return state
