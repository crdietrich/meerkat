// counter
int a = 0;

void setup() {
  // start serial connection on USB serial
  Serial.begin(9600);
  Serial1.begin(9600);
}

void loop(){
  // print counter with ID header characters
  /// to USB serial port
  Serial.print("Arduino>>");
  Serial.println(a);
  /// to hardware serial port
  Serial1.print("Arduino>>");
  Serial1.println(a);
  
  if (a == 10) {
    a = 0;
  }else{
    a += 1;
  }
  // return data at 4 Hz
  delay(250);
}
