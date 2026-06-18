#pragma once

#include <stdint.h>
#include <stddef.h>

namespace IotPins {

// LEDs from blinker/blinker.ino
constexpr uint8_t HALLWAY_LED_PIN = 14;
constexpr uint8_t KITCHEN_LED_PIN = 27;
constexpr uint8_t BATHROOM_LED_PIN = 26;
constexpr uint8_t BEDROOM_LED_PIN = 25;
constexpr uint8_t LIVING_ROOM_LED_PIN = 12;

constexpr uint8_t LED_PINS[] = {
    HALLWAY_LED_PIN,
    KITCHEN_LED_PIN,
    BATHROOM_LED_PIN,
    BEDROOM_LED_PIN,
    LIVING_ROOM_LED_PIN,
};
constexpr size_t LED_COUNT = sizeof(LED_PINS) / sizeof(LED_PINS[0]);

// MQ2 from blinker/blinker.ino
constexpr uint8_t MQ2_ANALOG_PIN = 33;
constexpr int MQ2_GAS_THRESHOLD = 4000;

// Buzzer from buzzer_happy_birthday/buzzer_happy_birthday.ino
constexpr uint8_t BUZZER_PIN = 23;

// DHT from DHT11/DHT11.ino
constexpr uint8_t DHT_PIN = 13;
constexpr uint8_t DHT_TYPE = 11;

// PIR from pir/pir.ino
constexpr uint8_t PIR_PIN = 36;
constexpr bool PIR_ACTIVE_HIGH = true;

// L298N fans from L298N/L298N.ino
constexpr uint8_t LIVING_ROOM_FAN_EN_PIN = 5;
constexpr uint8_t LIVING_ROOM_FAN_IN1_PIN = 18;
constexpr uint8_t LIVING_ROOM_FAN_IN2_PIN = 19;

constexpr uint8_t BEDROOM_FAN_EN_PIN = 4;
constexpr uint8_t BEDROOM_FAN_IN1_PIN = 16;
constexpr uint8_t BEDROOM_FAN_IN2_PIN = 17;

constexpr uint32_t FAN_PWM_FREQ = 1000;
constexpr uint8_t FAN_PWM_RESOLUTION = 8;
constexpr uint8_t FAN_PWM_DUTY_ON = 85;

// PCF8574 servo expander pins from pcf8574_servo_test/pcf8574_servo_test.ino
constexpr uint8_t PCF8574_ADDR = 0x20;
constexpr uint8_t I2C_SDA_PIN = 21;
constexpr uint8_t I2C_SCL_PIN = 22;
constexpr uint8_t OLED_SDA_PIN = I2C_SDA_PIN;
constexpr uint8_t OLED_SCL_PIN = I2C_SCL_PIN;
constexpr uint8_t OLED_I2C_ADDRESS = 0x3C;

constexpr uint8_t SERVO_COUNT = 5;
constexpr uint8_t SERVO_PINS[SERVO_COUNT] = {7, 3, 5, 4, 6};
constexpr int SERVO_OFFSETS[SERVO_COUNT] = {0, 0, 0, 0, 0};

// Door angles currently used in pcf8574_servo_angle_test/pcf8574_servo_angle_test.ino
constexpr int SERVO_CLOSE_ANGLES[SERVO_COUNT] = {8, 50, 10, 8, 8};
constexpr int SERVO_OPEN_ANGLES[SERVO_COUNT] = {98, 140, 100, 98, 98};
constexpr uint16_t SERVO_MOVE_HOLD_FRAMES = 10;
constexpr uint16_t SERVO_MIN_PULSE_US = 500;
constexpr uint16_t SERVO_MAX_PULSE_US = 2500;
constexpr uint32_t SERVO_FRAME_US = 20000;

constexpr float FAN_ON_TEMPERATURE = 35.0f;

}  // namespace IotPins
