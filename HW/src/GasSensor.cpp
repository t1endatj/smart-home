#include "GasSensor.h"
#include "Pins.h"
#include <math.h>

void gasSensorBegin() {
  pinMode(MQ2_DO_PIN, INPUT);
}

GasData gasSensorRead() {
  float voltage = analogRead(MQ2_AO_PIN) * 3.3 / 4095.0;
  int ppmVal = 0;
  if (voltage > 0.5) {
    ppmVal = round((voltage - 0.5) / 3.5 * 1000.0);
  }
  return {ppmVal, digitalRead(MQ2_DO_PIN) == HIGH};
}

void gasSensorPrint(const GasData &data) {
  Serial.print("MQ2 Nha Bep PPM: ");
  Serial.print(data.ppm);
  Serial.print(" | DO: ");
  Serial.println(data.digitalAlarm ? "CANH BAO" : "BINH THUONG");
}
