import time
from collections import deque
import json
import sys
import asyncio
import queue
from ebpfcat.ebpfcat import FastEtherCat, SyncGroup
from ebpfcat.devices import DigitalInput, DigitalOutput, AnalogInput, AnalogOutput
from ebpfcat.terminals import EK1100
from ebpfcat.terminals import EL1088
from ebpfcat.terminals import EL2088
import random
import zmq
import zmq.asyncio
from zmq.asyncio import Context

#import board
slot = {1:[False]*8, 2:[False]*8, 3:[False]*8, 4:[False]*8, 5:{0:[0]*32, 1:[0]*32}}
raw = {1:[False]*8, 2:[False]*8, 3:[False]*8, 4:[False]*8, 5:{0:[0]*32, 1:[0]*32}}

def getSlotsize(tag):
    if tag in (1,2,3,4):
        return len(slot[tag])
    else :
        return len(slot[tag][0])

def setOutput(tag,index,value):
    if tag in (3,4):
        slot[tag][index] = value
    else :
        slot[tag][0][index] = value

def getOutput(tag,index):
    if tag in (3,4):
        return slot[tag][index]
    else :
        return slot[tag][0][index]

def getInput(tag,index):
    if tag in (1,2,3,4):
        return slot[tag][index]
    else :
        slot[tag][1][index]

Que = queue.Queue()
plc_wait = True

#toWs = bytearray(0x0 for _ in range(32))
#fromWs = bytearray(0x0 for _ in range(32))
ecSt = 0
lock = asyncio.Lock()         
# ---------------------------------------------------------                   
async def ebpfcat_loop():   
    try:
        master = FastEtherCat("eth0")
        await master.connect()
        print("Number of terminals:", await master.count())    

        in1 = EL1088(master)   
        await in1.initialize(-1, 1)        

        in2 = EL1088(master)   
        await in2.initialize(-2, 2)

        out1 = EL2088(master)   
        await out1.initialize(-3, 3)

        out2 = EL2088(master)   
        await out2.initialize(-4, 4)

       

        di1 = []*8
        di1.append(DigitalInput(in1.channel1))  
        di1.append(DigitalInput(in1.channel2)) 
        di1.append(DigitalInput(in1.channel3)) 
        di1.append(DigitalInput(in1.channel4)) 
        di1.append(DigitalInput(in1.channel5)) 
        di1.append(DigitalInput(in1.channel6)) 
        di1.append(DigitalInput(in1.channel7)) 
        di1.append(DigitalInput(in1.channel8)) 

        di2 = []*8
        di2.append(DigitalInput(in2.channel1))  
        di2.append(DigitalInput(in2.channel2)) 
        di2.append(DigitalInput(in2.channel3)) 
        di2.append(DigitalInput(in2.channel4)) 
        di2.append(DigitalInput(in2.channel5)) 
        di2.append(DigitalInput(in2.channel6)) 
        di2.append(DigitalInput(in2.channel7)) 
        di2.append(DigitalInput(in2.channel8)) 

        do1 = []*8
        do1.append(DigitalOutput(out1.channel1))  # use channel 1 of terminal "out"
        do1.append(DigitalOutput(out1.channel2))  # use channel 1 of terminal "out"
        do1.append(DigitalOutput(out1.channel3))  # use channel 1 of terminal "out"
        do1.append(DigitalOutput(out1.channel4))  # use channel 1 of terminal "out"
        do1.append(DigitalOutput(out1.channel5))  # use channel 1 of terminal "out"
        do1.append(DigitalOutput(out1.channel6))  # use channel 1 of terminal "out"
        do1.append(DigitalOutput(out1.channel7))  # use channel 1 of terminal "out"
        do1.append(DigitalOutput(out1.channel8))  # use channel 1 of terminal "out"

        do2 = []*8
        do2.append(DigitalOutput(out2.channel1))  # use channel 1 of terminal "out"
        do2.append(DigitalOutput(out2.channel2))  # use channel 1 of terminal "out"
        do2.append(DigitalOutput(out2.channel3))  # use channel 1 of terminal "out"
        do2.append(DigitalOutput(out2.channel4))  # use channel 1 of terminal "out"
        do2.append(DigitalOutput(out2.channel5))  # use channel 1 of terminal "out"
        do2.append(DigitalOutput(out2.channel6))  # use channel 1 of terminal "out"
        do2.append(DigitalOutput(out2.channel7))  # use channel 1 of terminal "out"
        do2.append(DigitalOutput(out2.channel8))  # use channel 1 of terminal "out"

       

        
        sg = SyncGroup(master, [di1[0],di1[1],di1[2],di1[3],di1[4],di1[5],di1[6],di1[7],\
            di2[0],di2[1],di2[2],di2[3],di2[4],di2[5],di2[6],di2[7],\
            do1[0],do1[1],do1[2],do1[3],do1[4],do1[5],do1[6],do1[7],\
            do2[0],do2[1],do2[2],do2[3],do2[4],do2[5],do2[6],do2[7]          
            
            ])  # this sync group only contains one terminal
        task = sg.start()  # start operating the terminals
        plc_wait = False
        while True: #for i in range(5000):
            # we would measure an increasing value on the terminal output         
            for i in range(8):
                slot[1][i] = di1[i].value
                slot[2][i] = di2[i].value

                do1[i].value = slot[3][i]
                do2[i].value = slot[4][i]

            
            await asyncio.sleep(0.001)

    except EtherCatError:
        print('EtherCAT Exception')        


    task.cancel()  # stop the sync group
# --------------------------------------------------------
async def plc_loop():   
    while plc_wait:        
        await asyncio.sleep(0.1)
    print('plc is running ...')

    while True:       
        await asyncio.sleep(0.001)
        
# --------------------------------------------------------
urlp = f"tcp://192.168.1.181:5550"
# pub/sub and dealer/router
ctx = Context.instance()

async def pub_loop() -> None:
    pub = ctx.socket(zmq.PUB)
    pub.bind(urlp)
     # give time to subscribers to initialize; wait time >.2 sec
    await asyncio.sleep(0.5)
    print("Waiting so subscriber sockets can connect...")   
    # send setup connection message
    # await pub.send_multipart([b'world', "init".encode('utf-8')])
    # await pub.send_json([b'world', "init".encode('utf-8')])

    # without try statement, no error output
    try:
        # keep sending messages      
        while True:
            try:                
                msg = {}
                for i in range(8):
                    if raw[1][i]!=slot[1][i]:
                        msg[i] = slot[1][i]
                    raw[1][i] = slot[1][i]
                if len(msg)>0:
                    topic = 'S1'
                    msg_body = json.dumps(msg)
                    #print(f"   Topic: {topic}, msg:{msg_body}")          
                    await pub.send_multipart([topic.encode('utf8'), msg_body.encode("utf8")])
                    await asyncio.sleep(0.001)     

                msg1={}
                for i in range(8):
                    if raw[2][i]!=slot[2][i]:
                        msg1[i] = slot[2][i]
                    raw[2][i] = slot[2][i]

                if len(msg1)>0:
                    topic = 'S2'
                    msg_body = json.dumps(msg1)
                    #print(f"   Topic: {topic}, msg:{msg_body}")          
                    await pub.send_multipart([topic.encode('utf8'), msg_body.encode("utf8")])
                    await asyncio.sleep(0.001)  
                   
                await asyncio.sleep(0.001)       
            except KeyboardInterrupt:
                pass

    except Exception as e:
        print("Error with pub")
        print(e)
       

    finally:
        # TODO disconnect pub/sub
        pass

# processes message topic 'world'; "Hello World" or "Hello Sekai"
urls = f"tcp://192.168.1.181:5551"
async def sub_loop() -> None:   
    # setup subscriber
    sub = ctx.socket(zmq.SUB)
    sub.bind(urls)
    sub.setsockopt(zmq.SUBSCRIBE,b'')  

    # without try statement, no error output
    try:
        print("sub initialized")
        # keep listening to all published message on topic 'world'
        while True:
            [topic, msg] = await sub.recv_multipart()
            s1 = topic.decode().replace('S','') 
            #print(f"topic: {topic.decode()}\tmessage: {msg.decode()}")
            # process message
            if(s1.isnumeric()):
                n1 = int(s1)
                if(n1 in (3,4)):                  
                    v1 = json.loads(msg.decode())  
                    for k, v in v1.items():   
                        slot[n1][int(k)] = v
            
            #print('')

            #obj.msg_sub(msg.decode('utf-8'))

            # await asyncio.sleep(.2)

            # publish message to topic 'sekai'
            # async always needs `send_multipart()`
            # await pub.send_multipart([b'sekai', msg_publish.encode('ascii')])

    except Exception as e:
        print("Error with sub, {e}")        

    finally:
        # TODO disconnect pub/sub
        pass
# --------------------------------------------------------
async def main():
    tasks = [ebpfcat_loop(),plc_loop(),pub_loop(),sub_loop()]
    await asyncio.gather(*tasks)

asyncio.run(main())
