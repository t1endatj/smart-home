#line 1 "/tmp/Smart_Home_HardW-cli/Smart_Home_HardW/src/LedLight.cpp"
#include "LedLight.h"

#include "./Pins.h"

namespace {
struct LedConfig {
  LedId id;
  uint8_t pin;
  const char *name;
};

constexpr LedConfig LEDS[] = {
    {LedId::Hall, IotPins::HALLWAY_LED_PIN, "Den Hanh Lang"},
    {LedId::Kitchen, IotPins::KITCHEN_LED_PIN, "Den Nha Bep"},
    {LedId::Bathroom, IotPins::BATHROOM_LED_PIN, "Den Nha Ve Sinh"},
    {LedId::Bedroom, IotPins::BEDROOM_LED_PIN, "Den Phong Ngu"},
    {LedId::Living, IotPins::LIVING_ROOM_LED_PIN, "Den Phong Khach"},
};

bool ledStates[static_cast<uint8_t>(LedId::Count)] = {};

const LedConfig &configFor(LedId id) {
  return LEDS[static_cast<uint8_t>(id)];
}
}

void ledLightBegin() {
  for (const LedConfig &led : LEDS) {
    pinMode(led.pin, OUTPUT);
    digitalWrite(led.pin, LOW);
    ledStates[static_cast<uint8_t>(led.id)] = false;
  }
}

void ledLightSet(LedId id, bool on) {
  const LedConfig &led = configFor(id);
  ledStates[static_cast<uint8_t>(id)] = on;
  digitalWrite(led.pin, on ? HIGH : LOW);

  Serial.print(led.name);
  Serial.println(on ? ": BAT" : ": TAT");
}

void ledLightSetAll(bool on) {
  for (const LedConfig &led : LEDS) {
    ledLightSet(led.id, on);
  }
}

bool ledLightIsOn(LedId id) {
  return ledStates[static_cast<uint8_t>(id)];
}

const char *ledLightName(LedId id) {
  return configFor(id).name;
}
