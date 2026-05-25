#line 1 "/home/phuchoangsrc/smart-home/Smart_Home_HardW/src/DoorLock.cpp"
#include "DoorLock.h"

#include <ESP32Servo.h>

#include "Pins.h"

namespace {
Servo doorLockServo;
bool doorOpen = false;
}

void doorLockBegin() {
  doorLockServo.attach(SERVO_PIN);
  doorLockSet(false);
}

void doorLockSet(bool open) {
  doorOpen = open;
  doorLockServo.write(open ? 90 : 0);
  Serial.println(open ? "Cua: MO" : "Cua: KHOA");
}

bool doorLockIsOpen() {
  return doorOpen;
}
