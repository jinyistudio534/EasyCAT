import time
from collections import deque
import json
import sys
from easycat import EasyCAT
import asyncio, aioudp
import board

easycat = EasyCAT(8,False)

toNode = bytearray(0x0 for _ in range(32))
frNode = bytearray(0x0 for _ in range(32))

toNx = False
frNx = False
ecSt = 0

iQ = []
oQ = []

async def ipc_loop():       
    async def handler(connection):
        async for message in connection:               
            n1 = len(message)
            if n1>0:
                #print(message)
                js = str(message, encoding='ascii')
                if js != 'trash':
                    jg = json.loads(js)  
                    iQ.append(jg)
                else:
                    print('trash')

    async with aioudp.serve("0.0.0.0", 8888, handler):
        #await asyncio.Future()               
        async with aioudp.connect("0.0.0.0", 8889) as connection:            
            print('connect')         
            while True:
                try:
                    l1 = len(oQ)
                    if l1>0:
                        jpb = oQ[0]
                        del oQ[0]
                        # print('send.',l1,jpb)
                        await connection.send(jpb)                                                     

                    await asyncio.sleep(0.05)
                except KeyboardInterrupt:
                    # Ctrl-C to abort handling
                    print('ipc_Loop abort')
# ---------------------------------------------------------                    
async def pdo_loop():
    global frNode,frNx
    global toNode,toNx   
    while True:
        # Slave.input from Node-red ===
        if len(iQ)>0:
            # self._master.slaves[1].output = struct.pack('8h', 0x0CCD, 0x1999, 0x2666, 0x3332, 0x0CCD, 0x1999, 0x2666, 0x3332)
            jg = iQ[0]
            del iQ[0]

            if 'payload' in jg:                        
                _payload = jg.get('payload')
                j = 0
                for i in range(0, len(_payload), 2):
                    frNode[j] = int(_payload[i:i + 2],16)       
                    j+=1
                

                  
        # Slave.output to Node-RED =====
        if toNx:
            jgs = {"id":0,"status":ecSt,"payload":toNode.hex()}  
            jb =  bytes(json.dumps(jgs), 'ascii')
            #print(jb)
            oQ.append(jb)    
            toNx = False

        await asyncio.sleep(0.010)    
# --------------------------------------------------------
ecf = True
st = time.time()
def MainApplication():  
    global ecf,toNx,frNx,toNode,frNode,st    
    # node to easycat
    easycat.BufferIn[:] = frNode[:]
           
    # easycat to node
    b1 = False
    for i in range(32):
        if toNode[i] != easycat.BufferOut[i]:   
            #print('{}[{}] x {}[{}]'.format(txBuff[j],j,easycat.BufferOut[i],i))            
            b1 = True                                 
        toNode[i] = easycat.BufferOut[i]

    if b1:      
        st = time.time()
        print('XXX')  
        ecf = False
        toNx = True
    else:
        if ecf==False:
            if (time.time()-st)>=3:
                st = time.time()
                toNx = True
                

    #print("In:{} Out:{}".format(easycat.BufferIn.Byte[i], easycat.BufferOut.Byte[i]))


async def easycat_loop():
    global ecSt
    n0 = 0
    if easycat.Init():
        _ope = 0
        _watch = 0
        while True:
            st = easycat.MainTask()    
            if _watch != st:
                _watch = st
                if st & 0x80:        
                    print("Watchdog")
                    esSt = ecSt | 0x01
                else:
                    print("Not Watchdog")
                    esSt = ecSt & 0xfe

            if _ope != easycat.Operational:
                _ope = easycat.Operational
                if _ope:
                    print("Operational")   
                    ecSt = ecSt | 0x02    
                else:
                    print("Not Operational")
                    esSt = ecSt & 0xfd

            MainApplication()

            await asyncio.sleep(0.010)
    else:  
        print('easycat init false')



# asyncio.run(run_server())

async def main():
    tasks = [easycat_loop(), ipc_loop(), pdo_loop()]
    await asyncio.gather(*tasks)

asyncio.run(main())