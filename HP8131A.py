#!/usr/bin/env python3

import tango
from tango import AttrWriteType, DevState, DispLevel
from tango.server import Device, attribute, command, device_property

import pyvisa, time
from enum import IntEnum


class TriggerMode(IntEnum):
    AUTO = 0
    TRIGGER = 1
    GATE = 2
    BURST = 3
    EWIDTH = 4
    TRANSDUCER = 5

class TriggerSlope(IntEnum):
    POSITIVE = 0
    NEGATIVE = 1

attr2gpib = dict(
    trigger_mode=':INP:TRIG:MODE',
    trigger_slope=':INP:TRIG:SLOP',
    trigger_level=':INP:TRIG:THR',
    trigger_external=':INP:TRIG:STAT',
    period=':PULS:TIM:PER',
    width1=':PULS1:TIM:WIDT',
    delay1=':PULS1:TIM:DEL',
    low1=':PULS1:LEVEL:LOW',
    high1=':PULS1:LEVEL:HIGH',
    enabled1=':OUTP1:PULS:STAT',
    cenabled1=':OUTP1:PULS:CST',
    width2=':PULS2:TIM:WIDT',
    delay2=':PULS2:TIM:DEL',
    low2=':PULS2:LEVEL:LOW',
    high2=':PULS2:LEVEL:HIGH',
    enabled2=':OUTP2:PULS:STAT',
    cenabled2=':OUTP2:PULS:CST',
)

gpib2attr = {v: k for k, v in attr2gpib.items()}

class HP8131A(Device):
    '''HP8131A

    This controls most settings on a HP8131A pulse generator using pyvisa.
    Works transparently for regular GPIB connections as well as for USB-GPIB
    adapters that expose the GPIB interface as a serial device.
    '''
    visa_resource = device_property(
        dtype=str,
        default_value='ASRL/dev/ttyUSB0::INSTR',
        doc=('pyvisa resource name. Examples: "ASRL/dev/ttyUSB0::INSTR" '
             'for a serial device on /dev/ttyUSB0; "GPIB::6::INSTR" for an '
             'GPIB instrument at address 6. See pyvisa documentation.')
    )

    period = attribute(
        label='period',
        dtype=float,
        access=AttrWriteType.READ_WRITE,
        unit='s', min_value=2e-9, max_value=99.9e-3,
        format='8.3e',
        fget='read_general',
    )

    low1 = attribute(
        label='ch1_low',
        dtype=float,
        access=AttrWriteType.READ_WRITE,
        unit='V', min_value=-5, max_value=4.9,
        fget='read_general',
    )

    high1 = attribute(
        label='ch1_high',
        dtype=float,
        access=AttrWriteType.READ_WRITE,
        unit='V', min_value=-4.9, max_value=5,
        fget='read_general',
    )

    delay1 = attribute(
        label='ch1_delay',
        dtype=float,
        access=AttrWriteType.READ_WRITE,
        unit='s', min_value=0, max_value=99.9e-3,
        format='8.3e',
        fget='read_general',
    )

    width1 = attribute(
        label='ch1_width',
        dtype=float,
        access=AttrWriteType.READ_WRITE,
        unit='s', min_value=0.5e-9, max_value=99.9e-3,
        format='8.3e',
        fget='read_general',
    )

    enabled1 = attribute(
        label='ch1_enabled',
        dtype=bool,
        access=AttrWriteType.READ_WRITE,
        fget='read_general',
    )
    
    cenabled1 = attribute(
        label='ch1_comp_enabled',
        dtype=bool,
        access=AttrWriteType.READ_WRITE,
        fget='read_general',
    )

    low2 = attribute(
        label='ch2_low',
        dtype=float,
        access=AttrWriteType.READ_WRITE,
        unit='V', min_value=-5, max_value=4.9,
        fget='read_general',
    )
    
    high2 = attribute(
        label='ch2_high',
        dtype=float,
        access=AttrWriteType.READ_WRITE,
        unit='V', min_value=-4.9, max_value=5,
        fget='read_general',
    )
    
    delay2 = attribute(
        label='ch2_delay',
        dtype=float,
        access=AttrWriteType.READ_WRITE,
        unit='s', min_value=0, max_value=99.9e-3,
        format='8.3e',
        fget='read_general',
    )

    width2 = attribute(
        label='ch2_width',
        dtype=float,
        access=AttrWriteType.READ_WRITE,
        unit='s', min_value=0.5e-9, max_value=99.9e-3,
        format='8.3e',
        fget='read_general',
    )

    enabled2 = attribute(
        label='ch2_enabled',
        dtype=bool,
        access=AttrWriteType.READ_WRITE,
        fget='read_general',
    )
    
    cenabled2 = attribute(
        label='ch2_comp_enabled',
        dtype=bool,
        access=AttrWriteType.READ_WRITE,
        fget='read_general',
    )

    trigger_mode = attribute(
        label='trigger',
        dtype=TriggerMode,
        access=AttrWriteType.READ_WRITE,
        fget='read_general',
    )

    trigger_slope = attribute(
        label='tigger_slope',
        dtype=TriggerSlope,
        access=AttrWriteType.READ_WRITE,
        fget='read_general',
    )

    trigger_external = attribute(
        label='tigger_external',
        dtype=bool,
        access=AttrWriteType.READ_WRITE,
        fget='read_general',
    )

    trigger_level = attribute(
        label='trigger_level',
        dtype=float,
        access=AttrWriteType.READ_WRITE,
        unit='V', min_value=-5, max_value=5,
        fget='read_general',
    )
    

    def init_device(self):
        super(HP8131A, self).init_device()
        try:
            self.info_stream(f'Trying to connect to HP8131A on {self.port}')
            self.rm = pyvisa.ResourceManager('@py')
            self.dev = self.rm.open_resource(self.visa_resource)
            self.dev.read_termination = '\n'
            self.dev.write_termination = '\n'
            idn = self.write_read('*IDN?')
            self.info_stream(f'Connection established on {self.port}:\n{idn}')
            self.set_state(DevState.ON)
        except Exception as ex:
            self.error_stream(f'Error on initialization: {ex}')
            self.set_state(DevState.OFF)
        

    @command(dtype_in=str, doc_in='command', dtype_out=str, doc_out='response')
    def write_read(self, msg: str) -> str:
        ans = self.dev.query(msg)
        self.debug_stream(ans)
        return ans
    
    @command(dtype_in=str, doc_in='command', dtype_out=None)
    def write(self, msg: str):
        self.debug_stream(msg)
        self.dev.write(msg)

    def read_general(self, attr):
        name = attr.get_name()
        cmd = attr2gpib[name] + '?'
        ans = self.write_read(cmd)
        if name in ['enabled1', 'cenabled1', 'enabled2', 'cenabled2']:
            value = True if ans == 'ON' else False
        elif name == 'trigger_mode':
            value = TriggerMode[ans]
        elif name == 'trigger_slope':
            value = TriggerSlope[ans]
        else:
            value = float(ans)
        self.debug_stream(f'READ: {name} = {value}')
        attr.set_value(value)
        return value
    
    def write_period(self, value):
        cmd = f'{attr2gpib["period"]} {value}'
        self.write(cmd)
    
    def write_low1(self, value):
        cmd = f'{attr2gpib["low1"]} {value}'
        self.write(cmd)
    
    def write_high1(self, value):
        cmd = f'{attr2gpib["high1"]} {value}'
        self.write(cmd)
    
    def write_delay1(self, value):
        cmd = f'{attr2gpib["delay1"]} {value}'
        self.write(cmd)
    
    def write_width1(self, value):
        cmd = f'{attr2gpib["width1"]} {value}'
        self.write(cmd)
    
    def write_enabled1(self, value):
        cmd = f'{attr2gpib["enabled1"]} {int(value)}'
        self.write(cmd)
    
    def write_cenabled1(self, value):
        cmd = f'{attr2gpib["cenabled1"]} {int(value)}'
        self.write(cmd)
    
    def write_low2(self, value):
        cmd = f'{attr2gpib["low2"]} {value}'
        self.write(cmd)
    
    def write_high2(self, value):
        cmd = f'{attr2gpib["high2"]} {value}'
        self.write(cmd)
    
    def write_delay2(self, value):
        cmd = f'{attr2gpib["delay2"]} {value}'
        self.write(cmd)
    
    def write_width2(self, value):
        cmd = f'{attr2gpib["width2"]} {value}'
        self.write(cmd)
    
    def write_enabled2(self, value):
        cmd = f'{attr2gpib["enabled2"]} {int(value)}'
        self.write(cmd)

    def write_cenabled2(self, value):
        cmd = f'{attr2gpib["cenabled2"]} {int(value)}'
        self.write(cmd)
    
    def write_trigger_level(self, value):
        cmd = f'{attr2gpib["trigger_level"]} {value}'
        self.write(cmd)
    
    def write_trigger_mode(self, value):
        val_str = TriggerMode(value).name
        cmd = f'{attr2gpib["trigger_mode"]} {val_str}'
        self.write(cmd)
    
    def write_trigger_slope(self, value):
        val_str = TriggerSlope(value).name
        cmd = f'{attr2gpib["trigger_slope"]} {val_str}'
        self.write(cmd)
    
    def write_trigger_external(self, value):
        cmd = f'{attr2gpib["trigger_external"]} {int(value)}'
        self.write(cmd)
    
    def delete_device(self):
        self.dev.close()
        self.set_state(DevState.OFF)
        self.info_stream('HP8131A device server closed')

    @command(doc='Simulate single trigger event')
    def manual_trigger(self):
        self.write('*TRG')

    @command
    def selftest(self):
        ans = self.write_read('*TST?')
        if ans == '0':
            self.set_state(DevState.ON)
        else:
            self.set_state(DevState.FAULT)


# start the server
if __name__ == "__main__":
    HP8131A.run_server()
