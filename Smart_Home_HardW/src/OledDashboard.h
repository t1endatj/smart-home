#pragma once

#include <Arduino.h>

void oledDashboardBegin();
void oledDashboardClear();
void oledDashboardPrintLine(uint8_t line, const char *text);
void oledDashboardShowPattern();
void oledDashboardShowTextDemo();
void oledDashboardSetDisplayOn(bool on);
