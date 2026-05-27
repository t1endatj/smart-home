#line 1 "/tmp/Smart_Home_HardW-cli/Smart_Home_HardW/src/FanMotor.h"
#pragma once

#include <Arduino.h>

enum class FanId : uint8_t {
  Bed,
  Living,
  Kitchen,
  Count
};

void fanMotorBegin();
void fanMotorSet(FanId id, bool on);
void fanMotorSetAll(bool on);
bool fanMotorIsOn(FanId id);
const char *fanMotorName(FanId id);
void fanMotorAutoByTemperature(float temperature);
