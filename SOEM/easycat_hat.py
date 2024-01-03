import pysoem
import time
import ctypes
import threading
from stopwatch import Stopwatch

easycat = None

class OutputPdo(ctypes.Structure):
    _pack_ = 1
    _fields_ =[        
        ('Byte0',ctypes.c_uint8),
        ('Byte1',ctypes.c_uint8),
        ('Byte2',ctypes.c_uint8),
        ('Byte3',ctypes.c_uint8),
        ('Byte4',ctypes.c_uint8),
        ('Byte5',ctypes.c_uint8),
        ('Byte6',ctypes.c_uint8),
        ('Byte7',ctypes.c_uint8),
        ('Byte8',ctypes.c_uint8),
        ('Byte9',ctypes.c_uint8),
        ('Byte10',ctypes.c_uint8),
        ('Byte11',ctypes.c_uint8),
        ('Byte12',ctypes.c_uint8),
        ('Byte13',ctypes.c_uint8),
        ('Byte14',ctypes.c_uint8),
        ('Byte15',ctypes.c_uint8),
        ('Byte16',ctypes.c_uint8),
        ('Byte17',ctypes.c_uint8),
        ('Byte18',ctypes.c_uint8),
        ('Byte19',ctypes.c_uint8),
        ('Byte20',ctypes.c_uint8),
        ('Byte21',ctypes.c_uint8),
        ('Byte22',ctypes.c_uint8),
        ('Byte23',ctypes.c_uint8),
        ('Byte24',ctypes.c_uint8),
        ('Byte25',ctypes.c_uint8),
        ('Byte26',ctypes.c_uint8),
        ('Byte27',ctypes.c_uint8),
        ('Byte28',ctypes.c_uint8),
        ('Byte29',ctypes.c_uint8),
        ('Byte30',ctypes.c_uint8),
        ('Byte31',ctypes.c_uint8)
        
    ]

class InputPdo(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ('Byte0',ctypes.c_uint8),
        ('Byte1',ctypes.c_uint8),
        ('Byte2',ctypes.c_uint8),
        ('Byte3',ctypes.c_uint8),
        ('Byte4',ctypes.c_uint8),
        ('Byte5',ctypes.c_uint8),
        ('Byte6',ctypes.c_uint8),
        ('Byte7',ctypes.c_uint8),
        ('Byte8',ctypes.c_uint8),
        ('Byte9',ctypes.c_uint8),
        ('Byte10',ctypes.c_uint8),
        ('Byte11',ctypes.c_uint8),
        ('Byte12',ctypes.c_uint8),
        ('Byte13',ctypes.c_uint8),
        ('Byte14',ctypes.c_uint8),
        ('Byte15',ctypes.c_uint8),
        ('Byte16',ctypes.c_uint8),
        ('Byte17',ctypes.c_uint8),
        ('Byte18',ctypes.c_uint8),
        ('Byte19',ctypes.c_uint8),
        ('Byte20',ctypes.c_uint8),
        ('Byte21',ctypes.c_uint8),
        ('Byte22',ctypes.c_uint8),
        ('Byte23',ctypes.c_uint8),
        ('Byte24',ctypes.c_uint8),
        ('Byte25',ctypes.c_uint8),
        ('Byte26',ctypes.c_uint8),
        ('Byte27',ctypes.c_uint8),
        ('Byte28',ctypes.c_uint8),
        ('Byte29',ctypes.c_uint8),
        ('Byte30',ctypes.c_uint8),
        ('Byte31',ctypes.c_uint8)
    ]

def convert_input_data(data):
    return InputPdo.from_buffer_copy(data)

# I use this config function
def peasycat_config_func(slave_pos):
    global easycat
    # all default config

def main():
    global easycat

    master = pysoem.Master()
    # master.open('\\Device\\NPF_{A49DCDDE-F083-4985-A824-45BFBE483E3C}') 
    master.open('eth0')
    time.sleep(1) 
    if master.config_init() > 0:
        for i, slave in enumerate(master.slaves):
            print("{} ({}) {}".format(slave.man,f'0x{slave.id:X}', slave.name))

        easycat = master.slaves[0]
        
        easycat.config_func = peasycat_config_func
        master.config_map()
        if master.state_check(pysoem.SAFEOP_STATE, 50_000) == pysoem.SAFEOP_STATE:
            master.state = pysoem.OP_STATE
            
            master.send_processdata()
            master.receive_processdata(1_000)
            
            master.write_state()
            master.state_check(pysoem.OP_STATE, 5_000_000)
            if master.state == pysoem.OP_STATE:
                print('IN OP STATE')
                stopwatch = Stopwatch(0.5)
                stopwatch.reset()

                output_data = OutputPdo()              
                easycat.output = bytes(output_data)                    
                try:
                    while 1:                      
                        easycat.output = bytes(output_data)
                        master.send_processdata()
                        master.receive_processdata(1_000)
                        input_data = convert_input_data(easycat.input)
                        if stopwatch.duration:
                            output_data.Byte0 = output_data.Byte0 + 1
                            if output_data.Byte0>100:
                                output_data.Byte0=0
                            stopwatch.reset()

                        print('Input :', input_data.Byte0, input_data.Byte1, input_data.Byte2, input_data.Byte3, input_data.Byte4, input_data.Byte5,' Output:', output_data.Byte0, output_data.Byte1, output_data.Byte2, output_data.Byte3, output_data.Byte4, output_data.Byte5)
                        time.sleep(0.01)
                except KeyboardInterrupt:
                    print('stopped')
                # zero everything
                easycat.output = bytes(len(easycat.output))
                master.send_processdata()
                master.receive_processdata(1_000)
            else:
                print('al status code {} ({})'.format(hex(easycat.al_status), pysoem.al_status_code_to_string(easycat.al_status)))
                print('failed to got to op state')
        else:
            print('failed to got to safeop state')
        master.state = pysoem.PREOP_STATE
        master.write_state()
    else:
        print('no device found')
    master.close()


if __name__ == '__main__':
    main()
