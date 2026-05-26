#line 1 "/home/phuchoangsrc/smart-home/Smart_Home_HardW/src/GasSensor.cpp"
#include "GasSensor.h"

#include "Pins.h"

void gasSensorBegin() {
  pinMode(MQ2_DO_PIN, INPUT);
}

GasData gasSensorRead() {
  return {analogRead(MQ2_AO_PIN), digitalRead(MQ2_DO_PIN) == HIGH};
}

void gasSensorPrint(const GasData &data) {
  Serial.print("MQ2 Nha Bep AO: ");
  Serial.print(data.analogValue);
  Serial.print(" | DO: ");
  Serial.println(data.digitalAlarm ? "CANH BAO" : "BINH THUONG");
}
