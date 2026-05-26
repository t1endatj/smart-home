#line 1 "/home/phuchoangsrc/smart-home/Smart_Home_HardW/src/DoorLock.h"
#pragma once

#include <Arduino.h>

void doorLockBegin();
void doorLockSet(bool open);
bool doorLockIsOpen();
