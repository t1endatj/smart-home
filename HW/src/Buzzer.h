#pragma once

#include <Arduino.h>

void buzzerBegin();
void buzzerBeep(uint32_t durationMs = 250, uint32_t frequencyHz = 2200);
void buzzerPlayTone(uint32_t frequencyHz, uint32_t durationMs);
