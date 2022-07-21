# Zup-Python-Library: control TDK-Lambda™ Zup™ power supplies programmatically via Python™
"TDK", "TDK-Lambda" & "Zup" are registered trademarks of the TDK Corporation.

"Python" is a registered trademark of the Python Software Foundation.

pySerial Copyrighted by Chris Liechti.

pytest Copyrighted by Holger Krekel and pytest-dev team.

ScanExpress™ & ScanExpress Runner™ are trademarks of Corelis, Inc.

Reference: Zup User Manual at https://product.tdk.com/en/system/files?file=dam/doc/product/power/switching-power/prg-power/instruction_manual/zup-user-manual.pdf

Chapter 5 is especially relevant.

- Procure & install RS-232 & RS-485 serial cables connecting your PC to your Zup power supplies.
  - RS-232 PC to Zup cable: ZUP/NC401
    - Need 1 ZUP/NC401 to connect your PC to the first Zup in your serial chain.
  - RS-485 Zup to Zup cables: ZUP/NC405
    - Need 1 each for remaining Zups in your serial chain.  For 6 Zups, will need 5 ZUP/NC405s.
- Configure your Zup supplies for serial communication.
  - Note that the Zup connected to your PC communicates via RS-232, the Zups daisy-chained to one another via RS-485.
- Install Python:  https://www.python.org/
- Install pySerial: https://pypi.org/project/pyserial/
- Install Zup.py library from this repository.
- Modify zup_example_usage.py from this repository as needed.
- For ScanExpress Runner applications, modify zup_ON.* & zup_off.* as needed.
