#line 1 "/tmp/Smart_Home_HardW-cli/Smart_Home_HardW/src/Buzzer.cpp"
#include "Buzzer.h"

#include <esp32-hal-ledc.h>

#include "./Pins.h"

namespace {
bool buzzerReady = false;
}

void buzzerBegin() {
  buzzerReady = ledcAttach(IotPins::BUZZER_PIN, 2000, 8);
  if (!buzzerReady) {
    Serial.println("Buzzer: khong the khoi tao PWM");
    return;
  }
  ledcWriteTone(IotPins::BUZZER_PIN, 0);
}

void buzzerBeep(uint32_t durationMs, uint32_t frequencyHz) {
  buzzerPlayTone(frequencyHz, durationMs);
}

void buzzerPlayTone(uint32_t frequencyHz, uint32_t durationMs) {
  if (!buzzerReady) {
    return;
  }

  ledcWriteTone(IotPins::BUZZER_PIN, frequencyHz);
  delay(durationMs);
  ledcWriteTone(IotPins::BUZZER_PIN, 0);
}
