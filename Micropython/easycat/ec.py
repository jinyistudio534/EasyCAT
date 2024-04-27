from micropython import const
from machine import SPI, Pin
import utime
import uctypes

DEB                     = const(True)        # debug

ECAT_CSR_DATA           = const(0x0300)      # EtherCAT CSR Interface Data Register
ECAT_CSR_CMD            = const(0x0304)      # EtherCAT CSR Interface Command Register

                        #---- access to EtherCAT process RAM ----------------- 

ECAT_PRAM_RD_ADDR_LEN   = const(0x0308)      # EtherCAT Process RAM Read Address and Length Register
ECAT_PRAM_RD_CMD        = const(0x030C)      # EtherCAT Process RAM Read Command Register
ECAT_PRAM_WR_ADDR_LEN   = const(0x0310)      # EtherCAT Process RAM Write Address and Length Register 
ECAT_PRAM_WR_CMD        = const(0x0314)      # EtherCAT Process RAM Write Command Register

ECAT_PRAM_RD_DATA       = const(0x0000)      # EtherCAT Process RAM Read Data FIFO
ECAT_PRAM_WR_DATA       = const(0x0020)       # EtherCAT Process RAM Write Data FIFO

                        #---- EtherCAT registers -----------------------------

AL_CONTROL              = const(0x0120)      # AL control                                             
AL_STATUS               = const(0x0130)      # AL status
AL_STATUS_CODE          = const(0x0134)      # AL status code
AL_EVENT                = const(0x0220)      # AL event request
AL_EVENT_MASK           = const(0x0204)      # AL event interrupt mask

WDOG_STATUS             = const(0x0440)      # watch dog status

SM0_BASE                = const(0x0800)      # SM0 base address (output)
SM1_BASE                = const(0x0808)      # SM1 base address (input) 

                        #---- LAN9252 registers ------------------------------    

HW_CFG                  = const(0x0074)      # hardware configuration register
BYTE_TEST               = const(0x0064)      # byte order test register
RESET_CTL               = const(0x01F8)      # reset register       
ID_REV                  = const(0x0050)      # chip ID and revision
IRQ_CFG                 = const(0x0054)      # interrupt configuration
INT_EN                  = const(0x005C)      # interrupt enable

                        #---- LAN9252 flags ------------------------------------------------------------------------------

ECAT_CSR_BUSY           =const(0x80)
PRAM_ABORT              =const(0x40000000)
PRAM_BUSY               =const(0x80)
PRAM_AVAIL              =const(0x01)
READY                   =const(0x08)
DIGITAL_RST             =const(0x00000001)

                        #---- EtherCAT flags -----------------------------------------------------------------------------

ALEVENT_CONTROL         =const(0x0001)
ALEVENT_SM              =const(0x0010) 
 
                        #----- state machine ------------------------------------------------------------

ESM_INIT                =const(0x01)          # state machine control
ESM_PREOP               =const(0x02)          # (state request)
ESM_BOOT                =const(0x03)          # 
ESM_SAFEOP              =const(0x04)          # safe-operational
ESM_OP                  =const(0x08)          # operational    
    
                        #--- ESC commands --------------------------------------------------------------------------------

ESC_WRITE 		  = const(0x80)
ESC_READ 		    = const(0xC0)


#---- SPI ----------------------------------------------------------------------------------------

COMM_SPI_READ   = const(0x03)
COMM_SPI_WRITE  = const(0x02)

DUMMY_BYTE      = const(0xFF)

SPISPEED        = const(12000000)

ASYNC           = const(0)
DC_SYNC         = const(1)
SM_SYNC         = const(2)

BYTE_NUM                = const(32)
TOT_BYTE_NUM_OUT        = BYTE_NUM
FST_BYTE_NUM_OUT        = TOT_BYTE_NUM_OUT 
FST_BYTE_NUM_ROUND_OUT  = FST_BYTE_NUM_OUT
SEC_BYTE_NUM_OUT        = const(0)
SEC_BYTE_NUM_ROUND_OUT  = const(0) 

TOT_BYTE_NUM_IN         = BYTE_NUM
FST_BYTE_NUM_IN         = TOT_BYTE_NUM_IN 
FST_BYTE_NUM_ROUND_IN   = FST_BYTE_NUM_IN
SEC_BYTE_NUM_IN         = const(0)                        
SEC_BYTE_NUM_ROUND_IN   = const(0)

UWORD = {
    "Byte": (0 | uctypes.ARRAY, 2 | uctypes.UINT8),
    "Word": 0 | uctypes.UINT16
}

ULONG = {
    "Byte": (0 | uctypes.ARRAY, 4 | uctypes.UINT8),
    "Long": 0 | uctypes.UINT32
}



PROCBUFFER_OUT = {								            #-- output buffer -----------------
    "Byte": (0 | uctypes.ARRAY, BYTE_NUM | uctypes.UINT8)    
}						             
                                            
PROCBUFFER_IN = {                                          #-- input buffer ------------------
  "Byte": (0 | uctypes.ARRAY, BYTE_NUM | uctypes.UINT8)    
}	      

class EasyCAT():            
    # EtherCAT slave for HAT.        
    def __init__(self,Spi=0, Cs=5, Sck=2, Mosi=3, Miso=4, speed=12000000):   
        #111
        self.Operational = 0          
        self.__cs = Pin(Cs, mode=Pin.OUT)             
        # -----------------------------------------------
        # SB / Pico HAT Expansion      
        # -----------------------------------------------
        #SPI.setCS(5);
        #SPI.setSCK(2);
        #SPI.setRX(4) / Miso;
        #SPI.setTX(3) / Mosi;  
        # ------------------------------------------------      
        # Waveshare / GPIO Expander For Raspberry Pi Pico 
        # ------------------------------------------------     
        #SPI.setCS(8);
        #SPI.setSCK(10);
        #SPI.setRX(12) / Miso;
        #SPI.setTX(11) / Mosi; 
        self.__spi = SPI(Spi, baudrate=speed, sck=Pin(Sck), mosi=Pin(Mosi), miso=Pin(Miso), firstbit = SPI.MSB)   
        self.Sync_ = ASYNC   
         # output process data buffer 
        self.obuf = bytearray(0x0 for _ in range(BYTE_NUM))        
        self.BufferOut = uctypes.struct(uctypes.addressof(self.obuf), PROCBUFFER_OUT, uctypes.NATIVE)

        # input process data buffer
        self.ibuf = bytearray(0x0 for _ in range(BYTE_NUM))
        self.BufferIn = uctypes.struct(uctypes.addressof(self.ibuf), PROCBUFFER_IN, uctypes.NATIVE)

    def SCS_Low_macro (self):
      self.__cs.low()

    def SCS_High_macro (self):
      self.__cs.high() 

    def SPI_TransferTxLast (self, data):      
      self.__spi.write(bytes([data]))

    def SPI_TransferTx (self, data):     
      self.__spi.write(bytes([data]))

    def SPI_TransferRx (self, data):
      return self.__spi.read(1,data)[0]

    #---- read a directly addressable registers  -----------------------------------------------------

    def SPIReadRegisterDirect (self, Address, Len):
        # Address = register to read
        # Len = number of bytes to read (1,2,3,4)
        #
        # a long is returned but only the requested bytes
        # are meaningful, starting from LsByte                                                       
  
        self.SCS_Low_macro()                                     # SPI chip select enable

        Addr = Address.to_bytes(2,'big')  
        self.SPI_TransferTx(COMM_SPI_READ)                    # SPI read command
        self.SPI_TransferTx(Addr[0])                          # address of the register to read, MsByte first
        self.SPI_TransferTxLast(Addr[1])                         

        Result = bytearray([0x0,0x0,0x0,0x0])           
        for i in range(0,Len):                                # read the requested number of bytes
            Result[i] = self.SPI_TransferRx(DUMMY_BYTE)       # LsByte first            
  
        self.SCS_High_macro()                                 # SPI chip select disable 
 
        return int.from_bytes(Result,'little')                   # return the result
        
    #---- write a directly addressable registers  ----------------------------------------------------

    def SPIWriteRegisterDirect (self, Address, DataOut):        
        # Address = register to write
        # DataOut = data to write     
  
        self.SCS_Low_macro()                                 # SPI chip select enable  

        Addr = Address.to_bytes(2,'big') 
        self.SPI_TransferTx(COMM_SPI_WRITE)                  # SPI write command
        self.SPI_TransferTx(Addr[0])                         # address of the register to write MsByte first
        self.SPI_TransferTx(Addr[1])                         

        Data = DataOut.to_bytes(4,'little')
        self.SPI_TransferTx(Data[0])                         # data to write LsByte first
        self.SPI_TransferTx(Data[1])                         
        self.SPI_TransferTx(Data[2])                             
        self.SPI_TransferTxLast(Data[3])                         
 
        self.SCS_High_macro()                                # SPI chip select enable       

    #---- read an indirectly addressable registers  --------------------------------------------------

    def SPIReadRegisterIndirect (self, Address, Len):
        # Address = register to read
        # Len = number of bytes to read (1,2,3,4)
        #
        # a long is returned but only the requested bytes
        # are meaningful, starting from LsByte    

        TempL = bytearray([0x0,0x0,0x0,0x0])                                                                           
        Addr = Address.to_bytes(2,'big')          # compose the command  05                                  
        TempL[0] = Addr[1]                        # address of the register to read, LsByte first
        TempL[1] = Addr[0]                        # 
        TempL[2] = Len                            # number of bytes to read
        TempL[3] = ESC_READ                       # ESC read 

        self.SPIWriteRegisterDirect (ECAT_CSR_CMD, int.from_bytes(TempL,'little'))  # write the command, data to write LsByte first

        while True:                                                                
          Byte4 = self.SPIReadRegisterDirect(ECAT_CSR_CMD,4).to_bytes(4,'little')   # wait for command execution
          #print("216:{}".format(Byte4))
          if (Byte4[3] & ECAT_CSR_BUSY)!=ECAT_CSR_BUSY:
            break
                                                              
        return self.SPIReadRegisterDirect(ECAT_CSR_DATA,Len)                        # read the requested register starting from LsByte

    #---- write an indirectly addressable registers  -------------------------------------------------

    def SPIWriteRegisterIndirect (self, DataOut, Address, Len):
        # Address = register to write
        # DataOut = data to write                                                                  

         
        TempL = bytearray([0x0,0x0,0x0,0x0])  

        self.SPIWriteRegisterDirect (ECAT_CSR_DATA, DataOut)  # write the data

        Addr = Address.to_bytes(2,'big')                      # compose the command
        TempL[0] = Addr.Byte[0]                       # address of the register  
        TempL[1] = Addr.Byte[1]                       # to write, LsByte first
        TempL[2] = Len                                # number of bytes to write
        TempL[3] = ESC_WRITE                          # ESC write

        self.SPIWriteRegisterDirect (ECAT_CSR_CMD,int.from_bytes(TempL,'little'))  # write the command

        while True:                                           # wait for command execution
          Byte4 = self.SPIReadRegisterDirect (ECAT_CSR_CMD, 4).to_bytes(4,'little')
          if (Byte4[3] & ECAT_CSR_BUSY)==0:
             break

    #---- read from process ram fifo ----------------------------------------------------------------

    def SPIReadProcRamFifo (self):     # read data from the output process ram, through the fifo                                              
                                      # these are the bytes received from the EtherCAT master and
                                      # that will be use by our application to write the outputs     
  
        if TOT_BYTE_NUM_OUT > 0:
          self.SPIWriteRegisterDirect (ECAT_PRAM_RD_CMD, PRAM_ABORT)   # abort any possible pending transfer
  
          self.SPIWriteRegisterDirect (ECAT_PRAM_RD_ADDR_LEN, 0x00001000 | TOT_BYTE_NUM_OUT<<16)   
                                                                        # the high word is the num of bytes
                                                                        # to read 0xTOT_BYTE_NUM_OUT----
                                                                        # the low word is the output process        
                                                                        # ram offset 0x----1000 

          self.SPIWriteRegisterDirect (ECAT_PRAM_RD_CMD, 0x80000000)    # start command        
  
                                                                        #------- one round is enough if we have ----
                                                                        #------- to transfer up to 64 bytes --------
   
          while True:                                                                     # wait for the data to be transferred from the output
            TempL = self.SPIReadRegisterDirect (ECAT_PRAM_RD_CMD,2).to_bytes(4,'little')  # process ram to the read fifo   
            #print("268:{}".format(TempL))    
            if TempL[1] == (FST_BYTE_NUM_ROUND_OUT/4):                                    # *CCC* 
              break
  
          self.SCS_Low_macro()                                               # enable SPI chip select 
  
          self.SPI_TransferTx(COMM_SPI_READ)                                 # SPI read command
          self.SPI_TransferTx(0x00)                                          # address of the read  
          self.SPI_TransferTxLast(0x00)                                      # fifo MsByte first
  
          for i in range(0,FST_BYTE_NUM_ROUND_OUT):                          # transfer the data                                                                       
            self.BufferOut.Byte[i] = self.SPI_TransferRx(DUMMY_BYTE)
          
          #print(self.BufferOut.Byte[0],self.BufferOut.Byte[1],self.BufferOut.Byte[2],self.BufferOut.Byte[3])                                                                               
         
    
          self.SCS_High_macro()                                              # disable SPI chip select 
  
        if SEC_BYTE_NUM_OUT > 0:                                                        #-- if we have to transfer more then 64 bytes , we must do another round to transfer the remainig bytes --
          while True:                                                                   # wait for the data to be transferred from the output  
            TempL = self.SPIReadRegisterDirect(ECAT_PRAM_RD_CMD,2).to_bytes(4,'little') # process ram to the read fifo                                                                 
            if TempL[1] == SEC_BYTE_NUM_ROUND_OUT/4:                                    # *CCC*  
              break

          self.SCS_Low_macro()                                               # enable SPI chip select   
    
          self.SPI_TransferTx(COMM_SPI_READ)                                 # SPI read command
          self.SPI_TransferTx(0x00)                                          # address of the read  
          self.SPI_TransferTxLast(0x00)                                      # fifo MsByte first
    
          for i in range(0,SEC_BYTE_NUM_ROUND_OUT):                          # transfer loop for the remaining bytes                                                                          
            self.BufferOut.Byte[i+64] = self.SPI_TransferRx(DUMMY_BYTE)      # we transfer the second part of
                                                                               # the buffer, so offset by 64
      
          self.SCS_High_macro()                                              # SPI chip select disable  

    #---- write to the process ram fifo --------------------------------------------------------------

    def SPIWriteProcRamFifo(self):          
        # write data to the input process ram, through the fifo                                        
        # these are the bytes that we have read from the inputs of our                   
        # application and that will be sent to the EtherCAT master
  
        if TOT_BYTE_NUM_IN > 0:   
          self.SPIWriteRegisterDirect (ECAT_PRAM_WR_CMD, PRAM_ABORT)         # abort any possible pending transfer 
          self.SPIWriteRegisterDirect (ECAT_PRAM_WR_ADDR_LEN, 0x00001200 | TOT_BYTE_NUM_IN<<16 )   
                                                                        # the high word is the num of bytes
                                                                        # to write 0xTOT_BYTE_NUM_IN----
                                                                        # the low word is the input process        
                                                                        # ram offset  0x----1200
                                                                                               
          self.SPIWriteRegisterDirect (ECAT_PRAM_WR_CMD, 0x80000000)    # start command    
                                                                        #------- one round is enough if we have to transfer up to 64 bytes    
          while True:                                                   # check that the fifo has enough free space 
            TempL = self.SPIReadRegisterDirect (ECAT_PRAM_WR_CMD,2).to_bytes(4,'little') 
            #print(TempL)                                                                
            if TempL[1] >= (FST_BYTE_NUM_ROUND_IN/4):                    # *CCC*
              break
  
          self.SCS_Low_macro()                                          # enable SPI chip select  

          self.SPI_TransferTx(COMM_SPI_WRITE)                           # SPI write command
          self.SPI_TransferTx(0x00)                                     # address of the write fifo 
          self.SPI_TransferTx(0x20)                                     # MsByte first 

          for i in range(0,FST_BYTE_NUM_ROUND_IN - 1 ):                 # transfer the data                                                                   
            self.SPI_TransferTx (self.BufferIn.Byte[i])                                                                                           
                                                                  
          self.SPI_TransferTxLast (self.BufferIn.Byte[FST_BYTE_NUM_ROUND_IN - 1]) # one last byte  

          self.SCS_High_macro()                                         # disable SPI chip select           
  
        if SEC_BYTE_NUM_IN > 0:                                         # if we have to transfer more then 64 bytes, we must do another round to transfer the remainig bytes
          while True:                                                   # check that the fifo has enough free space       
            TempL = self.SPIReadRegisterDirect(ECAT_PRAM_WR_CMD,2).to_bytes(2,'little')
            #print(TempL)
            if TempL[1] >= (SEC_BYTE_NUM_ROUND_IN/4):                   #   *CCC*
              break
              
          self.SCS_Low_macro()                                           # enable SPI chip select
    
          self.SPI_TransferTx(COMM_SPI_WRITE)                            # SPI write command
          self.SPI_TransferTx(0x00)                                      # address of the write fifo 
          self.SPI_TransferTx(0x20)                                      # MsByte first 

          for i in range(0,SEC_BYTE_NUM_ROUND_IN - 1):                            # transfer loop for the remaining bytes
            self.SPI_TransferTx (self.BufferIn.Byte[i+64])                        # we transfer the second part of the buffer, so offset by 64                                                                

          self.SPI_TransferTxLast (self.BufferIn.Byte[SEC_BYTE_NUM_ROUND_IN - 1]) # one last byte  

          self.SCS_High_macro()                                          # disable SPI chip select    

    #---- EasyCAT board initialization ---------------------------------------------------------------

    def Init(self):
        Tout = const(1000)       
  
        #if defined (ARDUINO_ARCH_RP2040)
	        #SPI.begin(true);
        #else	
	        #SPI.begin();
        #endif
        self.SCS_High_macro()       
  
        utime.sleep_ms(100)     
                                                                 # set SPI parameters
        #SPI.beginTransaction(SPISettings(SpiSpeed, MSBFIRST, SPI_MODE0)); 
  
        self.SPIWriteRegisterDirect (RESET_CTL, DIGITAL_RST)     # LAN9252 reset 
   
        i = 0                                               # reset timeout 
        while True:                                         # wait for reset to complete
          i = i + 1                                                  
          TempL = self.SPIReadRegisterDirect (RESET_CTL, 4).to_bytes(4,'little')
          print(TempL)
          if (TempL[0] & 0x01)==0 or (i >= Tout):
            break;
                                                          
        if i >= Tout:                                       # time out expired  
          print("Tout0:{}".format(i))             
          return False                                      # initialization failed  
                                                        
        i = 0                                               # reset timeout  
        while True:                                         # check the Byte Order Test Register
          i = i + 1                                               
          TempL = self.SPIReadRegisterDirect (BYTE_TEST, 4)   
          #print(hex(TempL))       
          if (TempL == 0x87654321) or (i >= Tout):
            break   

        if i >= Tout:                                       # time out expired      
          print("Tout1:{}".format(i))
          return False                                      # initialization failed  
  
        i = 0                                               # reset timeout  
        while True:                                         # check the Ready flag
          i = i + 1                                                        
          TempL = self.SPIReadRegisterDirect (HW_CFG, 4).to_bytes(4,'little')
          print(TempL)
          if (TempL[3] & READY) or (i >= Tout):
            break
                                                          
        if i >= Tout:                                       # time out expired      
          print("Tout2:{}".format(i))
          return False                                      # initialization failed   
  
        if BYTE_NUM==32:
          print("STANDARD MODE") 
        else:
          print("CUSTOM MODE") 

        print (TOT_BYTE_NUM_OUT," Byte Out")
        print (TOT_BYTE_NUM_IN, " Byte In")              
        s1=''                                                 
        if (self.Sync_ == DC_SYNC) or (self.Sync_ == SM_SYNC):            #--- if requested, enable --------   
                                                                          #--- interrupt generation --------   
          if self.Sync_ == DC_SYNC:                                            # enable interrupt from SYNC 0
            self.SPIWriteRegisterIndirect (0x00000004, AL_EVENT_MASK, 4)  # in AL event mask register, and disable other interrupt sources    
            s1 = "DC_SYNC"      
          else:                                                           # enable interrupt from SM 0 event 
                                                                          # (output synchronization manager)
            self.SPIWriteRegisterIndirect (0x00000100, AL_EVENT_MASK, 4)     
            s1 = "SM_SYNC"                                                  # in AL event mask register, and disable other interrupt sources                   
                                                         
          self.SPIWriteRegisterDirect (IRQ_CFG, 0x00000111)              # set LAN9252 interrupt pin driver as push-pull active high
          self.SPIWriteRegisterDirect (INT_EN, 0x00000001)               # (On the EasyCAT shield board the IRQ pin is inverted by a mosfet, so Arduino receives an active low signal) 
                                                                         # enable LAN9252 interrupt        
        else:
          s1 = "ASYNC"
  
        print ("Sync = {}".format(s1)); 
        TempL = self.SPIReadRegisterDirect (ID_REV, 4)         # read the chip identification 
                                                            # and revision, and print it out on the serial line
        print ("Detected chip ",TempL>>16,"  Rev ",TempL & 0x0000FFFF)                                           
  
                          
        return True                                        # initalization completed   



    #---- EtherCAT task ------------------------------------------------------------------------------

    def MainTask(self):          
      # must be called cyclically by the application                                                                
      TempL = self.SPIReadRegisterIndirect (WDOG_STATUS, 1).to_bytes(4,"little")# read watchdog status, starting from LsByte
      #print("wc:{}".format(TempL))
      _WatchDog = 0 if (TempL[0] & 0x01) == 0x01 else 1                         # set/reset the corrisponding flag
     
      TempL = self.SPIReadRegisterIndirect (AL_STATUS, 1).to_bytes(4,"little")  # read the EtherCAT State Machine status, starting from LsByte
      Status = TempL[0] & 0x0F                                                  # to see if we are in operational state
      #print("op:{}".format(TempL))
      _Operational = 1 if Status == ESM_OP else 0                               # set/reset the corrisponding flag                                                                 
                                                                #--- process data transfert ----------                                                                                                                    
      if _WatchDog or (not _Operational):                       # if watchdog is active or we are not in operational state, reset         
        for i in range(0,TOT_BYTE_NUM_OUT):                     # the output buffer
          self.BufferOut.Byte[i] = 0                             
                                                                                                                                                             
      self.SPIReadProcRamFifo()                                    # otherwise transfer process data from the EtherCAT core to the output buffer  
                 
      self.SPIWriteProcRamFifo()                                     # we always transfer process data from the input buffer to the EtherCAT core                                                              
                                        
      self.Operational  = _Operational
      
      if _WatchDog:                                              # return the status of the State Machine and of the watchdog
        Status |= 0x80                                         
                                                           
      return Status                                           

  
# ---------------------------------------------
