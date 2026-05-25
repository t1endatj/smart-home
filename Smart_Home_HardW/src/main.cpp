#include <Arduino.h>
#include <WiFi.h>
#include <WiFiClient.h>

#include "DhtSensor.h"
#include "DoorLock.h"
#include "FanMotor.h"
#include "GasSensor.h"
#include "LedLight.h"
#include "OledDashboard.h"
#include "Pins.h"
#include "PirSensor.h"

namespace {
constexpr char WIFI_SSID[] = "Wokwi-GUEST";
constexpr char WIFI_PASSWORD[] = "";
constexpr char COMMAND_SERVER_HOST[] = "host.wokwi.internal";
constexpr uint16_t COMMAND_SERVER_PORT = 5001;
constexpr unsigned long WIFI_RETRY_DELAY_MS = 500;
constexpr unsigned long SOCKET_RECONNECT_INTERVAL_MS = 3000;

WiFiClient commandSocket;
unsigned long lastSocketConnectAttemptMs = 0;

void printHelp() {
  Serial.println();
  Serial.println("Lenh test theo diagram.json:");
  Serial.println("  ? : In menu lenh");
  Serial.println("  1 / 0 : Bat / tat tat ca den");
  Serial.println("  h / H : Den hanh lang bat / tat");
  Serial.println("  b / B : Den phong ngu bat / tat");
  Serial.println("  w / W : Den nha ve sinh bat / tat");
  Serial.println("  v / V : Den phong khach bat / tat");
  Serial.println("  k / K : Den nha bep bat / tat");
  Serial.println("  e / E : Den khu ky thuat bat / tat");
  Serial.println("  2 / 3 : Bat / tat tat ca quat");
  Serial.println("  q / Q : Quat phong ngu bat / tat");
  Serial.println("  f / F : Quat tran phong khach bat / tat");
  Serial.println("  n / N : Quat nha bep bat / tat");
  Serial.println("  o / c : Mo / khoa servo cua chinh");
  Serial.println("  t : Doc DHT11 phong khach (Wokwi DHT22)");
  Serial.println("  m : Doc PIR phong khach");
  Serial.println("  g : Doc MQ2 nha bep");
  Serial.println("  u : OLED hien chu test");
  Serial.println("  x : OLED hien pattern test");
  Serial.println("  z : OLED clear");
  Serial.println("  y / Y : OLED bat / tat");
  Serial.println("  a : Auto 1 lan (DHT->quat PK, PIR->den PK, MQ2->quat bep)");
  Serial.println("  p : In trang thai");
  Serial.println();
  Serial.println("Lenh qua server Python:");
  Serial.print("  TCP: ");
  Serial.print(COMMAND_SERVER_HOST);
  Serial.print(":");
  Serial.println(COMMAND_SERVER_PORT);
  Serial.println("  HTTP: POST /command {\"command\":\"1\"} hoac GET /send?cmd=1");
  Serial.println("-----------------------------------");
}

void setupSerial() {
  Serial.begin(115200);
  Serial.println("Khoi dong he thong Smart Home...");
}

void setupDevices() {
  ledLightBegin();
  fanMotorBegin();
  dhtSensorBegin();
  pirSensorBegin();
  gasSensorBegin();
  oledDashboardBegin();
  doorLockBegin();
}

void setupWifi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  Serial.print("Dang ket noi WiFi ");
  Serial.print(WIFI_SSID);
  while (WiFi.status() != WL_CONNECTED) {
    delay(WIFI_RETRY_DELAY_MS);
    Serial.print(".");
  }

  Serial.println();
  Serial.print("WiFi da ket noi. ESP32 IP: ");
  Serial.println(WiFi.localIP());
}

void connectCommandSocket() {
  if (WiFi.status() != WL_CONNECTED || commandSocket.connected()) {
    return;
  }

  const unsigned long now = millis();
  if (lastSocketConnectAttemptMs != 0 &&
      now - lastSocketConnectAttemptMs < SOCKET_RECONNECT_INTERVAL_MS) {
    return;
  }
  lastSocketConnectAttemptMs = now;

  Serial.print("Dang ket noi command server ");
  Serial.print(COMMAND_SERVER_HOST);
  Serial.print(":");
  Serial.println(COMMAND_SERVER_PORT);

  if (commandSocket.connect(COMMAND_SERVER_HOST, COMMAND_SERVER_PORT)) {
    Serial.println("Da ket noi command server.");
    commandSocket.println("ESP32 Smart Home online");
  } else {
    Serial.println("Chua ket noi duoc command server.");
  }
}

void readAndPrintDht() {
  ClimateData climate{};
  if (!dhtSensorRead(climate)) {
    Serial.println("Loi: Khong the doc DHT!");
    return;
  }

  dhtSensorPrint(climate);

  char line[22];
  oledDashboardClear();
  oledDashboardPrintLine(0, "DHT PHONG KHACH");
  snprintf(line, sizeof(line), "TEMP %.1f*C", climate.temperature);
  oledDashboardPrintLine(2, line);
  snprintf(line, sizeof(line), "HUM %.1f%%", climate.humidity);
  oledDashboardPrintLine(4, line);
}

void readAndPrintPir() {
  const bool motion = pirSensorRead();
  pirSensorPrint(motion);
  oledDashboardClear();
  oledDashboardPrintLine(0, "PIR PHONG KHACH");
  oledDashboardPrintLine(2, motion ? "CO CHUYEN DONG" : "KHONG CHUYEN DONG");
}

void readAndPrintGas() {
  const GasData gas = gasSensorRead();
  gasSensorPrint(gas);

  char line[22];
  oledDashboardClear();
  oledDashboardPrintLine(0, "MQ2 NHA BEP");
  snprintf(line, sizeof(line), "AO %d", gas.analogValue);
  oledDashboardPrintLine(2, line);
  oledDashboardPrintLine(4, gas.digitalAlarm ? "DO CANH BAO" : "DO BINH THUONG");
}

void runAutoOnce() {
  ClimateData climate{};
  if (!dhtSensorRead(climate)) {
    Serial.println("Loi: Khong the doc DHT!");
    return;
  }

  dhtSensorPrint(climate);
  fanMotorAutoByTemperature(climate.temperature);

  const bool motion = pirSensorRead();
  pirSensorPrint(motion);
  ledLightSet(LedId::Living, motion);

  const GasData gas = gasSensorRead();
  gasSensorPrint(gas);
  const bool gasAlarm = gas.digitalAlarm || gas.analogValue >= MQ2_ANALOG_ALARM_THRESHOLD;
  fanMotorSet(FanId::Kitchen, gasAlarm);

  char line[22];
  oledDashboardClear();
  oledDashboardPrintLine(0, "AUTO SMART HOME");
  snprintf(line, sizeof(line), "T %.1f*C H %.0f%%", climate.temperature, climate.humidity);
  oledDashboardPrintLine(2, line);
  oledDashboardPrintLine(4, motion ? "PIR CO NGUOI" : "PIR TRONG");
  snprintf(line, sizeof(line), "GAS %d", gas.analogValue);
  oledDashboardPrintLine(6, line);
}

void printStatus() {
  Serial.println("Trang thai den:");
  for (uint8_t i = 0; i < static_cast<uint8_t>(LedId::Count); i++) {
    const LedId id = static_cast<LedId>(i);
    Serial.print("  ");
    Serial.print(ledLightName(id));
    Serial.print(": ");
    Serial.println(ledLightIsOn(id) ? "BAT" : "TAT");
  }

  Serial.println("Trang thai quat:");
  for (uint8_t i = 0; i < static_cast<uint8_t>(FanId::Count); i++) {
    const FanId id = static_cast<FanId>(i);
    Serial.print("  ");
    Serial.print(fanMotorName(id));
    Serial.print(": ");
    Serial.println(fanMotorIsOn(id) ? "BAT" : "TAT");
  }

  Serial.print("Cua: ");
  Serial.println(doorLockIsOpen() ? "MO" : "KHOA");
}

void handleSerialCommand(char cmd) {
  if (cmd == '\n' || cmd == '\r' || cmd == ' ') {
    return;
  }

  Serial.print("Lenh nhan duoc: ");
  Serial.println(cmd);

  switch (cmd) {
    case '?':
      printHelp();
      break;
    case 't':
      readAndPrintDht();
      break;
    case 'm':
      readAndPrintPir();
      break;
    case 'g':
      readAndPrintGas();
      break;
    case 'a':
      runAutoOnce();
      break;
    case '1':
      ledLightSetAll(true);
      break;
    case '0':
      ledLightSetAll(false);
      break;
    case 'h':
      ledLightSet(LedId::Hall, true);
      break;
    case 'H':
      ledLightSet(LedId::Hall, false);
      break;
    case 'b':
      ledLightSet(LedId::Bed, true);
      break;
    case 'B':
      ledLightSet(LedId::Bed, false);
      break;
    case 'w':
      ledLightSet(LedId::Wc, true);
      break;
    case 'W':
      ledLightSet(LedId::Wc, false);
      break;
    case 'v':
      ledLightSet(LedId::Living, true);
      break;
    case 'V':
      ledLightSet(LedId::Living, false);
      break;
    case 'k':
      ledLightSet(LedId::Kitchen, true);
      break;
    case 'K':
      ledLightSet(LedId::Kitchen, false);
      break;
    case 'e':
      ledLightSet(LedId::Tech, true);
      break;
    case 'E':
      ledLightSet(LedId::Tech, false);
      break;
    case '2':
      fanMotorSetAll(true);
      break;
    case '3':
      fanMotorSetAll(false);
      break;
    case 'o':
      doorLockSet(true);
      break;
    case 'c':
      doorLockSet(false);
      break;
    case 'f':
      fanMotorSet(FanId::Living, true);
      break;
    case 'F':
      fanMotorSet(FanId::Living, false);
      break;
    case 'q':
      fanMotorSet(FanId::Bed, true);
      break;
    case 'Q':
      fanMotorSet(FanId::Bed, false);
      break;
    case 'n':
      fanMotorSet(FanId::Kitchen, true);
      break;
    case 'N':
      fanMotorSet(FanId::Kitchen, false);
      break;
    case 'u':
      oledDashboardShowTextDemo();
      break;
    case 'x':
      oledDashboardShowPattern();
      break;
    case 'z':
      oledDashboardClear();
      Serial.println("OLED Dashboard: clear");
      break;
    case 'y':
      oledDashboardSetDisplayOn(true);
      break;
    case 'Y':
      oledDashboardSetDisplayOn(false);
      break;
    case 'p':
      printStatus();
      break;
    default:
      Serial.println("Lenh khong hop le. Gui '?' de xem menu.");
      break;
  }
}

void handleSerialCommands() {
  while (Serial.available()) {
    handleSerialCommand(Serial.read());
  }
}

void handleSocketCommands() {
  connectCommandSocket();

  while (commandSocket.connected() && commandSocket.available()) {
    const char cmd = static_cast<char>(commandSocket.read());
    if (cmd == '\n' || cmd == '\r') {
      continue;
    }

    Serial.print("Lenh socket: ");
    Serial.println(cmd);
    handleSerialCommand(cmd);
  }
}
}

void setup() {
  setupSerial();
  setupDevices();
  setupWifi();
  connectCommandSocket();

  Serial.println("=> San sang!");
  printHelp();
}

void loop() {
  handleSerialCommands();
  handleSocketCommands();
  delay(10);
}
