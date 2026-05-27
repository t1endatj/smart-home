#pragma once

#include <Arduino.h>

struct GasData {
  int ppm;
  bool digitalAlarm;
};

void gasSensorBegin();
GasData gasSensorRead();
void gasSensorPrint(const GasData &data);
