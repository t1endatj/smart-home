#pragma once

#include <Arduino.h>

enum class LedId : uint8_t {
  Hall,
  Kitchen,
  Bathroom,
  Bedroom,
  Living,
  Count
};

void ledLightBegin();
void ledLightSet(LedId id, bool on);
void ledLightSetAll(bool on);
bool ledLightIsOn(LedId id);
const char *ledLightName(LedId id);
