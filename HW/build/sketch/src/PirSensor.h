#line 1 "/tmp/Smart_Home_HardW-cli/Smart_Home_HardW/src/PirSensor.h"
#pragma once

#include <Arduino.h>

void pirSensorBegin();
bool pirSensorRead();
void pirSensorPrint(bool motion);
