#line 1 "/tmp/Smart_Home_HardW-cli/Smart_Home_HardW/src/FanMotor.cpp"
#include "FanMotor.h"

#include <esp32-hal-ledc.h>

#include "./Pins.h"

namespace {
struct FanConfig {
  FanId id;
  uint8_t enPin;
  uint8_t in1Pin;
  uint8_t in2Pin;
  uint8_t pwmChannel;
  const char *name;
};

constexpr FanConfig FANS[] = {
    {FanId::Living, IotPins::LIVING_ROOM_FAN_EN_PIN, IotPins::LIVING_ROOM_FAN_IN1_PIN,
     IotPins::LIVING_ROOM_FAN_IN2_PIN, 0, "Quat Phong Khach"},
    {FanId::Bed, IotPins::BEDROOM_FAN_EN_PIN, IotPins::BEDROOM_FAN_IN1_PIN,
     IotPins::BEDROOM_FAN_IN2_PIN, 1, "Quat Phong Ngu"},
};

bool fanStates[static_cast<uint8_t>(FanId::Count)] = {};
uint8_t fanSpeedPercents[static_cast<uint8_t>(FanId::Count)] = {};

uint8_t clampPercent(uint8_t percent) {
  if (percent < 10) {
    return 10;
  }
  if (percent > 100) {
    return 100;
  }
  return percent;
}

uint8_t dutyForPercent(uint8_t percent) {
  const uint8_t clamped = clampPercent(percent);
  return static_cast<uint8_t>((static_cast<uint16_t>(clamped) * 255U) / 100U);
}

const FanConfig &configFor(FanId id) {
  return FANS[static_cast<uint8_t>(id)];
}
}

void fanMotorBegin() {
  for (const FanConfig &fan : FANS) {
    pinMode(fan.enPin, OUTPUT);
    pinMode(fan.in1Pin, OUTPUT);
    pinMode(fan.in2Pin, OUTPUT);
    ledcAttachChannel(
        fan.enPin, IotPins::FAN_PWM_FREQ, IotPins::FAN_PWM_RESOLUTION, fan.pwmChannel);
    ledcWriteChannel(fan.pwmChannel, 0);
    digitalWrite(fan.in1Pin, LOW);
    digitalWrite(fan.in2Pin, LOW);
    fanStates[static_cast<uint8_t>(fan.id)] = false;
    fanSpeedPercents[static_cast<uint8_t>(fan.id)] = 35;
  }
}

void fanMotorSet(FanId id, bool on) {
  const FanConfig &fan = configFor(id);
  const uint8_t speedPercent = fanSpeedPercents[static_cast<uint8_t>(id)];
  fanStates[static_cast<uint8_t>(id)] = on;
  if (on) {
    digitalWrite(fan.in1Pin, HIGH);
    digitalWrite(fan.in2Pin, LOW);
    ledcWriteChannel(fan.pwmChannel, dutyForPercent(speedPercent));
  } else {
    digitalWrite(fan.in1Pin, LOW);
    digitalWrite(fan.in2Pin, LOW);
    ledcWriteChannel(fan.pwmChannel, 0);
  }

  Serial.print(fan.name);
  if (on) {
    Serial.print(": BAT ");
    Serial.print(speedPercent);
    Serial.println("%");
  } else {
    Serial.println(": TAT");
  }
}

void fanMotorSetAll(bool on) {
  for (const FanConfig &fan : FANS) {
    fanMotorSet(fan.id, on);
  }
}

void fanMotorSetSpeedPercent(FanId id, uint8_t percent) {
  fanSpeedPercents[static_cast<uint8_t>(id)] = clampPercent(percent);

  Serial.print(configFor(id).name);
  Serial.print(": chuyen sang ");
  Serial.print(fanSpeedPercents[static_cast<uint8_t>(id)]);
  Serial.println("%");

  if (fanMotorIsOn(id)) {
    fanMotorSet(id, true);
  }
}

bool fanMotorIsOn(FanId id) {
  return fanStates[static_cast<uint8_t>(id)];
}

uint8_t fanMotorSpeedPercent(FanId id) {
  return fanSpeedPercents[static_cast<uint8_t>(id)];
}

const char *fanMotorName(FanId id) {
  return configFor(id).name;
}

void fanMotorAutoByTemperature(float temperature) {
  fanMotorSet(FanId::Living, temperature >= IotPins::FAN_ON_TEMPERATURE);
}
