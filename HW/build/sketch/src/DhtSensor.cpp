#line 1 "/tmp/Smart_Home_HardW-cli/Smart_Home_HardW/src/DhtSensor.cpp"
#include "DhtSensor.h"

#include <DHT.h>

#include "Pins.h"

namespace {
constexpr uint8_t DHT_TYPE = DHT22;
DHT dht(DHT_PIN, DHT_TYPE);
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
