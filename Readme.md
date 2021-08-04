# HP8131A device server
This device server controls most of the settings for the HP 8131A dual channel pulse generator. The server uses pyvisa as backend to handle regular GPIB connections as well as serial connections from USB-to-GPIB adapters.

## Requirements
* pyvisa

## Configuration
* visa_resource: pyvisa resource name. Examples: "ASRL/dev/ttyUSB0::INSTR" for a serial device on /dev/ttyUSB0; "GPIB::6::INSTR" for a GPIB instrument at address 6. See pyvisa documentation (https://pyvisa.readthedocs.io/en/latest/introduction/names.html).

## Authors
Michael Schneider
