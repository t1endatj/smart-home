#pragma once

#include <Arduino.h>

enum class FanId : uint8_t {
  Living,
  Bed,
  Count
};

void fanMotorBegin();
void fanMotorSet(FanId id, bool on);
void fanMotorSetAll(bool on);
void fanMotorSetSpeedPercent(FanId id, uint8_t percent);
bool fanMotorIsOn(FanId id);
uint8_t fanMotorSpeedPercent(FanId id);
const char *fanMotorName(FanId id);
void fanMotorAutoByTemperature(float temperature);
