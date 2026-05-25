#line 1 "/home/phuchoangsrc/smart-home/Smart_Home_HardW/src/DhtSensor.h"
#pragma once

#include <Arduino.h>

struct ClimateData {
  float temperature;
  float humidity;
};

void dhtSensorBegin();
bool dhtSensorRead(ClimateData &data);
void dhtSensorPrint(const ClimateData &data);
