import easycat

easycat = EasyCAT()

n0 = bytearray(0x0 for _ in range(BYTE_NUM))

def MainApplication():  
  global n0
  
  
  for i in range(32):   
    n1 = easycat.BufferOut.Byte[i]
    if n0[i] != n1:
      n0[i] = n1
      print("fill in [{}] = {}".format(i,n1))    

    easycat.BufferIn.Byte[i] = n1
    #print("In:{} Out:{}".format(easycat.BufferIn.Byte[i], easycat.BufferOut.Byte[i]))

if easycat.Init():
  _ope = 0
  _watch = 0
  while True:
    st = easycat.MainTask()    
    if _watch != st:
      _watch = st
      if st & 0x80:        
        print("Watchdog")
      else:
        print("Not Watchdog")

    if _ope != easycat.Operational:
      _ope = easycat.Operational
      if _ope:
        print("Operational")       
      else:
        print("Not Operational")

    if easycat.Operational:
       MainApplication()

    utime.sleep_ms(10)
else:
  print('init false')