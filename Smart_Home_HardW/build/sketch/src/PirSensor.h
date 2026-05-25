#line 1 "/home/phuchoangsrc/smart-home/Smart_Home_HardW/src/PirSensor.h"
#pragma once

#include <Arduino.h>

void pirSensorBegin();
bool pirSensorRead();
void pirSensorPrint(bool motion);
