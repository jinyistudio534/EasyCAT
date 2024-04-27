#include <LCD_I2C.h>
#include <TCA9555.h>
#include <Wire.h>

#include <Adafruit_NeoPixel.h>
#ifdef __AVR__
 #include <avr/power.h> // Required for 16 MHz Adafruit Trinket
#endif

// Which pin on the Arduino is connected to the NeoPixels?
// On a Trinket or Gemma we suggest changing this to 1:
#define LED_PIN    0

// How many NeoPixels are attached to the Arduino?
#define LED_COUNT 16

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

Adafruit_NeoPixel strip(LED_COUNT, LED_PIN, NEO_GRB + NEO_KHZ800);

TCA9535 di16l(0x20);

LCD_I2C lcd(0x27, 16, 2); // Default address of most PCF8574 modules, change according
 
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


unsigned long PreviousMillis = 0;
unsigned long PreviousSaw = 0;
unsigned long PreviousCycle = 0;
bool          stat;
uint32_t      BlinkTime;
uint32_t      LcdTime;
uint32_t      Time;
uint8_t       Qb[2]={1,0};
uint8_t       EcatState;
uint8_t       bitx[4]={0,0,0,0};
int           last16l = 0;
int           neoN = 0;
bool          dis1=false;
bool          lcdx=false;

//---- setup ---------------------------------------------------------------------------------------
 
void setup()
{
  
  Serial.begin(115200);                                             // serial line initialization
  while(!Serial){
    delay(25);
  };             
  // no interrupt notification
  //pinMode(6,INPUT);
  //pinMode(10,INPUT);
  //pinMode(11,INPUT);
  //pinMode(9,INPUT);
  
  Wire.setSCL(21);
  Wire.setSDA(20); 
  Wire.begin();  
    
  di16l.begin(false);
  while(!di16l.isConnected()) {
    delay(3);
  } 
  di16l.setPolarity8(0, 0xFF); // all inverted 
  delay(100);
  di16l.setPolarity8(1, 0xFF); // all inverted
  delay(100);
   
  lcd.begin(false);      // If you are using more I2C devices using the Wire library use lcd.begin(false)
                    // this stop the library(LCD_I2C) from calling Wire.begin()
  lcd.backlight();  
 
     
                                      //(used only for debug)
          
  Serial.print ("\nEasyCAT - Generic EtherCAT slave\n");          // print the banner  
  lcd.clear();
  lcd.home();  
  lcd.print("EasyCAT");
  delay(10);  
  lcd.setCursor(10, 0); // Or setting the cursor in the desired position.
  delay(10);   
   
  pinMode(LED_BUILTIN, OUTPUT);                                           
  //---- initialize the EasyCAT board -----
  SPI.setCS(5);
  SPI.setSCK(2);
  SPI.setRX(4);
  SPI.setTX(3);
                                                                  
  if (EASYCAT.Init() == true)                                     // initialization
  {                                                               // succesfully completed
    Serial.print ("initialized\n");  
    lcd.print("init");
    BlinkTime = millis();                               //
    lcdx = true;
  }                                                               //
  
  else                                                            // initialization failed   
  {                                                               // the EasyCAT board was not recognized
    Serial.print ("initialization failed\n");                     //     
    lcd.print("fail");                                     // The most common reason is that the SPI 
                                                                  // chip select choosen on the board doesn't 
                                                                  // match the one choosen by the firmware
                                                                  
                                             // stay in loop for ever
                                                                  // with the Arduino led blinking
    while(1)                                                      //
    {                                                             //   
      digitalWrite (LED_BUILTIN, LOW);                                     // 
      delay(500);                                                 //   
      digitalWrite (LED_BUILTIN, HIGH);                                    //  
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

  EcatState = EASYCAT.MainTask();                                   // execute the EasyCAT task
  
  Application();                                        // user applications
  
}

//---- user application ------------------------------------------------------------------------------

void Application ()                                        

{

  
  Time = millis();                                    // As an example for this application 
  if (Time - PreviousMillis >= 50)                    // we choose a cycle time of 10 mS 
  {                                                     // 
    PreviousMillis = Time;                            //   
                                                  // we use these variables to create sawtooth,
  }                                                  // with different slopes and periods, for
                                                       // test pourpose, in input Bytes 2,3,4,5,30,31
  Time = millis();                                                  //------ led blink management --------------     
  if ((Time - BlinkTime) >  BLINK_SPEED)                          //
  {                                                               //  
    BlinkTime = Time;                                             //
    digitalWrite (LED_BUILTIN,!(digitalRead(LED_BUILTIN))); 
   
  }   
                                             
}


void setup1()
{    
  // These lines are specifically to support the Adafruit Trinket 5V 16 MHz.
  // Any other board, you can remove this part (but no harm leaving it):
  #if defined(__AVR_ATtiny85__) && (F_CPU == 16000000)
    clock_prescale_set(clock_div_1);
  #endif
  // END of Trinket-specific code.

  strip.begin();           // INITIALIZE NeoPixel strip object (REQUIRED)
  strip.show();            // Turn OFF all pixels ASAP
  strip.setBrightness(50); // Set BRIGHTNESS to about 1/5 (max = 255)

  while(!lcdx){
  };
}

void loop1()
{
   // Fill along the length of the strip in various colors...  
  Time = millis();                                                  //------ led blink management --------------     
  if ((Time - LcdTime) >  300) 
  {
    LcdTime = Time; 
    if(dis1) {                                         
      lcd.setCursor(15, 0); 
      lcd.print(stat?"-":"*");    
      stat = !(stat);     
    }
    else 
    {
      if(Qb[0] != EASYCAT.BufferOut.Byte[0]) {
        Qb[0] = EASYCAT.BufferOut.Byte[0];
        lcd.setCursor(0, 1);   
        lcd.printf("QB4=%03d",Qb[0]);     
      }   
      
            
    }
    dis1 = !dis1;      
  } 
  EASYCAT.BufferIn.Byte[4] = di16l.read8(0);
  EASYCAT.BufferIn.Byte[5] = di16l.read8(1);  
  
  if(bitx[0] != EASYCAT.BufferOut.Byte[2]) {  
    strip.setPixelColor(bitx[0],strip.Color(0,0,0));
    bitx[0] = EASYCAT.BufferOut.Byte[2];
    strip.setPixelColor(bitx[0],strip.Color(120,0,0));
    strip.show();
  }
}

// Fill strip pixels one after another with a color. Strip is NOT cleared
// first; anything there will be covered pixel by pixel. Pass in color
// (as a single 'packed' 32-bit value, which you can get by calling
// strip.Color(red, green, blue) as shown in the loop() function above),
// and a delay time (in milliseconds) between pixels.
void colorWipe(uint32_t color, int wait) {
  for(int i=0; i<strip.numPixels(); i++) { // For each pixel in strip...
    strip.setPixelColor(i, color);         //  Set pixel's color (in RAM)
    strip.show();                          //  Update strip to match
    delay(wait);                           //  Pause for a moment
  }
}





