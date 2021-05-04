const int irLED = 3;
const int mosfetPin = 4;
//volatile byte state = LOW;
volatile int count =0;
const byte interruptPin =2;
boolean firstWakeUp = true;
volatile boolean raspiAwake = false;
volatile boolean motionTriggered = false;
int r = 1;
volatile float wakeupinterval = 10;//1831  // wakeupinterval =  time_in_seconds/((256*1024)/ 8000000))
float time_in_seconds;
float minutes;
int batteryPin = A0;  
float batteryVoltage;




 
void setup() {
   pinMode(interruptPin,INPUT);
   attachInterrupt(digitalPinToInterrupt(interruptPin),motionDetected,RISING);
   pinMode(irLED, OUTPUT);
   pinMode(mosfetPin, OUTPUT);
   pinMode(13, OUTPUT);
   Serial.begin(9600);  
  ////////////////CLOCK SETUP/////////////////////////
  //TCCR1A = (0 << COM0A1) | (0 << COM0A0) | (0 << COM0B1) | (0 << COM0B0) | (0 << WGM01) | (0 << WGM00); //normal mode
    TCCR1B = (0 << WGM12)  | (1 << CS12) | (0 << CS11) | (1 << CS10);  // prescaler 1024
    TIMSK1 = (0 << OCIE1B) | (0 << OCIE1A) | (1 << TOIE1);    
  ////////////////////////////////////////////////
} 
 
void loop() 
{
  
    if(raspiAwake && Serial.available())
    {
      raspiGoodmorning();
    }  
    
}
   

ISR(TIMER1_OVF_vect){         
    count++;   
    if (count == (int)wakeupinterval)
    {
      digitalWrite(mosfetPin, HIGH); 
      digitalWrite(13, HIGH);
      raspiAwake = true;
      count = 0;
    }    
}

//external interrupt motionsensor
void motionDetected(){  
  raspiAwake = true;
  digitalWrite(mosfetPin, HIGH);  
  digitalWrite(13, HIGH);   
  motionTriggered= true;
}


void raspiGoodmorning()
  {    
        
      //r =(Serial.read() - '0');  //conveting the value of chars to integer
      r = Serial.readString().toInt();
      //Serial.println(r); 
      
      if (r==1) //request batteryVoltage
      {
        batteryVoltage= analogRead(batteryPin) * (5.0 / 1023.0);
        Serial.println(batteryVoltage,DEC);   
      }
      
      if (r==2) //request shutdown after 30 seconds
      {
        Serial.println("shutting down MOSFET in 20s");
        delay(15000);
        digitalWrite(mosfetPin, LOW); 
        digitalWrite(13, LOW); 
        raspiAwake = false;         
      }
      
      if (r==3) //request irLED on
      {
         digitalWrite(irLED, HIGH);
         Serial.println("turng on ir led");
      }
      
      if (r==4) //request irLED off
      {
         digitalWrite(irLED, LOW);  
         Serial.println("turng off ir led");      
      }


       if (r==5) //request wakeupReason
      {
         if (motionTriggered)
         {
            Serial.println(1,DEC); 
         }
         else     
         {
           Serial.println(0,DEC); 
         }
        motionTriggered = false;
      }


         if (r == 6) //ask if first time wakeup         
      {

         minutes = (float)r;
        time_in_seconds = minutes*60.0;
        //wakeupinterval = time_in_seconds/0.032768;//((256.*1024)/ 8000000)
           if (firstWakeUp)
         {
            Serial.println(1,DEC); 
           // Serial.print("setting timer and the wakeupinterval 3 min");
         }
         else     
         {
           Serial.println(0,DEC); 
          // Serial.print("setting timer and the wakeupinterval 6 min ");
         }  
       
      }

      
       if (r==7) //setting timer
      {      
          if (firstWakeUp)
         {
            wakeupinterval = 109863,28; // 1 tim
            count = 0;
         }

           firstWakeUp = false; 
          
      }
      
     
   
}
