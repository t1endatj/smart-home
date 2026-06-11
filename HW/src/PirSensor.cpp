#include "PirSensor.h"

#include "./Pins.h"

void pirSensorBegin() {
  pinMode(IotPins::PIR_PIN, INPUT);
}

bool pirSensorRead() {
  const bool isHigh = digitalRead(IotPins::PIR_PIN) == HIGH;
  return IotPins::PIR_ACTIVE_HIGH ? isHigh : !isHigh;
}

void pirSensorPrint(bool motion) {
  Serial.print("PIR Phong Khach: ");
  Serial.println(motion ? "CO CHUYEN DONG" : "KHONG CO CHUYEN DONG");
}
