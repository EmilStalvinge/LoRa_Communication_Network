void setup(){
  Serial.begin(9600);
}

void loop(){
  //Serial.println("Hello g!");   
  //delay(1000);

  if(Serial.available()){         //From RPi to Arduino
    //r = r * (Serial.read() - '0');  //conveting the value of chars to integer
    Serial.write(Serial.read());
    //Serial.println("");
  }
}
