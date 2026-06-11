#include "DhtSensor.h"

#include <DHT.h>

#include "./Pins.h"

namespace {
DHT dht(IotPins::DHT_PIN, IotPins::DHT_TYPE);
}

void dhtSensorBegin() {
  dht.begin();
}

bool dhtSensorRead(ClimateData &data) {
  data.temperature = dht.readTemperature();
  data.humidity = dht.readHumidity();

  return !isnan(data.temperature) && !isnan(data.humidity);
}

void dhtSensorPrint(const ClimateData &data) {
  Serial.print("Nhiet do: ");
  Serial.print(data.temperature);
  Serial.print(" *C  |  ");
  Serial.print("Do am: ");
  Serial.print(data.humidity);
  Serial.println(" %");
}
