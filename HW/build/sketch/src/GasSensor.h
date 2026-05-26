#line 1 "/home/phuchoangsrc/smart-home/Smart_Home_HardW/src/GasSensor.h"
#pragma once

#include <Arduino.h>

struct GasData {
  int analogValue;
  bool digitalAlarm;
};

void gasSensorBegin();
GasData gasSensorRead();
void gasSensorPrint(const GasData &data);
