#include <Arduino.h>
#include <DHT.h>
#include <ESP32Servo.h>

#define DHTPIN 15
#define DHTTYPE DHT22

#define LED_PIN 2
#define LDR_PIN 34
#define SERVO_PIN 13
#define MOTOR_PIN 25

#define LDR_THRESHOLD 2000

DHT dht(DHTPIN, DHTTYPE);
Servo doorLock;

bool fanOn = false;
bool doorOpen = false;

void fanControl(bool on) {
  fanOn = on;
  digitalWrite(MOTOR_PIN, on ? HIGH : LOW);
  Serial.println(on ? "Quat: BAT" : "Quat: TAT");
}

void doorControl(bool open) {
  doorOpen = open;
  doorLock.write(open ? 90 : 0);
  Serial.println(open ? "Cua: MO" : "Cua: KHOA");
}

void setup() {
  Serial.begin(115200);
  Serial.println("Khoi dong he thong Smart Home...");

  pinMode(LED_PIN, OUTPUT);
  pinMode(MOTOR_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
  digitalWrite(MOTOR_PIN, LOW);

  dht.begin();

  doorLock.attach(SERVO_PIN);
  doorLock.write(0);

  Serial.println("=> San sang!");
  Serial.println("-----------------------------------");
}

void loop() {
  delay(2000);

  // --- ĐỌC DHT22 ---
  float t = dht.readTemperature();
  float h = dht.readHumidity();

  if (isnan(t) || isnan(h)) {
    Serial.println("Loi: Khong the doc DHT!");
    return;
  }

  Serial.print("Nhiet do: "); Serial.print(t); Serial.print(" *C  |  ");
  Serial.print("Do am: "); Serial.print(h); Serial.println(" %");

  // --- ĐỌC LDR ---
  int ldrValue = analogRead(LDR_PIN);
  Serial.print("Anh sang (LDR): "); Serial.println(ldrValue);

  if (ldrValue < LDR_THRESHOLD) {
    digitalWrite(LED_PIN, HIGH);
    Serial.println("Den: BAT (troi toi)");
  } else {
    digitalWrite(LED_PIN, LOW);
    Serial.println("Den: TAT (troi sang)");
  }

  // --- TỰ ĐỘNG QUẠT THEO NHIỆT ĐỘ ---
  if (t >= 35.0 && !fanOn) {
    fanControl(true);
  } else if (t < 35.0 && fanOn) {
    fanControl(false);
  }

  // --- ĐIỀU KHIỂN QUA SERIAL ---
  if (Serial.available()) {
    char cmd = Serial.read();
    if (cmd == 'o') doorControl(true);
    if (cmd == 'c') doorControl(false);
    if (cmd == 'f') fanControl(true);
    if (cmd == 's') fanControl(false);
  }
}