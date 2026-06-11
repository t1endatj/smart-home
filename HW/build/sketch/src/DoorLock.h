#line 1 "/tmp/Smart_Home_HardW-cli/Smart_Home_HardW/src/DoorLock.h"
#pragma once

#include <Arduino.h>

void doorLockBegin();
void doorLockSet(bool open);
void doorLockSet(uint8_t index, bool open);
void doorLockSetAll(bool open);
bool doorLockIsOpen();
bool doorLockIsOpen(uint8_t index);
