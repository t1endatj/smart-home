#include "GasSensor.h"

#include <math.h>

#include "./Pins.h"

void gasSensorBegin() {
  pinMode(IotPins::MQ2_ANALOG_PIN, INPUT);
}

GasData gasSensorRead() {
  const int rawValue = analogRead(IotPins::MQ2_ANALOG_PIN);
  return {rawValue, rawValue >= IotPins::MQ2_GAS_THRESHOLD};
}

void gasSensorPrint(const GasData &data) {
  Serial.print("MQ2 Nha Bep PPM: ");
  Serial.print(data.ppm);
  Serial.print(" | DO: ");
  Serial.println(data.digitalAlarm ? "CANH BAO" : "BINH THUONG");
}
