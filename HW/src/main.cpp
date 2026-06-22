#include <Arduino.h>
#include <ArduinoJson.h>
#include <WiFi.h>
#include <WebSocketsClient.h>

#include "Buzzer.h"
#include "DhtSensor.h"
#include "DoorLock.h"
#include "FanMotor.h"
#include "GasSensor.h"
#include "LedLight.h"
#include "Pins.h"
#include "PirSensor.h"

namespace {
constexpr char WIFI_SSID[] = "BA4-1017 5G";
constexpr char WIFI_PASSWORD[] = "1234567?";
constexpr char WS_HOST[] = "wss.caohoangphuc.id.vn";
constexpr uint16_t WS_PORT = 443;
constexpr char WS_PATH[] = "/ws";
constexpr unsigned long WIFI_RETRY_DELAY_MS = 500;
constexpr unsigned long WS_RECONNECT_INTERVAL_MS = 500;
constexpr uint32_t WS_HEARTBEAT_INTERVAL_MS = 30000;
constexpr uint32_t WS_HEARTBEAT_TIMEOUT_MS = 10000;
constexpr uint8_t WS_HEARTBEAT_DISCONNECT_COUNT = 3;
constexpr unsigned long SENSOR_SYNC_INTERVAL_MS = 2000;
constexpr unsigned long GAS_CHECK_INTERVAL_MS = 300;

WebSocketsClient webSocket;
bool webSocketReady = false;
bool sendSensorSnapshotOnConnect = false;
unsigned long lastSensorSyncMs = 0;
unsigned long lastGasCheckMs = 0;
bool gasAlarmLatched = false;

constexpr uint8_t DOOR_TECH_SERVO_INDEX = 4;
constexpr uint8_t DOOR_KITCHEN_SERVO_INDEX = 3;
constexpr uint8_t DOOR_TOILET_SERVO_INDEX = 2;
constexpr uint8_t DOOR_BEDROOM_SERVO_INDEX = 1;
constexpr uint8_t DOOR_MAIN_SERVO_INDEX = 0;

void sendSensorSnapshot();

void setAllLights(bool on) {
  ledLightSetAll(on);
}

void playSirenWithLights() {
  bool lightsOn = false;
  // Hú còi 10 nhịp (khoảng 6 giây)
  for (int i = 0; i < 10; i++) {
    lightsOn = !lightsOn;
    setAllLights(lightsOn);
    buzzerPlayTone(800, 300); // Tần số 800Hz trong 300ms

    lightsOn = !lightsOn;
    setAllLights(lightsOn);
    buzzerPlayTone(1200, 300); // Tần số 1200Hz trong 300ms
  }

  setAllLights(true);
}

void triggerGasAlarmResponse() {
  Serial.println("CANH BAO GAS: mo cua, bat quat, nhay den, phat nhac.");
  sendSensorSnapshot();
  webSocket.loop(); // process websocket tx
  doorLockSetAll(true);
  fanMotorSetSpeedPercent(FanId::Living, 80);
  fanMotorSetSpeedPercent(FanId::Bed, 80);
  fanMotorSetAll(true);
  playSirenWithLights();
}

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
  Serial.println("  2 / 3 : Bat / tat tat ca quat");
  Serial.println("  f / F : Quat tran phong khach bat / tat");
  Serial.println("  q / Q : Quat phong ngu bat / tat");
  Serial.println("  4 / 5 / 6 : Quat PK 35% / 70% / 100%");
  Serial.println("  7 / 8 / 9 : Quat PN 35% / 70% / 100%");
  Serial.println("  o / c : Mo / khoa tat ca servo cua");
  Serial.println("  t : Doc DHT11");
  Serial.println("  m : Doc PIR phong khach");
  Serial.println("  g : Doc MQ2 nha bep");
  Serial.println("  a : Auto 1 lan (DHT->quat PK, PIR->den PK, MQ2->coi)");
  Serial.println("  p : In trang thai");
  Serial.println();
  Serial.println("Dong bo thiet bi qua WebSocket:");
  Serial.print("  WSS: ");
  Serial.print(WS_HOST);
  Serial.print(":");
  Serial.print(WS_PORT);
  Serial.println(WS_PATH);
  Serial.println("-----------------------------------");
}

void setupSerial() {
  Serial.begin(115200);
  Serial.println("Khoi dong he thong Smart Home...");
}

void setupDevices() {
  ledLightBegin();
  fanMotorBegin();
  buzzerBegin();
  dhtSensorBegin();
  pirSensorBegin();
  gasSensorBegin();
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

void applyFanSocketCommand(FanId id, bool status, int speed) {
  if (speed >= 10 && speed <= 100) {
    fanMotorSetSpeedPercent(id, static_cast<uint8_t>(speed));
  }
  fanMotorSet(id, status);
}

void applyDeviceCommand(const char *key, bool status, int speed = 0) {
  if (strcmp(key, "light_hallway") == 0) {
    ledLightSet(LedId::Hall, status);
  } else if (strcmp(key, "light_kitchen") == 0) {
    ledLightSet(LedId::Kitchen, status);
  } else if (strcmp(key, "light_toilet") == 0) {
    ledLightSet(LedId::Bathroom, status);
  } else if (strcmp(key, "light_bedroom") == 0) {
    ledLightSet(LedId::Bedroom, status);
  } else if (strcmp(key, "light_livingroom") == 0) {
    ledLightSet(LedId::Living, status);
  } else if (strcmp(key, "fan") == 0) {
    applyFanSocketCommand(FanId::Living, status, speed);
  } else if (strcmp(key, "fan_bedroom") == 0) {
    applyFanSocketCommand(FanId::Bed, status, speed);
  } else if (strcmp(key, "door_tech") == 0) {
    doorLockSet(DOOR_TECH_SERVO_INDEX, status);
  } else if (strcmp(key, "door_kitchen") == 0) {
    doorLockSet(DOOR_KITCHEN_SERVO_INDEX, status);
  } else if (strcmp(key, "door_toilet") == 0) {
    doorLockSet(DOOR_TOILET_SERVO_INDEX, status);
  } else if (strcmp(key, "door_bedroom") == 0) {
    doorLockSet(DOOR_BEDROOM_SERVO_INDEX, status);
  } else if (strcmp(key, "door") == 0) {
    doorLockSet(DOOR_MAIN_SERVO_INDEX, status);
  } else if (strcmp(key, "door_all") == 0) {
    doorLockSet(status);
  } else {
    Serial.print("Bo qua key khong ho tro: ");
    Serial.println(key);
  }
}

void sendSensorSnapshot() {
  if (!webSocketReady) {
    return;
  }

  ClimateData climate{};
  if (!dhtSensorRead(climate)) {
    Serial.println("Bo qua sensor sync: khong doc duoc DHT.");
    return;
  }

  const bool motion = pirSensorRead();
  const GasData gas = gasSensorRead();

  JsonDocument doc;
  doc["event"] = "sensor.sync";
  JsonObject data = doc["data"].to<JsonObject>();
  data["temperature"] = climate.temperature;
  data["humidity"] = climate.humidity;
  data["pir"] = motion;
  data["gas_ppm"] = gas.ppm;
  data["gas_alarm"] = gas.digitalAlarm;

  String payload;
  serializeJson(doc, payload);
  webSocket.sendTXT(payload);
  lastSensorSyncMs = millis();

  Serial.print("Da gui sensor sync: ");
  Serial.println(payload);
}

void applySocketPayload(uint8_t *payload, size_t length) {
  JsonDocument doc;
  DeserializationError error = deserializeJson(doc, payload, length);
  if (error) {
    Serial.print("JSON khong hop le: ");
    Serial.println(error.c_str());
    return;
  }

  const char *eventName = doc["event"];
  if (!eventName || strcmp(eventName, "device.sync") != 0) {
    return;
  }

  JsonArray commands = doc["data"]["commands"].as<JsonArray>();
  if (commands.isNull()) {
    Serial.println("Khong co commands trong payload.");
    return;
  }

  const bool fullState = doc["data"]["full_state"] | false;
  Serial.println(fullState ? "Nhan full_state tu server." : "Nhan delta state tu server.");

  for (JsonObject command : commands) {
    const char *key = command["key"];
    const bool status = command["status"] | false;
    const int speed = command["speed"] | 0;
    if (!key) {
      continue;
    }
    Serial.print("WS command -> ");
    Serial.print(key);
    Serial.print(": ");
    Serial.println(status ? "BAT/MO" : "TAT/KHOA");
    if (speed > 0) {
      Serial.print("  Toc do quat: ");
      Serial.print(speed);
      Serial.println("%");
    }
    applyDeviceCommand(key, status, speed);
  }
}

void onWebSocketEvent(WStype_t type, uint8_t *payload, size_t length) {
  switch (type) {
    case WStype_DISCONNECTED:
      webSocketReady = false;
      Serial.print("WebSocket da ngat ket noi");
      if (payload && length > 0) {
        Serial.print(": ");
        Serial.write(payload, length);
      }
      Serial.println();
      break;
    case WStype_CONNECTED:
      webSocketReady = true;
      sendSensorSnapshotOnConnect = true;
      Serial.print("WebSocket da ket noi: ");
      Serial.println(reinterpret_cast<const char *>(payload));
      break;
    case WStype_TEXT:
      applySocketPayload(payload, length);
      break;
    case WStype_ERROR:
      Serial.println("WebSocket gap loi.");
      break;
    default:
      break;
  }
}

void setupWebSocket() {
  Serial.print("Dang ket noi WebSocket WSS: ");
  Serial.print(WS_HOST);
  Serial.print(":");
  Serial.println(WS_PORT);

  webSocket.beginSSL(WS_HOST, WS_PORT, WS_PATH);
  webSocket.setReconnectInterval(WS_RECONNECT_INTERVAL_MS);
  webSocket.enableHeartbeat(
      WS_HEARTBEAT_INTERVAL_MS,
      WS_HEARTBEAT_TIMEOUT_MS,
      WS_HEARTBEAT_DISCONNECT_COUNT);
  webSocket.onEvent(onWebSocketEvent);
}

void readAndPrintDht() {
  ClimateData climate{};
  if (!dhtSensorRead(climate)) {
    Serial.println("Loi: Khong the doc DHT!");
    return;
  }

  dhtSensorPrint(climate);
}

void readAndPrintPir() {
  const bool motion = pirSensorRead();
  pirSensorPrint(motion);
}

void readAndPrintGas() {
  const GasData gas = gasSensorRead();
  gasSensorPrint(gas);
  if (gas.digitalAlarm) {
    triggerGasAlarmResponse();
  }
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
  if (gas.digitalAlarm) {
    triggerGasAlarmResponse();
  }
}

void handleGasAlarm() {
  const unsigned long now = millis();
  if (now - lastGasCheckMs < GAS_CHECK_INTERVAL_MS) {
    return;
  }
  lastGasCheckMs = now;

  const GasData gas = gasSensorRead();
  if (gas.digitalAlarm) {
    if (!gasAlarmLatched) {
      gasAlarmLatched = true;
      triggerGasAlarmResponse();
    }
    return;
  }

  gasAlarmLatched = false;
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
    if (fanMotorIsOn(id)) {
      Serial.print("BAT ");
      Serial.print(fanMotorSpeedPercent(id));
      Serial.println("%");
    } else {
      Serial.print("TAT (");
      Serial.print(fanMotorSpeedPercent(id));
      Serial.println("%)");
    }
  }

  Serial.println("Trang thai cua servo:");
  for (uint8_t i = 0; i < IotPins::SERVO_COUNT; i++) {
    Serial.print("  Cua S");
    Serial.print(i + 1);
    Serial.print(": ");
    Serial.println(doorLockIsOpen(i) ? "MO" : "KHOA");
  }
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
      ledLightSet(LedId::Bedroom, true);
      break;
    case 'B':
      ledLightSet(LedId::Bedroom, false);
      break;
    case 'w':
      ledLightSet(LedId::Bathroom, true);
      break;
    case 'W':
      ledLightSet(LedId::Bathroom, false);
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
    case '2':
      fanMotorSetAll(true);
      break;
    case '3':
      fanMotorSetAll(false);
      break;
    case '4':
      fanMotorSetSpeedPercent(FanId::Living, 35);
      break;
    case '5':
      fanMotorSetSpeedPercent(FanId::Living, 70);
      break;
    case '6':
      fanMotorSetSpeedPercent(FanId::Living, 100);
      break;
    case '7':
      fanMotorSetSpeedPercent(FanId::Bed, 35);
      break;
    case '8':
      fanMotorSetSpeedPercent(FanId::Bed, 70);
      break;
    case '9':
      fanMotorSetSpeedPercent(FanId::Bed, 100);
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
  if (WiFi.status() != WL_CONNECTED) {
    webSocketReady = false;
    return;
  }
  webSocket.loop();
  if (sendSensorSnapshotOnConnect && webSocketReady) {
    sendSensorSnapshotOnConnect = false;
    sendSensorSnapshot();
    return;
  }

  const unsigned long now = millis();
  if (webSocketReady && (lastSensorSyncMs == 0 || now - lastSensorSyncMs >= SENSOR_SYNC_INTERVAL_MS)) {
    sendSensorSnapshot();
  }
}
}

void setup() {
  setupSerial();
  setupDevices();
  setupWifi();
  setupWebSocket();

  Serial.println("=> San sang!");
  printHelp();
}

void loop() {
  handleSerialCommands();
  handleSocketCommands();
  handleGasAlarm();
  delay(10);
}
