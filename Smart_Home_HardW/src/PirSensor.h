#pragma once

#include <Arduino.h>

void pirSensorBegin();
bool pirSensorRead();
void pirSensorPrint(bool motion);
