"""
    "TDK", "TDK-Lambda" & "Zup" are registered trademarks of the TDK Corporation.
    "Python" is a registered trademark of the Python Software Foundation.
    pySerial Copyrighted by Chris Liechti.
    pytest Copyrighted by Holger Krekel and pytest-dev team.
    This script Copyright Amphenol Borisch Technologies, 2022
    - https://www.borisch.com/

    Pytest tests for Zup class.
    Dependencies:
    - Functioning TDK-Lambda ZUP power supply(s) connected to PC via RS232 and/or RS485 serial.
    - Class Zup's _write_command(command) & _read_response() methods are assumed to be bug-free.
    - pySerial library:
       - https://pypi.org/project/pyserial/
       - https://pyserial.readthedocs.io/en/latest/pyserial.html
    - pytest library:
       - https://docs.pytest.org/en/6.2.x/

    Reference 'TDK-Lambda Zup Power Supplies User Manual, IA549-04-01R', especially Chapter 5, 'RS232 & RS485 Remote Control':
      - https://product.tdk.com/system/files/dam/doc/product/power/switching-power/prg-power/instruction_manual/zup-user-manual.pdf
"""
import time
import pytest # https://docs.pytest.org/en/6.2.x/
import serial # https://pypi.org/project/pyserial/
from Zup import Zup

def test_formats() -> None:
    a = 0.2468
    assert Zup.FORMATS['1.2'].format(a) == '0.25'     ;  print(Zup.FORMATS['1.2'].format(a))
    assert Zup.FORMATS['1.3'].format(a) == '0.247'    ;  print(Zup.FORMATS['1.3'].format(a))
    assert Zup.FORMATS['1.4'].format(a) == '0.2468'   ;  print(Zup.FORMATS['1.4'].format(a))

    a = 2.2468
    assert Zup.FORMATS['1.2'].format(a) == '2.25'     ;  print(Zup.FORMATS['1.2'].format(a))
    assert Zup.FORMATS['1.3'].format(a) == '2.247'    ;  print(Zup.FORMATS['1.3'].format(a))
    assert Zup.FORMATS['1.4'].format(a) == '2.2468'   ;  print(Zup.FORMATS['1.4'].format(a))

    a = 42.2468
    assert Zup.FORMATS['1.2'].format(a) == '42.25'    ;  print(Zup.FORMATS['1.2'].format(a))
    assert Zup.FORMATS['1.3'].format(a) == '42.247'   ;  print(Zup.FORMATS['1.3'].format(a))
    assert Zup.FORMATS['1.4'].format(a) == '42.2468'  ;  print(Zup.FORMATS['1.4'].format(a))

    a = 0.2468
    assert Zup.FORMATS['2.1'].format(a) == '00.2'    ;  print(Zup.FORMATS['2.1'].format(a))
    assert Zup.FORMATS['2.2'].format(a) == '00.25'   ;  print(Zup.FORMATS['2.2'].format(a))
    assert Zup.FORMATS['2.3'].format(a) == '00.247'  ;  print(Zup.FORMATS['2.3'].format(a))

    a = 2.2468
    assert Zup.FORMATS['2.1'].format(a) == '02.2'    ;  print(Zup.FORMATS['2.1'].format(a))
    assert Zup.FORMATS['2.2'].format(a) == '02.25'   ;  print(Zup.FORMATS['2.2'].format(a))
    assert Zup.FORMATS['2.3'].format(a) == '02.247'  ;  print(Zup.FORMATS['2.3'].format(a))

    a = 42.2468
    assert Zup.FORMATS['2.1'].format(a) == '42.2'    ;  print(Zup.FORMATS['2.1'].format(a))
    assert Zup.FORMATS['2.2'].format(a) == '42.25'   ;  print(Zup.FORMATS['2.2'].format(a))
    assert Zup.FORMATS['2.3'].format(a) == '42.247'  ;  print(Zup.FORMATS['2.3'].format(a))

    a = 642.2468
    assert Zup.FORMATS['2.1'].format(a) == '642.2'   ;  print(Zup.FORMATS['2.1'].format(a))
    assert Zup.FORMATS['2.2'].format(a) == '642.25'  ;  print(Zup.FORMATS['2.2'].format(a))
    assert Zup.FORMATS['2.3'].format(a) == '642.247' ;  print(Zup.FORMATS['2.3'].format(a))

    a = 0.2468
    assert Zup.FORMATS['3.1'].format(a) == '000.2'   ;  print(Zup.FORMATS['3.1'].format(a))
    assert Zup.FORMATS['3.2'].format(a) == '000.25'  ;  print(Zup.FORMATS['3.2'].format(a))

    a = 2.2468
    assert Zup.FORMATS['3.1'].format(a) == '002.2'   ;  print(Zup.FORMATS['3.1'].format(a))
    assert Zup.FORMATS['3.2'].format(a) == '002.25'  ;  print(Zup.FORMATS['3.2'].format(a))

    a = 42.2468
    assert Zup.FORMATS['3.1'].format(a) == '042.2'   ;  print(Zup.FORMATS['3.1'].format(a))
    assert Zup.FORMATS['3.2'].format(a) == '042.25'  ;  print(Zup.FORMATS['3.2'].format(a))

    a = 642.2468
    assert Zup.FORMATS['3.1'].format(a) == '642.2'   ;  print(Zup.FORMATS['3.1'].format(a))
    assert Zup.FORMATS['3.2'].format(a) == '642.25'  ;  print(Zup.FORMATS['3.2'].format(a))

    a = 8642.2468
    assert Zup.FORMATS['3.1'].format(a) == '8642.2'  ;  print(Zup.FORMATS['3.1'].format(a))
    assert Zup.FORMATS['3.2'].format(a) == '8642.25' ;  print(Zup.FORMATS['3.2'].format(a))
    return None

def test_MODELS() -> None:
    MODELS = {'Nemic-Lambda ZUP(6V-33A)'      : {'mdl' : '6V-33A',    'v' : '6',   'a' :  '33',   'mva' : 'ZUP6-33',    'mxy' : 'ZUP6-XY'},
              'Nemic-Lambda ZUP(6V-66A)'      : {'mdl' : '6V-66A',    'v' : '6',   'a' :  '66',   'mva' : 'ZUP6-66',    'mxy' : 'ZUP6-XY'},
              'Nemic-Lambda ZUP(6V-132A)'     : {'mdl' : '6V-132A',   'v' : '6',   'a' : '132',   'mva' : 'ZUP6-132',   'mxy' : 'ZUP6-XY'},
              'Nemic-Lambda ZUP(10V-20A)'     : {'mdl' : '10V-20A',   'v' : '10',  'a' :  '20',   'mva' : 'ZUP10-20',   'mxy' : 'ZUP10-XY'},
              'Nemic-Lambda ZUP(10V-40A)'     : {'mdl' : '10V-40A',   'v' : '10',  'a' :  '40',   'mva' : 'ZUP10-40',   'mxy' : 'ZUP10-XY'},
              'Nemic-Lambda ZUP(10V-80A)'     : {'mdl' : '10V-80A',   'v' : '10',  'a' :  '80',   'mva' : 'ZUP10-80',   'mxy' : 'ZUP10-XY'},
              'Nemic-Lambda ZUP(20V-10A)'     : {'mdl' : '20V-10A',   'v' : '20',  'a' :  '10',   'mva' : 'ZUP20-10',   'mxy' : 'ZUP20-XY'},
              'Nemic-Lambda ZUP(20V-20A)'     : {'mdl' : '20V-20A',   'v' : '20',  'a' :  '20',   'mva' : 'ZUP20-20',   'mxy' : 'ZUP20-XY'},
              'Nemic-Lambda ZUP(20V-40A)'     : {'mdl' : '20V-40A',   'v' : '20',  'a' :  '40',   'mva' : 'ZUP20-40',   'mxy' : 'ZUP20-XY'},
              'Nemic-Lambda ZUP(36V-6A)'      : {'mdl' : '36V-6A',    'v' : '36',  'a' :   '6',   'mva' : 'ZUP36-6',    'mxy' : 'ZUP36-XY'},
              'Nemic-Lambda ZUP(36V-12A)'     : {'mdl' : '36V-12A',   'v' : '36',  'a' :  '12',   'mva' : 'ZUP36-12',   'mxy' : 'ZUP36-XY'},
              'Nemic-Lambda ZUP(36V-24A)'     : {'mdl' : '36V-24A',   'v' : '36',  'a' :  '24',   'mva' : 'ZUP36-24',   'mxy' : 'ZUP36-XY'},
              'Nemic-Lambda ZUP(60V-3.5A)'    : {'mdl' : '60V-3.5A',  'v' : '60',  'a' :   '3.5', 'mva' : 'ZUP60-3.5',  'mxy' : 'ZUP60-XY'},
              'Nemic-Lambda ZUP(60V-7A)'      : {'mdl' : '60V-7A',    'v' : '60',  'a' :   '7',   'mva' : 'ZUP60-7',    'mxy' : 'ZUP60-XY'},
              'Nemic-Lambda ZUP(60V-14A)'     : {'mdl' : '60V-14A',   'v' : '60',  'a' :  '14',   'mva' : 'ZUP60-14',   'mxy' : 'ZUP60-XY'},
              'Nemic-Lambda ZUP(80V-2.5A)'    : {'mdl' : '80V-2.5A',  'v' : '80',  'a' :   '2.5', 'mva' : 'ZUP80-2.5',  'mxy' : 'ZUP80-XY'},
              'Nemic-Lambda ZUP(80V-5A)'      : {'mdl' : '80V-5A',    'v' : '80',  'a' :   '5',   'mva' : 'ZUP80-5',    'mxy' : 'ZUP80-XY'},
              'Nemic-Lambda ZUP(120V-1.8A)'   : {'mdl' : '120V-1.8A', 'v' : '120', 'a' :   '1.8', 'mva' : 'ZUP120-1.8', 'mxy' : 'ZUP120-XY'},
              'Nemic-Lambda ZUP(120V-3.6A)'   : {'mdl' : '120V-3.6A', 'v' : '120', 'a' :   '3.6', 'mva' : 'ZUP120-3.6', 'mxy' : 'ZUP120-XY'}}
    for model in MODELS:
        print('Model:   ' + model)
        mdl = model[model.index('(') + 1 : model.index(')')]  ;  print('mdl:     ' + mdl)
        assert mdl == MODELS[model]['mdl']
        v = mdl[ : mdl.index('V')]                            ;  print('v:    ' + v)
        assert v == MODELS[model]['v']
        a = mdl[mdl.index('-') + 1 : mdl.index('A')]          ;  print('a:    ' + a)
        assert a == MODELS[model]['a']
        mva = 'ZUP{}-{}'.format(v, a)                         ;  print('mva:     ' + mva)
        assert mva == MODELS[model]['mva']
        mxy = 'ZUP{}-XY'.format(v)                            ;  print('mxy:     ' + mxy)
        assert mxy == MODELS[model]['mxy']
    return None

def test__init__fails_() -> None:
    sp = serial.Serial(port='COM1', baudrate=115200, bytesize=serial.EIGHTBITS,
                       parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE,timeout=10, xonxoff=True,
                       rtscts=False, write_timeout=10, dsrdtr=False, inter_byte_timeout=None)
    assert 1 in Zup.ADDRESS_RANGE
    assert 115200 not in Zup.BAUD_RATES
    with pytest.raises(ValueError):
        z = Zup(1, sp)

    assert 9600 in Zup.BAUD_RATES
    sp.baudrate = 9600
    assert '1' not in Zup.ADDRESS_RANGE
    with pytest.raises(TypeError):
        z = Zup('1', sp)

    assert 42 not in Zup.ADDRESS_RANGE # A nod to Deep Thought...
    with pytest.raises(ValueError):
        z = Zup(42, sp)
    sp.close()
    return None

@pytest.fixture(scope='session')
def serial_port() -> serial:
    serial_port = serial.Serial(port='COM1', baudrate=9600, bytesize=serial.EIGHTBITS,
                  parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE,timeout=10, xonxoff=True,
                  rtscts=False, write_timeout=10, dsrdtr=False, inter_byte_timeout=None)
    return serial_port

@pytest.fixture(params=(1,2,3,4,5,6))
def zup_address(request):
    return request.param

@pytest.fixture
def zup(zup_address, serial_port) -> Zup:
    return Zup(zup_address, serial_port)

def test__init__passes(zup: Zup) -> None:
    assert zup.address in Zup.ADDRESS_RANGE                                 ;  print(zup.address)
    assert zup.serial_port.baudrate in Zup.BAUD_RATES                       ;  print(zup.serial_port.baudrate)
    assert zup.serial_port.port == 'COM1'                                   ;  print(zup.serial_port.port)
    assert zup.listening_addresses == {zup.serial_port.port : zup.address}  ;  print(zup.listening_addresses)
    zup._write_command(':RMT?;')
    assert zup._read_response() == 'RM2'
    zup._write_command(':MDL?;')
    mdl = zup._read_response()                                              ;  print('mdl:     ' + mdl)
    assert 'Lambda ZUP' in mdl
    mdl = mdl[mdl.index('(') + 1 : mdl.index(')')]
    v = mdl[ : mdl.index('V')]
    a = mdl[mdl.index('-') + 1 : mdl.index('A')]
    mdl = 'ZUP{}-{}'.format(v, a)
    assert zup.CUR == Zup.CURs[mdl]
    mdl = 'ZUP{}-XY'.format(v)
    assert zup.VOL == Zup.VOLs[mdl]
    assert zup.OVP == Zup.OVPs[mdl]
    assert zup.UVP == Zup.UVPs[mdl]
    return None

def test__del__(zup: Zup) -> None:
    # Confirmed Zup.__del__() did not execute when Python's garbage collector was solely depended upon.
    # Confirmed Zup.__del__() did execute when Zup objects were explicitly deleted; 'del zup'.
    zup._write_command(':RMT2;')
    zup._write_command(':RMT?;')
    assert zup._read_response() == 'RM2'
    assert zup.__del__() is None
    zup._write_command(':RMT?;')
    assert zup._read_response() == 'RM1'
    zup._write_command(':RMT2;')
    return None

def test__str__(zup: Zup) -> None:
    _str_ = zup.__str__()
    assert 'Lambda ZUP' in _str_
    zup._write_command(':MDL?;')
    assert _str_ == zup._read_response()
    return None

def test_configure(zup: Zup) -> None:
    assert zup.configure() is None
    return None

def test_set_under_voltage_protection(zup: Zup) -> None:
    with pytest.raises(TypeError):
        zup.set_under_voltage_protection('Invalid Under-Voltage')
    with pytest.raises(ValueError):
        zup.set_under_voltage_protection(zup.UVP['min'] - 1)
    print(zup.UVP['min'] - 1)
    zup._write_command(':OUT0;')
    assert zup.set_under_voltage_protection(zup.UVP['min']) is None
    zup._write_command(':UVP?;')
    up = zup._read_response()
    assert 'UP' in up                ;  print(up)
    up = up.replace('UP', '')
    up = float(up)                   ;  print(up)
    assert up == zup.UVP['min']
    return None

def test_get_under_voltage_protection(zup: Zup) -> None:
    up = zup.get_under_voltage_protection()   ;  print(up)
    assert type(up) in (int, float)
    assert (zup.UVP['min'] <= up <= zup.UVP['MAX'])
    return None

def test_set_over_voltage_protection(zup: Zup) -> None:
    with pytest.raises(TypeError):
        zup.set_over_voltage_protection('Invalid Over-Voltage')
    with pytest.raises(ValueError):
        zup.set_over_voltage_protection(zup.OVP['MAX'] + 1)
    print(zup.OVP['MAX'] + 1)
    zup._write_command(':OUT0;')
    assert zup.set_over_voltage_protection(zup.OVP['MAX']) is None
    zup._write_command(':OVP?;')
    op = zup._read_response()
    assert 'OP' in op                ;  print(op)
    op = op.replace('OP', '')
    op = float(op)                   ;  print(op)
    assert op == zup.OVP['MAX']
    return None

def test_get_over_voltage_protection(zup: Zup) -> None:
    op = zup.get_over_voltage_protection() ;  print(op)
    assert type(op) in (int, float)
    assert (zup.OVP['min'] <= op <= zup.OVP['MAX'])
    return None

def test_set_amperage(zup: Zup) -> None:
    with pytest.raises(TypeError):
        zup.set_amperage('Invalid Amperage')
    with pytest.raises(ValueError):
        zup.set_amperage(zup.CUR['MAX'] + 1)

    # Cannot test specific actual currents without also setting voltage and powering with a real load impedance.
    # So only test programmed current.
    zup._write_command(':OUT0;')
    a = zup.CUR['MAX'] / 2              ;  print(a)
    assert zup.set_amperage(a) is None
    zup._write_command(':CUR!;')
    sa = zup._read_response()           ;  print(sa)
    assert 'SA' in sa
    sa = sa.replace('SA', '')
    sa = float(sa)                      ;  print(sa)
    assert (a * 0.9 <= sa <= a * 1.1) # Allow for rounding.
    return None

def test_get_amperage_actual(zup: Zup) -> None:
    aa = zup.get_amperage_actual()      ;  print(aa)
    assert type(aa) in (int, float)
    assert (zup.CUR['min'] <= aa <= zup.CUR['MAX'])
    return None

def test_get_amperage_set(zup: Zup) -> None:
    sa = zup.get_amperage_set()         ;  print(sa)
    assert type(sa) in (int, float)
    assert (zup.CUR['min'] <= sa <= zup.CUR['MAX'])
    return None

def test_set_voltage(zup: Zup) -> None:
    with pytest.raises(TypeError):
        zup.set_voltage('Invalid Voltage')
    with pytest.raises(ValueError):
        zup.set_voltage(zup.VOL['MAX'] + 1)

    zup._write_command(':OUT1;')
    v = zup.VOL['MAX'] / 2              ;  print(v)
    assert zup.set_voltage(v) is None
    zup._write_command(':VOL!;')
    sv = zup._read_response()           ;  print(sv)
    assert 'SV' in sv
    sv = sv.replace('SV', '')
    sv = float(sv)                      ;  print(sv)
    assert (v * 0.9 <= sv <= v * 1.1) # Allow for rounding.

    zup._write_command(':VOL?;')
    av = zup._read_response()           ;  print(av)
    assert 'AV' in av
    av = av.replace('AV', '')
    av = float(av)                      ;  print(av)
    assert (v * 0.9 <= av <= v * 1.1) # Allow for rounding.
    zup._write_command(':OUT0;')
    return None

def test_get_voltage_actual(zup: Zup) -> None:
    av = zup.get_voltage_actual()       ;  print(av)
    assert type(av) in (int, float)
    assert (zup.VOL['min'] <= av <= zup.VOL['MAX'])
    return None

def test_get_voltage_set(zup: Zup) -> None:
    sv = zup.get_voltage_set()          ;  print(sv)
    assert type(sv) in (int, float)
    assert (zup.VOL['min'] <= sv <= zup.VOL['MAX'])
    return None

def test_set_power(zup: Zup) -> None:
    assert zup != None
    zup._write_command(':OUT0;')
    v = zup.VOL['Format'].format(zup.VOL['MAX'] / 2) ;  print(v)
    zup._write_command(':VOL{};'.format(v))
    assert zup.set_power('On') is None
    zup._write_command(':OUT?;')
    r = zup._read_response()                         ;  print(r)
    assert r == 'OT1'
    zup.set_power('Off')
    zup._write_command(':OUT?;')
    r = zup._read_response()                         ;  print(r)
    assert r == 'OT0'
    return None

def test_power_on(zup: Zup) -> None:
    assert type(zup.power_on()) == bool
    return None

def test_get_status(zup: Zup) -> None:
    s = zup.get_status()  ;  print(s)
    for r in ('AV','SV','AA','SA','AL','PS'):
        assert r in s
    return None

def test_get_statuses(zup: Zup) -> None:
    cmd_res = [(':MDL?;', 'Lambda ZUP'),
               (':REV?;', 'Ver'),
               (':VOL!;', 'SV'),
               (':VOL?;', 'AV'),
               (':UVP?;', 'UP'),
               (':OVP?;', 'OP'),
               (':CUR!;', 'SA'),
               (':CUR?;', 'AA'),
               (':FLD?;', 'FD'),
               (':RMT?;', 'RM'),
               (':AST?;', 'AS'),
               (':STA?;', 'OS'),
               (':STP?;', 'PS'),
               (':ALM?;', 'AL'),
               (':SRV?;', 'QV'),
               (':SRT?;', 'QT'),
               (':SRF?;', 'QF')]
    st = zup.get_statuses()  ;  print(st)
    assert type(st) == list
    for i in range(0, len(cmd_res), 1):
        assert cmd_res[i][0] == st[i][0]
        assert cmd_res[i][1] in st[i][1]
    return None

def test_issue_commands_read_responses(zup: Zup) -> None:
    r = zup.issue_commands_read_responses((':DCL;',':VOL!;',':VOL?;'))  ;  print(r)
    assert type(r) == list
    assert r[0][0] == ':DCL;'     ;    assert 'N/A' == r[0][1]
    assert r[1][0] == ':VOL!;'    ;    assert 'SV'  in r[1][1]
    assert r[2][0] == ':VOL?;'    ;    assert 'AV'  in r[2][1]
    return None

def test_set_autostart(zup: Zup) -> None:
    assert zup.set_autostart('On') is None
    zup._write_command(':AST?;')
    r = zup._read_response()            ;  print(r)
    assert r == 'AS1'
    zup.set_autostart('Off')
    zup._write_command(':AST?;')
    r = zup._read_response()            ;  print(r)
    assert r == 'AS0'
    return None

def test_autostart_on(zup: Zup) -> None:
    assert type(zup.autostart_on()) == bool
    return None

def test_set_foldback(zup: Zup) -> None:
    with pytest.raises(ValueError):
        zup.set_foldback('This is not a valid Foldback state, so should fail.')
    assert zup.set_foldback('Arm') is None
    zup._write_command(':FLD?;')
    r = zup._read_response()            ;  print(r)
    # Doesn't test 'Release' capability.
    assert r == 'FD1'
    zup.set_foldback('Cancel')
    zup._write_command(':FLD?;')
    r = zup._read_response()            ;  print(r)
    assert r== 'FD0'
    return None

def test_foldback_on(zup: Zup) -> None:
    assert type(zup.foldback_on()) == bool
    return None

def test_get_model(zup: Zup) -> None:
    r = zup.get_model()                 ;  print(r)
    assert type(r) == str
    assert 'Lambda ZUP' in r
    # 'TDK-Lambda Zup Power Supplies User Manual, IA549-04-01R' states ':MDL?;' returns 'TDK-Lambda ZUP(XXV-YYA)'.
    # - Some Zup supplies queried with ':MDL?;' return 'Nemic-Lambda ZUP(XXV-YYA)'.
    # - Hence search only for common substring 'Lambda ZUP'.
    return None

def test_get_revision(zup: Zup) -> None:
    r = zup.get_revision()              ;  print(r)
    assert type(r) == str
    assert 'Ver' in r
    # Search only for common susbstring 'Ver'; some Zups return revision '1.1', whereas IA549-04-01R documents '1.0'.
    return None

def test_clear_registers(zup: Zup) -> None:
    assert zup.clear_registers() is None
    ps = zup.get_register_program()           ;  print(ps)
    assert type(ps) == str
    assert ps == 'PS00000'
    v_over_max = zup.VOL['MAX'] + 1           ;  print(v_over_max)
    v = zup.VOL['Format'].format(v_over_max)  ;  print(v)
    zup._write_command(':VOL{};'.format(v))
    ps = zup.get_register_program()           ;  print(ps)
    assert ps == 'PS00010'
    zup.clear_registers()
    ps = zup.get_register_program()           ;  print(ps)
    assert ps == 'PS00000'

    a_over_max = zup.CUR['MAX'] + 1           ;  print(a_over_max)
    a = zup.CUR['Format'].format(a_over_max)  ;  print(a)
    zup._write_command(':CUR{};'.format(a))
    ps = zup.get_register_program()           ;  print(ps)
    assert ps == 'PS00001'
    zup.clear_registers()
    ps = zup.get_register_program()           ;  print(ps)
    assert ps == 'PS00000'
    return None

def test_get_register_alarm(zup: Zup) -> None:
    reg = zup.get_register_alarm()         ;  print(reg)
    assert type(reg) == str
    assert format_test(reg, 'AL01010', ('0','1')) is None
    return None

def test_get_register_operation(zup: Zup) -> None:
    reg = zup.get_register_operation()     ;  print(reg)
    assert type(reg) == str
    assert format_test(reg, 'OS00010000', ('0','1')) is None
    return None

def test_get_register_program(zup: Zup) -> None:
    reg = zup.get_register_program()       ;  print(reg)
    assert type(reg) == str
    assert format_test(reg, 'PS00000', ('0','1')) is None
    return None

def format_test(reg: str, reg_format: str, valid_chars: tuple) -> None:
    assert len(reg) == len(reg_format)
    assert reg[0:2] == reg_format[0:2]
    for i in range(2, len(reg_format), 1):
        assert reg[i] in valid_chars
    return None

def test_set_remote_mode(zup: Zup) -> None:
    with pytest.raises(ValueError):
        zup.set_remote_mode('This is not a valid Remote state, so should fail.')
    assert zup.set_remote_mode('Remote Unlatched') is None
    zup._write_command(':RMT?;')
    r = zup._read_response()            ;  print(r)
    assert r== 'RM1'
    zup.set_remote_mode('Remote Latched')
    zup._write_command(':RMT?;')
    r = zup._read_response()            ;  print(r)
    assert r== 'RM2'
    return None

def test_remote_latched(zup: Zup) -> None:
    assert type(zup.remote_latched()) == bool
    return None

def test_set_service_request_over_voltage(zup: Zup) -> None:
    assert zup.set_service_request_over_voltage('On') is None
    zup._write_command(':SRV?;')
    r = zup._read_response()            ;  print(r)
    assert r == 'QV1'
    zup.set_service_request_over_voltage('Off')
    zup._write_command(':SRV?;')
    r = zup._read_response()            ;  print(r)
    assert r == 'QV0'
    return None

def test_service_request_over_voltage_on(zup: Zup) -> None:
    assert type(zup.service_request_over_voltage_on()) == bool
    return None

def test_set_service_request_over_temperature(zup: Zup) -> None:
    assert zup.set_service_request_over_temperature('On') is None
    zup._write_command(':SRT?;')
    r = zup._read_response()            ;  print(r)
    assert r == 'QT1'
    zup.set_service_request_over_temperature('Off')
    zup._write_command(':SRT?;')
    r = zup._read_response()            ;  print(r)
    assert r == 'QT0'
    return None

def test_service_request_over_temperature_on(zup: Zup) -> None:
    assert type(zup.service_request_over_temperature_on()) == bool
    return None

def test_set_service_request_foldback(zup: Zup) -> None:
    assert zup.set_service_request_foldback('On') is None
    zup._write_command(':SRF?;')
    r = zup._read_response()            ;  print(r)
    assert r == 'QF1'
    zup.set_service_request_foldback('Off')
    zup._write_command(':SRF?;')
    r = zup._read_response()            ;  print(r)
    assert r == 'QF0'
    return None

def test_service_request_foldback_on(zup: Zup) -> None:
    assert type(zup.service_request_foldback_on()) == bool
    return None

def test__read_response(zup: Zup) -> None:
    if (zup.serial_port.port not in Zup.listening_addresses) or (Zup.listening_addresses[zup.serial_port.port] != zup.address):
        Zup.listening_addresses.update({zup.serial_port.port : zup.address})
        t0 = time.time()  ;  time.sleep(0.015)  ;  t_slept = time.time() - t0     ;  print(t_slept)
        assert (0.015 <= t_slept <= 0.035)
        adr = '{:0>2d}'.format(zup.address)                                       ;  print(adr)
        assert adr in ('01','02','03','04','05','06','07','08','09','10',
                       '11','12','13','14','15','16','17','18','19','20',
                       '21','22','23','24','25','26','27','28','29','30',
                       '31')
        cmd = ':ADR{};'.format(adr)                                               ;  print(cmd)
        assert cmd == ':ADR' + adr + ';'
        zup.serial_port.write(cmd.encode('utf-8'))
        t0 = time.time()  ;  time.sleep(0.035)  ;  t_slept = time.time() - t0     ;  print(t_slept)
        assert (0.035 <= t_slept <= 0.070)
    assert zup.serial_port.port in Zup.listening_addresses
    assert Zup.listening_addresses[zup.serial_port.port] == zup.address
    assert zup.serial_port.write(':MDL?;'.encode('utf-8')) == 6 # 6 = number of bytes written, from ':MDL?;'.
    t0 = time.time()  ;  time.sleep(0.020)  ;  t_slept = time.time() - t0         ;  print(t_slept)
    assert (0.020 <= t_slept <= 0.050)
    r = zup._read_response()                                                      ;  print(r)
    assert type(r) == str
    assert 'Lambda ZUP' in r
    assert '\r\n' not in r
    return None

def test__write_command(zup: Zup) -> None:
    assert zup._write_command(':MDL?;') is None
    r = zup.serial_port.readline().decode('utf-8')  ;  print(r)
    assert type(r) == str
    assert 'Lambda ZUP' in r
    assert '\r\n' in r
    return None

def test__validate_binary_state() -> None:
    state = 'oFf'
    state = Zup._validate_binary_state(state)
    assert type(state) == str
    assert state == 'Off'
    state = 'oN'
    state = Zup._validate_binary_state(state)
    assert state == 'On'
    state = 'This is not a valid binary state, so should fail.'
    with pytest.raises(ValueError):
        state = Zup._validate_binary_state(state)
    return None
