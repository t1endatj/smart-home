#line 1 "/tmp/Smart_Home_HardW-cli/Smart_Home_HardW/src/Pins.h"
#pragma once

#include <Arduino.h>

constexpr uint8_t LED_HALL_PIN = 2;
constexpr uint8_t LED_BED_PIN = 4;
constexpr uint8_t LED_WC_PIN = 16;
constexpr uint8_t LED_LIVING_PIN = 17;
constexpr uint8_t LED_KITCHEN_PIN = 18;
constexpr uint8_t LED_TECH_PIN = 19;

constexpr uint8_t SERVO_PIN = 13;

constexpr uint8_t DHT_PIN = 15;
constexpr uint8_t PIR_PIN = 34;

constexpr uint8_t OLED_SDA_PIN = 21;
constexpr uint8_t OLED_SCL_PIN = 22;
constexpr uint8_t OLED_I2C_ADDRESS = 0x3C;

constexpr uint8_t MQ2_AO_PIN = 35;
constexpr uint8_t MQ2_DO_PIN = 32;
constexpr uint16_t MQ2_PPM_ALARM_THRESHOLD = 300;

constexpr uint8_t FAN_BED_IN1_PIN = 25;
constexpr uint8_t FAN_BED_IN2_PIN = 26;
constexpr uint8_t FAN_LIVING_IN1_PIN = 27;
constexpr uint8_t FAN_LIVING_IN2_PIN = 14;
constexpr uint8_t FAN_KITCHEN_IN1_PIN = 12;
constexpr uint8_t FAN_KITCHEN_IN2_PIN = 33;

constexpr uint16_t LDR_THRESHOLD = 2000;
constexpr float FAN_ON_TEMPERATURE = 35.0;
