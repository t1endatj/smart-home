#pragma once

#include <Arduino.h>

void doorLockBegin();
void doorLockSet(bool open);
bool doorLockIsOpen();
