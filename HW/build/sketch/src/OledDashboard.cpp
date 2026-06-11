#line 1 "/tmp/Smart_Home_HardW-cli/Smart_Home_HardW/src/OledDashboard.cpp"
#include "OledDashboard.h"

#include <Wire.h>

#include "./Pins.h"

namespace {
constexpr uint8_t FONT_WIDTH = 5;
constexpr uint8_t CHAR_WIDTH = 6;
constexpr uint8_t OLED_COLUMNS = 128;
constexpr uint8_t OLED_PAGES = 8;

const uint8_t GLYPH_SPACE[FONT_WIDTH] = {0x00, 0x00, 0x00, 0x00, 0x00};
const uint8_t GLYPH_UNKNOWN[FONT_WIDTH] = {0x7E, 0x09, 0x09, 0x09, 0x06};

const uint8_t *glyphFor(char value) {
  static const uint8_t digits[][FONT_WIDTH] = {
      {0x3E, 0x51, 0x49, 0x45, 0x3E}, {0x00, 0x42, 0x7F, 0x40, 0x00},
      {0x42, 0x61, 0x51, 0x49, 0x46}, {0x21, 0x41, 0x45, 0x4B, 0x31},
      {0x18, 0x14, 0x12, 0x7F, 0x10}, {0x27, 0x45, 0x45, 0x45, 0x39},
      {0x3C, 0x4A, 0x49, 0x49, 0x30}, {0x01, 0x71, 0x09, 0x05, 0x03},
      {0x36, 0x49, 0x49, 0x49, 0x36}, {0x06, 0x49, 0x49, 0x29, 0x1E},
  };
  static const uint8_t letters[][FONT_WIDTH] = {
      {0x7E, 0x11, 0x11, 0x11, 0x7E}, {0x7F, 0x49, 0x49, 0x49, 0x36},
      {0x3E, 0x41, 0x41, 0x41, 0x22}, {0x7F, 0x41, 0x41, 0x22, 0x1C},
      {0x7F, 0x49, 0x49, 0x49, 0x41}, {0x7F, 0x09, 0x09, 0x09, 0x01},
      {0x3E, 0x41, 0x49, 0x49, 0x7A}, {0x7F, 0x08, 0x08, 0x08, 0x7F},
      {0x00, 0x41, 0x7F, 0x41, 0x00}, {0x20, 0x40, 0x41, 0x3F, 0x01},
      {0x7F, 0x08, 0x14, 0x22, 0x41}, {0x7F, 0x40, 0x40, 0x40, 0x40},
      {0x7F, 0x02, 0x0C, 0x02, 0x7F}, {0x7F, 0x04, 0x08, 0x10, 0x7F},
      {0x3E, 0x41, 0x41, 0x41, 0x3E}, {0x7F, 0x09, 0x09, 0x09, 0x06},
      {0x3E, 0x41, 0x51, 0x21, 0x5E}, {0x7F, 0x09, 0x19, 0x29, 0x46},
      {0x46, 0x49, 0x49, 0x49, 0x31}, {0x01, 0x01, 0x7F, 0x01, 0x01},
      {0x3F, 0x40, 0x40, 0x40, 0x3F}, {0x1F, 0x20, 0x40, 0x20, 0x1F},
      {0x7F, 0x20, 0x18, 0x20, 0x7F}, {0x63, 0x14, 0x08, 0x14, 0x63},
      {0x07, 0x08, 0x70, 0x08, 0x07}, {0x61, 0x51, 0x49, 0x45, 0x43},
  };
  static const uint8_t colon[FONT_WIDTH] = {0x00, 0x36, 0x36, 0x00, 0x00};
  static const uint8_t dot[FONT_WIDTH] = {0x00, 0x60, 0x60, 0x00, 0x00};
  static const uint8_t slash[FONT_WIDTH] = {0x20, 0x10, 0x08, 0x04, 0x02};
  static const uint8_t dash[FONT_WIDTH] = {0x08, 0x08, 0x08, 0x08, 0x08};
  static const uint8_t percent[FONT_WIDTH] = {0x23, 0x13, 0x08, 0x64, 0x62};
  static const uint8_t degree[FONT_WIDTH] = {0x02, 0x05, 0x02, 0x00, 0x00};

  if (value >= '0' && value <= '9') {
    return digits[value - '0'];
  }
  if (value >= 'a' && value <= 'z') {
    value -= 32;
  }
  if (value >= 'A' && value <= 'Z') {
    return letters[value - 'A'];
  }

  switch (value) {
    case ' ':
      return GLYPH_SPACE;
    case ':':
      return colon;
    case '.':
      return dot;
    case '/':
      return slash;
    case '-':
      return dash;
    case '%':
      return percent;
    case '*':
      return degree;
    default:
      return GLYPH_UNKNOWN;
  }
}

void writeCommand(uint8_t command) {
  Wire.beginTransmission(IotPins::OLED_I2C_ADDRESS);
  Wire.write(0x00);
  Wire.write(command);
  Wire.endTransmission();
}

void writeData(uint8_t data) {
  Wire.beginTransmission(IotPins::OLED_I2C_ADDRESS);
  Wire.write(0x40);
  Wire.write(data);
  Wire.endTransmission();
}

void setPageAddress(uint8_t page) {
  writeCommand(0xB0 + page);
  writeCommand(0x00);
  writeCommand(0x10);
}

void clearLine(uint8_t line) {
  setPageAddress(line);
  for (uint8_t column = 0; column < OLED_COLUMNS; column++) {
    writeData(0x00);
  }
}
}

void oledDashboardBegin() {
  Wire.begin(IotPins::OLED_SDA_PIN, IotPins::OLED_SCL_PIN);
  delay(50);

  writeCommand(0xAE);
  writeCommand(0x20);
  writeCommand(0x00);
  writeCommand(0x40);
  writeCommand(0xA1);
  writeCommand(0xC8);
  writeCommand(0x81);
  writeCommand(0x7F);
  writeCommand(0xA6);
  writeCommand(0xA8);
  writeCommand(0x3F);
  writeCommand(0xD3);
  writeCommand(0x00);
  writeCommand(0xD5);
  writeCommand(0x80);
  writeCommand(0xD9);
  writeCommand(0xF1);
  writeCommand(0xDA);
  writeCommand(0x12);
  writeCommand(0xDB);
  writeCommand(0x40);
  writeCommand(0x8D);
  writeCommand(0x14);
  writeCommand(0xAF);

  oledDashboardClear();
}

void oledDashboardClear() {
  for (uint8_t page = 0; page < OLED_PAGES; page++) {
    clearLine(page);
  }
}

void oledDashboardPrintLine(uint8_t line, const char *text) {
  if (line >= OLED_PAGES) {
    return;
  }

  clearLine(line);
  setPageAddress(line);

  uint8_t usedColumns = 0;
  while (*text != '\0' && usedColumns + CHAR_WIDTH <= OLED_COLUMNS) {
    const uint8_t *glyph = glyphFor(*text);
    for (uint8_t i = 0; i < FONT_WIDTH; i++) {
      writeData(glyph[i]);
    }
    writeData(0x00);
    usedColumns += CHAR_WIDTH;
    text++;
  }
}

void oledDashboardShowPattern() {
  for (uint8_t page = 0; page < 8; page++) {
    setPageAddress(page);
    for (uint8_t column = 0; column < 128; column++) {
      const bool stripe = ((column / 8) + page) % 2 == 0;
      writeData(stripe ? 0xFF : 0x18);
    }
  }
  Serial.println("OLED Dashboard: hien pattern test");
}

void oledDashboardShowTextDemo() {
  oledDashboardClear();
  oledDashboardPrintLine(0, "SMART HOME");
  oledDashboardPrintLine(2, "DHT PIR MQ2");
  oledDashboardPrintLine(4, "DEN QUAT CUA");
  oledDashboardPrintLine(6, "SERIAL READY");
  Serial.println("OLED Dashboard: hien chu test");
}

void oledDashboardSetDisplayOn(bool on) {
  writeCommand(on ? 0xAF : 0xAE);
  Serial.println(on ? "OLED Dashboard: BAT" : "OLED Dashboard: TAT");
}
