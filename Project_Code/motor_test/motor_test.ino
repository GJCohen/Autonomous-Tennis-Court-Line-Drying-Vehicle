#include <Servo.h>

Servo motorController;

void setup() {
  // Attach the Victor 888 signal on pin 9 
  // Explicitly set pulse bounds to standard RC 1000us (full reverse) and 2000us (full forward)
  motorController.attach(9, 1000, 2000); 
}

void loop() {
  motorController.writeMicroseconds(1500); // Neutral / Stop (1.5 ms)
  delay(3000);
  
  motorController.writeMicroseconds(1650); // Slow Forward
  delay(3000);
  

}
