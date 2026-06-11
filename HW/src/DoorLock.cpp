#include "DoorLock.h"

#include <Wire.h>

#include "./Pins.h"

namespace {
bool doorStates[IotPins::SERVO_COUNT] = {false, false, false, false};
uint8_t expanderState = 0;
int servoAngles[IotPins::SERVO_COUNT] = {90, 90, 90, 90};
int servoPulses[IotPins::SERVO_COUNT] = {1500, 1500, 1500, 1500};
int activeServo = -2;

bool writeExpanderState() {
  Wire.beginTransmission(IotPins::PCF8574_ADDR);
  Wire.write(expanderState);
  return Wire.endTransmission() == 0;
}

uint16_t angleToPulseMicros(int angle) {
  const int clampedAngle = constrain(angle, 0, 180);
  return static_cast<uint16_t>(
      map(clampedAngle, 0, 180, IotPins::SERVO_MIN_PULSE_US, IotPins::SERVO_MAX_PULSE_US));
}

void setServoAngle(uint8_t index, int angle) {
  if (index >= IotPins::SERVO_COUNT) {
    return;
  }

  const int requestedAngle = constrain(angle, 0, 180);
  const int adjustedAngle =
      constrain(requestedAngle + IotPins::SERVO_OFFSETS[index], 0, 180);

  servoAngles[index] = adjustedAngle;
  servoPulses[index] = angleToPulseMicros(adjustedAngle);
}

void refreshServos() {
  const unsigned long frameStart = micros();

  expanderState = 0x00;

  if (activeServo == -1) {
    for (uint8_t i = 0; i < IotPins::SERVO_COUNT; i++) {
      expanderState |= static_cast<uint8_t>(1U << IotPins::SERVO_PINS[i]);
    }
    writeExpanderState();

    bool done[IotPins::SERVO_COUNT] = {false, false, false, false};
    uint8_t doneCount = 0;

    while (doneCount < IotPins::SERVO_COUNT) {
      const unsigned long elapsed = micros() - frameStart;
      for (uint8_t i = 0; i < IotPins::SERVO_COUNT; i++) {
        if (!done[i] && elapsed >= static_cast<unsigned long>(servoPulses[i])) {
          expanderState &= static_cast<uint8_t>(~(1U << IotPins::SERVO_PINS[i]));
          writeExpanderState();
          done[i] = true;
          doneCount++;
        }
      }
    }
  } else if (activeServo >= 0 && activeServo < IotPins::SERVO_COUNT) {
    expanderState |= static_cast<uint8_t>(1U << IotPins::SERVO_PINS[activeServo]);
    writeExpanderState();

    while (micros() - frameStart < static_cast<unsigned long>(servoPulses[activeServo])) {
    }

    expanderState &= static_cast<uint8_t>(~(1U << IotPins::SERVO_PINS[activeServo]));
    writeExpanderState();
  }

  while (micros() - frameStart < IotPins::SERVO_FRAME_US) {
  }
}

void holdCurrentServo(uint16_t frameCount) {
  for (uint16_t i = 0; i < frameCount; i++) {
    refreshServos();
  }
}

int servoTargetAngle(uint8_t index, bool open) {
  return open ? IotPins::SERVO_OPEN_ANGLES[index] : IotPins::SERVO_CLOSE_ANGLES[index];
}

void moveServoToState(uint8_t index, bool open) {
  if (index >= IotPins::SERVO_COUNT) {
    return;
  }

  doorStates[index] = open;
  setServoAngle(index, servoTargetAngle(index, open));
  activeServo = index;
  holdCurrentServo(IotPins::SERVO_MOVE_HOLD_FRAMES);
  activeServo = -2;
  expanderState = 0x00;
  writeExpanderState();
}
}

void doorLockBegin() {
  Wire.begin(IotPins::I2C_SDA_PIN, IotPins::I2C_SCL_PIN);
  expanderState = 0;
  writeExpanderState();
  for (uint8_t index = 0; index < IotPins::SERVO_COUNT; index++) {
    doorStates[index] = false;
    setServoAngle(index, IotPins::SERVO_CLOSE_ANGLES[index]);
  }
}

void doorLockSet(bool open) {
  doorLockSetAll(open);
}

void doorLockSet(uint8_t index, bool open) {
  moveServoToState(index, open);
  Serial.print("Cua S");
  Serial.print(index + 1);
  Serial.println(open ? ": MO" : ": KHOA");
}

void doorLockSetAll(bool open) {
  for (uint8_t index = 0; index < IotPins::SERVO_COUNT; index++) {
    moveServoToState(index, open);
    delay(60);
  }
  Serial.println(open ? "Tat ca cua: MO" : "Tat ca cua: KHOA");
}

bool doorLockIsOpen() {
  for (uint8_t index = 0; index < IotPins::SERVO_COUNT; index++) {
    if (!doorStates[index]) {
      return false;
    }
  }
  return true;
}

bool doorLockIsOpen(uint8_t index) {
  if (index >= IotPins::SERVO_COUNT) {
    return false;
  }
  return doorStates[index];
}
