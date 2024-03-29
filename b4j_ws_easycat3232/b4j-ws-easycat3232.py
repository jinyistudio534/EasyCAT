
import time
from collections import deque
import json
import sys
from easycat import EasyCAT
import asyncio, websockets
import queue
#import board

easycat = EasyCAT(8,False)

Que = queue.Queue()

#toWs = bytearray(0x0 for _ in range(32))
#fromWs = bytearray(0x0 for _ in range(32))
ecSt = 0

lock = asyncio.Lock()
clients = {} #: {websocket: name}

async def ws_handler(websocket, path):
    print('New client', websocket.remote_address)
    print(' ({} existing clients)'.format(len(clients)))  
    clients[websocket] = {'transform':False, 'timing':0, 'tags':[], 'raw':bytearray(0x0 for _ in range(32))}
    
    async for message in websocket:  
        if message is None:
            item1 = clients[websocket]
            del clients[websocket]
            print('Client closed connection', item1)           
            break    

        try:
            # 解碼JSON訊息
            data = json.loads(message)
            print(f"Received: {data}")
            if "action" in data:                
                if data["action"]=="get":
                    # {'action': 'get', 'tags': ['byte31']}
                    resp = {'status':ecf,'get':{}}
                    if "tags" in data:                         
                        tags = {}
                        for tag in data['tags']:  
                            if tag.isnumeric():
                                k1=int(tag)                          
                                if k1>=0 and k1<32:
                                    tags[k1] = easycat.BufferOut[k1]
                                else:
                                    print('Index over: ',k1)
                            else:
                                print('letter invalid: ',tag)

                        resp['get'] = tags

                    resps = json.dumps(resp)
                    await websocket.send(resps)
                
                elif data["action"]=="set":
                    #  {'action': 'set', 'tags': {'1': 2}}
                    if "tags" in data: 
                        for k,v in data['tags'].items():
                            if k.isnumeric():
                                k1 = int(k)
                                if k1>=0 and k1<32:
                                    easycat.BufferIn[k1] = v
                                else:
                                    print('Index over: ',k1)    
                            else:
                                print('letter invalid: ',k1)
                       
                elif data["action"]=="list":                
                    # 在這裡進行你的處理邏輯，這裡只是簡單地回傳相同的訊息
                    resp = {"slave": "EasyCAT HAT 32*32"}           
                    # 將回應編碼為JSON並發送回客戶端
                    resps = json.dumps(resp)
                    await websocket.send(resps)

                elif data["action"]=="event":
                    # {'transform': False, 'timing': 500, 'tags': [0, 1, 2, 3, 4, 5, 6, 7]}
                    Event = clients[websocket]
                    Event['transform'] = False
                    Event['timing'] = 0
                    Event['tags'] = []
                    Event['raw'] = bytearray(0x0 for _ in range(32))

                    if "transform" in data:
                        Event['transform'] = data['transform']                 

                    if "timing" in data:
                        Event['timing'] = data['timing']
                        if Event['timing'] > 0:
                            Event['lasttime'] = time.perf_counter()
                    
                    if "tags" in data:
                        for tag in data['tags']:                           
                            Event['tags'].append(tag)

                    print('Event: ',clients[websocket])
            else:
                print("Invalid Command")    

        except json.JSONDecodeError:
            print("Invalid JSON format")

async def ws_loop(server_host="192.168.1.183",server_port=8080):
    print('WebSocket server ',end='')
    async with websockets.serve(ws_handler, server_host, server_port):
        print(f" started on ws://{server_host}:{server_port}")
        await asyncio.Future()     
                
# ---------------------------------------------------------                    
# await lock.acquire()
# try:
#   pass       
# finally:
# release the lock
#   lock.release()
async def data_loop():
    global clients
    while True:            
        if len(clients)>0:  
            try:                
                for client,_ in clients.items():                    
                    event = clients[client]                
                    if len(event)>0:
                        Transform = event['transform']
                        Timing = event['timing']                        
                        Timeup = False
                        if Timing>0:
                            Last = event['lasttime']
                            Elap = (time.perf_counter()-Last)*1000 #ms
                            if Elap >= Timing:
                                event['lasttime'] = time.perf_counter()
                                print('timeup: ',Elap)                            
                                Timeup = True

                        Tags = event['tags']                        
                        Resp = {'status':ecf,'event':{}}
                        for k in Tags:
                            k1 = int(k)
                            if Timeup:
                                 Resp['event'][k] = easycat.BufferOut[k1]
                            if Transform:
                                if event['raw'][k1] != easycat.BufferOut[k1]:
                                    Resp['event'][k1] = easycat.BufferOut[k1]

                            event['raw'][k1] = easycat.BufferOut[k1]

                        if len(Resp['event'])>0:
                            Resps = json.dumps(Resp)
                            await client.send(Resps)


            except Exception as err:
                print(f"Unexpected {err=}, {type(err)=}")
                raise


        await asyncio.sleep(0.01)    
# --------------------------------------------------------
ecf = True
def MainApplication():  
    global ecf
    # node to easycat
    #easycat.BufferIn[:] = fromWs[:]
    #toWs[:] = easycat.BufferOut[:]  
                

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

            await asyncio.sleep(0.005)
    else:  
        print('easycat init false')



# asyncio.run(run_server())

async def main():
    tasks = [easycat_loop(), ws_loop(), data_loop()]
    await asyncio.gather(*tasks)

asyncio.run(main())