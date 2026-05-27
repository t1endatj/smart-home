#line 1 "/tmp/Smart_Home_HardW-cli/Smart_Home_HardW/src/PirSensor.cpp"
#include "PirSensor.h"

#include "Pins.h"

void pirSensorBegin() {
  pinMode(PIR_PIN, INPUT);
}

bool pirSensorRead() {
  return digitalRead(PIR_PIN) == HIGH;
}

void pirSensorPrint(bool motion) {
  Serial.print("PIR Phong Khach: ");
  Serial.println(motion ? "CO CHUYEN DONG" : "KHONG CO CHUYEN DONG");
}
