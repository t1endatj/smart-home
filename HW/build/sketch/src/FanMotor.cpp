#line 1 "/tmp/Smart_Home_HardW-cli/Smart_Home_HardW/src/FanMotor.cpp"
#include "FanMotor.h"

#include "Pins.h"

namespace {
struct FanConfig {
  FanId id;
  uint8_t in1Pin;
  uint8_t in2Pin;
  const char *name;
};

constexpr FanConfig FANS[] = {
    {FanId::Bed, FAN_BED_IN1_PIN, FAN_BED_IN2_PIN, "Quat Phong Ngu"},
    {FanId::Living, FAN_LIVING_IN1_PIN, FAN_LIVING_IN2_PIN, "Quat Tran Phong Khach"},
    {FanId::Kitchen, FAN_KITCHEN_IN1_PIN, FAN_KITCHEN_IN2_PIN, "Quat Nha Bep"},
};

bool fanStates[static_cast<uint8_t>(FanId::Count)] = {};

const FanConfig &configFor(FanId id) {
  return FANS[static_cast<uint8_t>(id)];
}
}

void fanMotorBegin() {
  for (const FanConfig &fan : FANS) {
    pinMode(fan.in1Pin, OUTPUT);
    pinMode(fan.in2Pin, OUTPUT);
    digitalWrite(fan.in1Pin, LOW);
    digitalWrite(fan.in2Pin, LOW);
    fanStates[static_cast<uint8_t>(fan.id)] = false;
  }
}

void fanMotorSet(FanId id, bool on) {
  const FanConfig &fan = configFor(id);
  fanStates[static_cast<uint8_t>(id)] = on;
  digitalWrite(fan.in1Pin, on ? HIGH : LOW);
  digitalWrite(fan.in2Pin, LOW);

  Serial.print(fan.name);
  Serial.println(on ? ": BAT" : ": TAT");
}

void fanMotorSetAll(bool on) {
  for (const FanConfig &fan : FANS) {
    fanMotorSet(fan.id, on);
  }
}

bool fanMotorIsOn(FanId id) {
  return fanStates[static_cast<uint8_t>(id)];
}

const char *fanMotorName(FanId id) {
  return configFor(id).name;
}

void fanMotorAutoByTemperature(float temperature) {
  fanMotorSet(FanId::Living, temperature >= FAN_ON_TEMPERATURE);
}
