# Reference 'TDK-Lambda Zup Power Supplies User Manual, IA549-04-01R'.
# - Available at https://product.tdk.com/en/system/files?file=dam/doc/product/power/switching-power/prg-power/instruction_manual/Zup-uSerialPort-manual.pdf.
#
# FYI, UVP & OVP either don't program correctly or read back correctly; they consistently read back at 0.1V lower than programmed.
# - Programming ':UVP02.7;' & ':OVP03.3;' should result in 'UP02.7' & 'OP03.3' when queried with ':UVP?; & ':OVP?;'.
# - That is, programming UVP & OVP to 2.7V & 3.3V respectively should result in reading 2.7V & 3.3V back from the Zup.
#   But, both read back at 0.1V lower than programmed; 'UP02.6' & 'OP03.2'
# - Unsure why, but this 0.1V lower programming or reading error is consistent across 20V-20A, 20V-10A & 36V-6A Zup
#   models with a range of UVP & OVP values from 1V to 20V.
# - Could potentially compensate by programming UVP & OVP to 0.1V greater than desired, but since programming
#   may be correct and reading erroneous, forego.
#
# Phillip Smelt, 12/30/2021.
#
import time

class Zup(object):
       listening_addresses = {}
       CRLF = '\r\n'
       ADDRESS_RANGE = range(1, 32, 1)
       BAUD_RATES = [300, 600, 1200, 2400, 4800, 9600]
       KEYWORDS = {  'Address'	                                   :
                                                                      {'Set'        : ':ADR{};'},
                     'Amperage'                                       :
                                                                      {'Set'        : ':CUR{};',
                                                                       'Programmed' : ':CUR!;',
                                                                       'Read'       : ':CUR?;',
                                                                       'PrefixProg' : 'SA',
                                                                       'PrefixRead' : 'AA'},
                     'Autostart'                                      :
                                                                      {'off'        : ':AST0;',
                                                                       'ON'         : ':AST1;',
                                                                       'Read'       : ':AST?;',
                                                                       'Is off'      : 'AS0' + CRLF,
                                                                       'Is ON'       : 'AS1' + CRLF},
                     'Foldback'                                       :
                                                                      {'Arm'        : ':FLD1;',
                                                                       'Release'    : ':FLD0;',
                                                                       'Cancel'     : ':FLD2;',
                                                                       'Read'       : ':FLD?;',
                                                                       'Is off'      : 'FD0' + CRLF,
                                                                       'Is ON'       : 'FD1' + CRLF},
                     'Model'	                                   :
                                                                      {'Read'       : ':MDL?;'},
                     'off'                                            : 
                                                                      False,
                     'ON'                                             :
                                                                      True,
                     'Output'	                                   :
                                                                      {'off'        : ':OUT0;',
                                                                       'ON'         : ':OUT1;',
                                                                       'Read'       : ':OUT?;',
                                                                       'Is off'      : 'OT0' + CRLF,
                                                                       'Is ON'       : 'OT1' + CRLF},
                     'Register'           :      {'All'               :
                                                                      {'Clear'      : ':DCL;'},
                                                  'Alarm'             :
                                                                      {'Read'       : ':ALM?;'},
                                                  'Operation'         :
                                                                      {'Read'       : ':STA?;'},
                                                  'Program'           : 
                                                                      {'Read'       : ':STP?;'}},
                     'Remote'	                                   :
                                                                      {'Local'      : ':RMT0;',
                                                                       'Remote'     : ':RMT1;',
                                                                       'Latched'    : ':RMT2;',
                                                                       'Read'       : ':RMT?;',
                                                                       'Is ON'       : 'RM1' + CRLF,
                                                                       'IsLatched'  : 'RM2' + CRLF},
                     'Revision'	                                   :	
                                                                      {'Read'       : ':REV?;'},
                     'Status'	                                   :
                                                                      {'Read'       : ':STT?;'},
                     'ServiceRequest'     :      {'OverVoltage'       : 
                                                                      {'off'        : ':SRV0;',
                                                                       'ON'         : ':SRV1;',
                                                                       'Read'       : ':SRV?;',
                                                                       'Is off'      : 'QV0' + CRLF,
                                                                       'Is ON'       : 'QV1' + CRLF},
                                                  'OverTemperature'   : 
                                                                      {'off'        : ':SRT0;',
                                                                       'ON'         : ':SRT1;',
                                                                       'Read'       : ':SRT?;',
                                                                       'Is off'      : 'QT0' + CRLF,
                                                                       'Is ON'       : 'QT1' + CRLF},
                                                  'Foldback'          : 
                                                                      {'off'        : ':SRF0;',
                                                                       'ON'         : ':SRF1;',
                                                                       'Read'       : ':SRF?;',
                                                                       'Is off'      : 'QF0' + CRLF,
                                                                       'Is ON'       : 'QF1' + CRLF}},
                     'Voltage'                                        :
                                                                      {'Set'        : ':VOL{};',
                                                                       'Programmed' : ':VOL!;',
                                                                       'Read'       : ':VOL?;',
                                                                       'PrefixProg' : 'SV',
                                                                       'PrefixRead' : 'AV'},
                     'VoltageProtection'  :    	{'Under'             :
                                                                      {'Set'        : ':UVP{};',
                                                                       'Read'       : ':UVP?;',
                                                                       'PrefixRead' : 'UP'},
                                                  'Over'              :
                                                                      {'Set'        : ':OVP{};',
                                                                       'Read'       : ':OVP?;',
                                                                       'PrefixRead' : 'OP'}}}

       FORMATS = {   '1.2'  : '{:0>4.2f}',
                     '1.3'  : '{:0>5.3f}',
                     '1.4'  : '{:0>6.4f}',
                     '2.1'  : '{:0>4.1f}',
                     '2.2'  : '{:0>5.2f}',
                     '2.3'  : '{:0>6.3f}',
                     '3.1'  : '{:0>5.1f}',
                     '3.2'  : '{:0>6.2f}'}

       # Zup Manual Table 5.5.3.  VOL['MAX'] allowed to be up to 105% of rated voltage.
       VOLs = {'ZUP6-XY'   : {'min': 0.0, 'MAX': 6.300,  'Format': FORMATS['1.3']},
               'ZUP10-XY'  : {'min': 0.0, 'MAX': 10.500, 'Format': FORMATS['2.3']},
               'ZUP20-XY'  : {'min': 0.0, 'MAX': 21.000, 'Format': FORMATS['2.3']},
               'ZUP36-XY'  : {'min': 0.0, 'MAX': 37.80,  'Format': FORMATS['2.2']},
               'ZUP60-XY'  : {'min': 0.0, 'MAX': 63.00,  'Format': FORMATS['2.2']},
               'ZUP80-XY'  : {'min': 0.0, 'MAX': 84.00,  'Format': FORMATS['2.2']},
               'ZUP120-XY' : {'min': 0.0, 'MAX': 126.00, 'Format': FORMATS['3.2']}}

       # Zup Manual Table 5.5.4.  CUR['MAX'] allowed to be up to 105% of rated current.
       CURs = {'ZUP6-33'   : {'min': 0.0, 'MAX': 34.65,  'Format': FORMATS['2.2']},
               'ZUP6-66'   : {'min': 0.0, 'MAX': 69.30,  'Format': FORMATS['2.2']},
               'ZUP6-132'  : {'min': 0.0, 'MAX': 138.60, 'Format': FORMATS['3.2']},
               'ZUP10-20'  : {'min': 0.0, 'MAX': 21.000, 'Format': FORMATS['2.3']},
               'ZUP10-40'  : {'min': 0.0, 'MAX': 42.00,  'Format': FORMATS['2.2']},
               'ZUP10-80'  : {'min': 0.0, 'MAX': 84.00,  'Format': FORMATS['2.2']},
               'ZUP20-10'  : {'min': 0.0, 'MAX': 10.500, 'Format': FORMATS['2.3']},
               'ZUP20-20'  : {'min': 0.0, 'MAX': 21.000, 'Format': FORMATS['2.3']},
               'ZUP20-40'  : {'min': 0.0, 'MAX': 42.00,  'Format': FORMATS['2.2']},
               'ZUP36-6'   : {'min': 0.0, 'MAX': 6.300,  'Format': FORMATS['1.3']},
               'ZUP36-12'  : {'min': 0.0, 'MAX': 12.600, 'Format': FORMATS['2.3']},
               'ZUP36-24'  : {'min': 0.0, 'MAX': 25.200, 'Format': FORMATS['2.3']},
               'ZUP60-3.5' : {'min': 0.0, 'MAX': 3.675,  'Format': FORMATS['1.3']},
               'ZUP60-7'   : {'min': 0.0, 'MAX': 7.350,  'Format': FORMATS['1.3']},
               'ZUP60-14'  : {'min': 0.0, 'MAX': 14.700, 'Format': FORMATS['2.3']},
               'ZUP80-2.5' : {'min': 0.0, 'MAX': 2.6250, 'Format': FORMATS['1.4']},
               'ZUP80-5'   : {'min': 0.0, 'MAX': 5.250,  'Format': FORMATS['1.3']},
               'ZUP120-1.8': {'min': 0.0, 'MAX': 1.8900, 'Format': FORMATS['1.4']},
               'ZUP120-3.6': {'min': 0.0, 'MAX': 3.780,  'Format': FORMATS['1.3']}}

       # Zup Manual Table 5.5.11.
       OVPs = {'ZUP6-XY'   : {'min': 0.2, 'MAX': 7.50,   'Format': FORMATS['1.2']},
               'ZUP10-XY'  : {'min': 0.5, 'MAX': 13.0,   'Format': FORMATS['2.1']},
               'ZUP20-XY'  : {'min': 1.0, 'MAX': 24.0,   'Format': FORMATS['2.1']},
               'ZUP36-XY'  : {'min': 0.8, 'MAX': 40.0,   'Format': FORMATS['2.1']},
               'ZUP60-XY'  : {'min': 3.0, 'MAX': 66.0,   'Format': FORMATS['2.1']},
               'ZUP80-XY'  : {'min': 4.0, 'MAX': 88.0,   'Format': FORMATS['2.1']},
               'ZUP120-XY' : {'min': 6.0, 'MAX': 132.0,  'Format': FORMATS['3.1']}}

       # Zup Manual Table 5.5.13.  UVP['MAX'] ≈  95% * VOL['MAX'].
       UVPs = {'ZUP6-XY'   : {'min': 0.0, 'MAX': 5.98,   'Format': FORMATS['1.2']},
               'ZUP10-XY'  : {'min': 0.0, 'MAX': 9.97,   'Format': FORMATS['1.2']},
               'ZUP20-XY'  : {'min': 0.0, 'MAX': 19.9,   'Format': FORMATS['2.1']},
               'ZUP36-XY'  : {'min': 0.0, 'MAX': 35.9,   'Format': FORMATS['2.1']},
               'ZUP60-XY'  : {'min': 0.0, 'MAX': 59.8,   'Format': FORMATS['2.1']},
               'ZUP80-XY'  : {'min': 0.0, 'MAX': 79.8,   'Format': FORMATS['2.1']},
               'ZUP120-XY' : {'min': 0.0, 'MAX': 119.8,  'Format': FORMATS['3.1']}}

       def __init__(self, address, serial_port):
              if address not in Zup.ADDRESS_RANGE:
                     raise ValueError('Invalid address, must be an integer in Python ' + str(Zup.ADDRESS_RANGE) + '.')
              if serial_port.baudrate not in Zup.BAUD_RATES:
                     raise ValueError('Invalid baud rate, must be in list ' + str(Zup.BAUD_RATES) + '.')
              self.serial_port = serial_port
              self.address = address                           # Integer in range [1..31]
              mdl = self.get_model()                           # Assuming mdl ='Nemic-Lambda ZUp(36V-6A)\r\n':
              mdl = mdl[mdl.index('(') + 1 : mdl.index(')')]   # mdl = 36V-6A
              v = mdl[ : mdl.index('V')]                       # v = '36'
              a = mdl[mdl.index('-') + 1 : mdl.index('A')]     # a = '6'
              mdl = 'ZUP{}-{}'.format(v, a)                    # mdl = 'ZUP36-6'
              self.CUR = Zup.CURs[mdl]                         # self.CUR = {'min': 0.0, 'MAX': 6.300,  'Format': FORMATS['1.3']}
              mdl = 'ZUP{}-XY'.format(v)                       # mdl = 'ZUP36-XY'
              self.VOL = Zup.VOLs[mdl]                         # self.VOL = {'min': 0.0, 'MAX': 37.80,  'Format': FORMATS['2.2']}
              self.OVP = Zup.OVPs[mdl]                         # self.OVP = {'min': 0.8, 'MAX': 40.0,   'Format': FORMATS['2.1']}
              self.UVP = Zup.UVPs[mdl]                         # self.UVP = {'min': 0.0, 'MAX': 35.9,   'Format': FORMATS['2.1']}
              return None

       def initialize(self):
              self.set_power(Zup.KEYWORDS['off'])
              self.set_remote(Zup.KEYWORDS['Remote']['Latched'])
              self.set_autostart(Zup.KEYWORDS['off'])
              self.set_foldback(Zup.KEYWORDS['Foldback']['Cancel'])
              self.clear_register()
              self.set_service_request_over_voltage(Zup.KEYWORDS['off'])
              self.set_service_request_over_temperature(Zup.KEYWORDS['off'])
              self.set_service_request_foldback(Zup.KEYWORDS['off'])
              # Zup Manual paragraph 5.7:
              #  - If Service Requests are enabled, a Zup can initiate Service Request messages to its controlling PC through its Serial Port.
              #  - May investigate implementing Service Requests in the future, but for now will rely upon explicitly querying the Zups for correct operating
              #    status, and/or Zup operators noticing if Zups don't function correctly.
              #    - Even if this library implemented Service Requests, client applications would still need to subscribe to notifications of Service Requests, 
              #      and implement event handling routines to respond to arising Service Requests.
              self.set_under_voltage_protection(self.UVP['min'])
              self.set_over_voltage_protection(self.OVP['MAX'])
              # Minumum under-voltage & maximum over-voltage effectively disable under/over-voltage protections, AKA UVP & OVP.
              return None

       def de_initialize(self):
              self.initialize()
              self.set_remote(Zup.KEYWORDS['Remote']['Remote'])
              return None

       def set_amperage(self, a):
              if type(a) not in [int, float]:
                     raise ValueError('Invalid amperage, must be real number.')
              if not (self.CUR['min'] <= a <= self.CUR['MAX']):
                     raise ValueError('Invalid amperage, must be in range [{}..{}].'.format(self.CUR['min'], self.CUR['MAX']))
              a = self.CUR['Format'].format(a)
              self._write_command(Zup.KEYWORDS['Amperage']['Set'].format(a)) # :CUR{};
              return None

       def get_amperage_actual(self):
              self._write_command(Zup.KEYWORDS['Amperage']['Read'])           # :CUR?;
              aa = self._read_response()                                      # aa = 'AA1.234'.
              aa = aa.replace(Zup.KEYWORDS['Amperage']['PrefixRead'], '')     # aa = '1.234'
              return float(aa)                                                # return 1.234

       def get_amperage_set(self):
              self._write_command(Zup.KEYWORDS['Amperage']['Programmed'])     # :CUR!;
              sa = self._read_response()                                      # sa = 'SA1.234'.
              sa = sa.replace(Zup.KEYWORDS['Amperage']['PrefixProg'], '')     # sa = '1.234'
              return float(sa)                                                # return 1.234

       def set_voltage(self, v):
              if type(v) not in [int, float]:
                     raise ValueError('Invalid voltage, must be a real number.')
              if not (self.VOL['min'] <= v <= self.VOL['MAX']):
                     raise ValueError('Invalid voltage, must be in range [{}..{}].'.format(self.VOL['min'], self.VOL['MAX']))
              if not (self.get_under_voltage_protection() / 0.95 <= v <= self.get_over_voltage_protection() / 1.05):
                     # UVP['min'] <= VOL['min'] <= get_under_voltage_protection(self) / 0.95 <= v <= get_over_voltage_protection(self) / 1.05 <= OVP['MAX'].
                     # Unknown if get_over_voltage_protection(self) <= VOL['MAX'], hence 2 inequality checks.
                     raise ValueError('Invalid voltage, must be in range [{}..{}].'.format(self.get_under_voltage_protection(self) / 0.95, self.get_over_voltage_protection(self) / 1.05))
              v = self.VOL['Format'].format(v)
              self._write_command(Zup.KEYWORDS['Voltage']['Set'].format(v))  # :VOL{};
              return None

       def get_voltage_actual(self):
              self._write_command(Zup.KEYWORDS['Voltage']['Read'])            # :VOL?;
              av = self._read_response()                                      # Assuming av = 'AV05.12'.
              av = av.replace(Zup.KEYWORDS['Voltage']['PrefixRead'], '')      # av = '05.12'
              return float(av)                                                # return 5.12

       def get_voltage_set(self):
              self._write_command(Zup.KEYWORDS['Voltage']['Programmed'])      # :VOL!;
              sv = self._read_response()                                      # Assuming sv = 'SV05.00'.
              sv = sv.replace(Zup.KEYWORDS['Voltage']['PrefixProg'], '')      # sv = '05.00'
              return float(sv)                                                # return 5.00

       def set_under_voltage_protection(self, uv):
              if type(uv) not in [int, float]:
                     raise ValueError('Invalid under-voltage, must be a real number.')
              if not (self.UVP['min'] <= uv <= self.get_voltage_set() * 0.95):
                     # UVP['min'] <= uv <= get_voltage_set(self) * 0.95 <= UVP['MAX'].
                     raise ValueError('Invalid under-voltage, must be in range [{}..{}].'.format(self.UVP['min'], self.get_voltage_set(self) * 0.95))
              uv = self.UVP['Format'].format(uv)
              self._write_command(Zup.KEYWORDS['VoltageProtection']['Under']['Set'].format(uv))  # :UVP{};
              return None

       def get_under_voltage_protection(self):
              self._write_command(Zup.KEYWORDS['VoltageProtection']['Under']['Read'])        # :UVP?;
              up = self._read_response()                                                     # up = 'UP04.5'.
              up = up.replace(Zup.KEYWORDS['VoltageProtection']['Under']['PrefixRead'], '')  # up = '04.5'
              return float(up)                                                               # return 4.5

       def set_over_voltage_protection(self, ov):
              if type(ov) not in [int, float]:
                     raise ValueError('Invalid over-voltage, must be a real number.')
              if not (self.get_voltage_set() * 1.05 <= ov <= self.OVP['MAX']):
                     # OVP['min'] <= get_voltage_set(self) * 1.05 <= ov <= OVP['MAX']
                     raise ValueError('Invalid under-voltage, must be in range [{}..{}].'.format(self.get_voltage_set(self) * 1.05, self.OVP['MAX']))
              ov = self.UVP['Format'].format(ov)
              self._write_command(Zup.KEYWORDS['VoltageProtection']['Over']['Set'].format(ov))   # :OVP{};
              return None

       def get_over_voltage_protection(self):
              self._write_command(Zup.KEYWORDS['VoltageProtection']['Over']['Read'])         # :OVP?;
              op = self._read_response()                                                     # op = 'OP05.5'.
              op = op.replace(Zup.KEYWORDS['VoltageProtection']['Over']['PrefixRead'], '')   # op = '05.5'
              return float(op)                                                               # return 5.5

       def set_power(self, state):
              self._validate_binary_state(self, state)
              if state == Zup.KEYWORDS['off']:
                     self._write_command(Zup.KEYWORDS['Output']['off'])                # :OUT0;
              else: # state == Zup.KEYWORDS['ON']
                     self._write_command(Zup.KEYWORDS['Output']['ON'])                 # :OUT1;                     
              return None

       def power_on(self):
              self._write_command(Zup.KEYWORDS['Output']['Read'])                      # :OUT?;
              ps = self._read_response()
              return ps == Zup.KEYWORDS['Output']['Read']['Is ON']

       def get_status(self):
              self._write_command(Zup.KEYWORDS['Status']['Read'])                      # :STT?;
              return self._read_response()

       def get_statuses(self):
              status, statuses = '', []
              self._write_command(Zup.KEYWORDS['Model']['Read'])                              ; status += self._read_response()   # :MDL?; 
              self._write_command(Zup.KEYWORDS['Revision']['Read'])                           ; status += self._read_response()   # :REV?;
              self._write_command(Zup.KEYWORDS['Voltage']['Programmed'])                      ; status += self._read_response()   # :VOL!;
              self._write_command(Zup.KEYWORDS['Voltage']['Read'])                            ; status += self._read_response()   # :VOL?;
              self._write_command(Zup.KEYWORDS['VoltageProtection']['Under']['Read'])         ; status += self._read_response()   # :UVP?;
              self._write_command(Zup.KEYWORDS['VoltageProtection']['Over']['Read'])          ; status += self._read_response()   # :OVP?;
              self._write_command(Zup.KEYWORDS['Amperage']['Programmed'])                     ; status += self._read_response()   # :CUR!;
              self._write_command(Zup.KEYWORDS['Amperage']['Read'])                           ; status += self._read_response()   # :CUR?;
              self._write_command(Zup.KEYWORDS['Foldback']['Read'])                           ; status += self._read_response()   # :FLD?;
              self._write_command(Zup.KEYWORDS['Remote']['Read'])                             ; status += self._read_response()   # :RMT?;
              self._write_command(Zup.KEYWORDS['Autostart']['Read'])                          ; status += self._read_response()   # :AST?;
              self._write_command(Zup.KEYWORDS['Register']['Operation']['Read'])              ; status += self._read_response()   # :STA?;
              self._write_command(Zup.KEYWORDS['Register']['Programming']['Read'])            ; status += self._read_response()   # :STP?;
              self._write_command(Zup.KEYWORDS['Register']['Alarm']['Read'])                  ; status += self._read_response()   # :ALM?;
              self._write_command(Zup.KEYWORDS['ServiceRequest']['OverVoltage']['Read'])      ; status += self._read_response()   # :SRV?;
              self._write_command(Zup.KEYWORDS['ServiceRequest']['OverTemperature']['Read'])  ; status += self._read_response()   # :SRT?;
              self._write_command(Zup.KEYWORDS['ServiceRequest']['Foldback']['Read'])         ; status += self._read_response()   # :SRF?;
              # Per Zup Manual, paragraph 5.6.3,   
              # Zup appends '\r\n' to it's responses, so each status has a carriage return/linefeed
              # between each '+=' concatenation, which prints out nicely onscreen.
              statuses.append([self.address, status])
              return statuses

       def set_autostart(self, state):
              self._validate_binary_state(self, state)              
              if state == Zup.KEYWORDS['off']:               
                     self._write_command(Zup.KEYWORDS['Autostart']['off'])             # :AST0;
              else: # state == Zup.KEYWORDS['ON']
                     self._write_command(Zup.KEYWORDS['Autostart']['ON'])              # :AST1;                     
              return None

       def autostart_on(self):
              self._write_command(Zup.KEYWORDS['Autostart']['Read'])                   # :AST?;
              at = self._read_response()
              return  at == Zup.KEYWORDS['Autostart']['Read']['Is ON']

       def set_foldback(self, state):
              if state not in [Zup.KEYWORDS['Foldback']['Arm'], Zup.KEYWORDS['Foldback']['Release'], Zup.KEYWORDS['Foldback']['Cancel']]:
                     raise ValueError('Invalid foldback state, must be a valid state in ' + str(Zup.KEYWORDS['Foldback']) + '.')
              self._write_command(state)
              return None

       def foldback_on(self):
              self._write_command(Zup.KEYWORDS['Foldback']['Read'])                    # :FLD?;
              fb = self._read_response()
              return fb == Zup.KEYWORDS['Foldback']['Read']['Is ON']

       def get_model(self):
              self._write_command(Zup.KEYWORDS['Model']['Read'])                       # :MDL?;
              return self._read_response()

       def get_revision(self):
              self._write_command(Zup.KEYWORDS['Revision']['Read'])                    # :REV?;
              return self._read_response()

       def clear_register(self):
              self._write_command(Zup.KEYWORDS['Register']['All']['Clear'])            # :DCL;
              return None

       def get_register_alarm(self):
              self._write_command(Zup.KEYWORDS['Register']['Alarm']['Read'])           # :ALM?;
              return self._read_response()

       def get_register_operation(self):
              self._write_command(Zup.KEYWORDS['Register']['Operation']['Read'])       # :STA?;
              return self._read_response()

       def get_register_program(self):
              self._write_command(Zup.KEYWORDS['Register']['Program']['Read'])         # :STP?;
              return self._read_response()

       def set_remote(self, state):
              if state not in Zup.KEYWORDS['Remote']:
                     raise ValueError('Invalid remote state, must be a valid state in set ' + str(Zup.KEYWORDS['Remote']) + '.')
              if state == 'local':               
                     self._write_command(Zup.KEYWORDS['Remote']['Local'])              # :RMT0;
              elif state == 'remote':
                     self._write_command(Zup.KEYWORDS['Remote']['Remote'])             # :RMT1;                     
              else: # state == 'latched'
                     self._write_command(Zup.KEYWORDS['Remote']['Latched'])            # :RMT2;
              return None

       def remote_on(self):
              self._write_command(Zup.KEYWORDS['Remote']['Read'])                      # :RMT?;
              r = self._read_response()
              return r == Zup.KEYWORDS['Remote']['Read']['Is ON']

       def set_service_request_over_voltage(self, state):
              self._validate_binary_state(self, state)              
              if state == Zup.KEYWORDS['off']:               
                     self._write_command(Zup.KEYWORDS['ServiceRequest']['OverVoltage']['off'])     # :SRV0;
              else: # state == Zup.KEYWORDS['ON']
                     self._write_command(Zup.KEYWORDS['ServiceRequest']['OverVoltage']['ON'])      # :SRV1;                   
              return None

       def service_request_over_voltage_on(self):
              self._write_command(Zup.KEYWORDS['ServiceRequest']['OverVoltage']['Read'])           # :SRV?;
              srov = self._read_response()
              return srov == Zup.KEYWORDS['ServiceRequest']['OverVoltage']['Read']['Is ON']

       def set_service_request_over_temperature(self, state):
              self._validate_binary_state(self, state)
              if state == Zup.KEYWORDS['off']:               
                     self._write_command(Zup.KEYWORDS['ServiceRequest']['OverTemperature']['off']) # :SRT0;
              else: # state == Zup.KEYWORDS['ON']
                     self._write_command(Zup.KEYWORDS['ServiceRequest']['OverTemperature']['ON'])  # :SRT1;                   
              return None

       def service_request_over_temperature_on(self):
              self._write_command(Zup.KEYWORDS['ServiceRequest']['OverTemperature']['Read'])       # :SRT?;
              srot = self._read_response()
              return srot == Zup.KEYWORDS['ServiceRequest']['OverTemperature']['Read']['Is ON']

       def set_service_request_foldback(self, state):
              self._validate_binary_state(self, state)
              if state == Zup.KEYWORDS['off']:              
                     self._write_command(Zup.KEYWORDS['ServiceRequest']['Foldback']['off'])        # :SRF0;
              else: # state == Zup.KEYWORDS['ON']
                     self._write_command(Zup.KEYWORDS['ServiceRequest']['Foldback']['ON'])         # :SRF1;                   
              return None

       def service_request_foldback_on(self):
              self._write_command(Zup.KEYWORDS['ServiceRequest']['Foldback']['Read'])              # :SRF?;
              srfb = self._read_response()
              return srfb == Zup.KEYWORDS['ServiceRequest']['Foldback']['Read']['Is ON']

       def issue_commands(self, commands):
              responses = []
              for command in commands:
                     self._write_command(command)
                     if command[4:5] in ['?', '!']:
                            responses.append([command, self._read_response()])
                     else:
                            responses.append([command, 'Response N/A'])
              return responses

       def _write_command(self, command):
              if (self.serial_port.port not in Zup.listening_addresses) or (Zup.listening_addresses[self.serial_port.port] != self.address):
                     Zup.listening_addresses.update({self.serial_port.port : self.address})
                     # Zups only need to be addressed at the begininng of a command sequence.
                     # The most recently addressed Zup remains in "listen" mode until a different
                     # Zup is addressed.
                     # If the currently addressed & listening Zup is also the Zup object 
                     # being commanded, then skip re-addressing it, avoiding delay.
                     time.sleep(0.015)
                     adr = '{:0>2d}'.format(self.address)                   # String in set {'01', '02', '03'...'31'}
                     cmd = Zup.KEYWORDS['Address']['Set'].format(adr)       # :ADR{};
                     self.serial_port.write(cmd.encode('utf-8'))
                     time.sleep(0.035)
                     # Python's pySerial library requires UTF-8 byte encoding/decoding, not string.
                     # Per Zup Manual, paragraph 5.6.1:
                     #   - 10mSec minimum delay is required before sending ADR command.
                     #   - 30mSec delay required after sending ADR command.
                     # Add 5 mSec safety margin to each delay, may need to adjust.
              self.serial_port.write(command.encode('utf-8'))
              time.sleep(0.020)
              # Python's pySerial library requires UTF-8 byte encoding/decoding, not string.
              # Per Zup Manual, paragraph 5.6.1:
              #   - 15mSec *average* command processing time for the Zup Series.
              # Add 5 mSec safety margin to delay, may need to adjust.
              return None

       def _read_response(self):
              return self.serial_port.readline().decode('utf-8')
              # Python's pySerial library requires UTF-8 byte encoding/decoding, not string.

       def _validate_binary_state(self, state):
              if state not in [Zup.KEYWORDS['off'], Zup.KEYWORDS['ON']]:
                     raise ValueError('Invalid binary state, must be in [' + str(Zup.KEYWORDS['off']) + ', ' + str(Zup.KEYWORDS['ON']) + '].')
              return None