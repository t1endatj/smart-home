#pragma once

#include <Arduino.h>

enum class LedId : uint8_t {
  Hall,
  Bed,
  Wc,
  Living,
  Kitchen,
  Tech,
  Count
};

void ledLightBegin();
void ledLightSet(LedId id, bool on);
void ledLightSetAll(bool on);
bool ledLightIsOn(LedId id);
const char *ledLightName(LedId id);
