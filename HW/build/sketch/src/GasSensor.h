#line 1 "/tmp/Smart_Home_HardW-cli/Smart_Home_HardW/src/GasSensor.h"
#pragma once

#include <Arduino.h>

struct GasData {
  int ppm;
  bool digitalAlarm;
};

void gasSensorBegin();
GasData gasSensorRead();
void gasSensorPrint(const GasData &data);
