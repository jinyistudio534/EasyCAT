//********************************************************************************************
//                                                                                           *
// AB&T Tecnologie Informatiche - Ivrea Italy                                                *
// http://www.bausano.net                                                                    *
// https://www.ethercat.org/en/products/791FFAA126AD43859920EA64384AD4FD.htm                 *
//                                                                                           *  
//********************************************************************************************    

//********************************************************************************************    
//                                                                                           *
// This software is distributed as an example, "AS IS", in the hope that it could            *
// be useful, WITHOUT ANY WARRANTY of any kind, express or implied, included, but            *
// not limited,  to the warranties of merchantability, fitness for a particular              *
// purpose, and non infringiment. In no event shall the authors be liable for any            *    
// claim, damages or other liability, arising from, or in connection with this software.     *
//                                                                                           *
//******************************************************************************************** 



//---- AB&T EasyCAT shield application example V.2_0 -------------------------------------------  



#include "EasyCAT_PICO.h"           // EasyCAT library to interface the LAN9252
#include <SPI.h>                    // SPI library

#define BLINK_SPEED 250


 
EasyCAT EASYCAT;                    // EasyCAT istantiation

                                    // The constructor allow us to choose the pin used for the EasyCAT SPI chip select 
                                    // Without any parameter pin 9 will be used 
                   
                                    // We can choose between:
                                    // 8(27), 9(22), 10, A5, 6, 7                                    

                                    // On the EasyCAT board the SPI chip select is selected through a bank of jumpers              

                                    // (The EasyCAT board REV_A allows only pins 8, 9, 10 through 0 ohm resistors)

 //EasyCAT EASYCAT(8);              // example:                                  
                                    // pin 8 will be used as SPI chip select
                                    // The chip select chosen by the firmware must match the setting on the board  


//---- pins declaration ------------------------------------------------------------------------------

//---- global variables ---------------------------------------------------------------------------


unsigned long Millis = 0;
unsigned long PreviousMillis = 0;
unsigned long PreviousSaw = 0;
unsigned long PreviousCycle = 0;
uint32_t      BlinkTime;
uint32_t      Time;

//---- setup ---------------------------------------------------------------------------------------
 
void setup()
{
  SPI.setCS(5);
  SPI.setSCK(2);
  SPI.setRX(4);
  SPI.setTX(3);
    
  Serial.begin(115200);                                             // serial line initialization
  while(!Serial){
    delay(25);
  };                                                 //(used only for debug)
          
  Serial.print ("\nEasyCAT - Generic EtherCAT slave\n");          // print the banner

  

  pinMode(25, OUTPUT);                                           //---- initialize the EasyCAT board -----
                                                                  
  if (EASYCAT.Init() == true)                                     // initialization
  {                                                               // succesfully completed
    Serial.print ("initialized\n");  
   
    BlinkTime = millis();                               //
  }                                                               //
  
  else                                                            // initialization failed   
  {                                                               // the EasyCAT board was not recognized
    Serial.print ("initialization failed\n");                       //     
                                                                  // The most common reason is that the SPI 
                                                                  // chip select choosen on the board doesn't 
                                                                  // match the one choosen by the firmware
                                                                  
                                             // stay in loop for ever
                                                                  // with the Arduino led blinking
    while(1)                                                      //
    {                                                             //   
      digitalWrite (25, LOW);                                     // 
      delay(500);                                                 //   
      digitalWrite (25, HIGH);                                    //  
      delay(500);                                                 // 
    }                                                             // 
  } 
  
  PreviousMillis = millis();
}


//---- main loop ----------------------------------------------------------------------------------------
 
void loop()                                             // In the main loop we must call ciclically the 
{                                                       // EasyCAT task and our application
                                                        //
                                                        // This allows the bidirectional exachange of the data
                                                        // between the EtherCAT master and our application
                                                        //
                                                        // The EasyCAT cycle and the Master cycle are asynchronous
                                                        //   

  EASYCAT.MainTask();                                   // execute the EasyCAT task
  
  Application();                                        // user applications
  
}



//---- user application ------------------------------------------------------------------------------

void Application ()                                        

{

  
  Millis = millis();                                    // As an example for this application 
  if (Millis - PreviousMillis >= 50)                    // we choose a cycle time of 10 mS 
  {                                                     // 
    PreviousMillis = Millis;                            // 
  
    for(int n1=0;n1<8;n1++)
    {  
      EASYCAT.BufferIn.Byte[n1] = EASYCAT.BufferOut.Byte[n1];
    }                                                 // we use these variables to create sawtooth,
  }                                                  // with different slopes and periods, for
                                                       // test pourpose, in input Bytes 2,3,4,5,30,31
  Time = millis();                                                  //------ led blink management --------------     
  if ((Time - BlinkTime) >  BLINK_SPEED)                          //
  {                                                               //  
    BlinkTime = Time;                                             //
    digitalWrite (25,!(digitalRead(25))); 
      
  }   
                                             
}




