#include <Arduino.h>
#include <DHT.h>
#include <ESP32Servo.h>

#define DHTPIN 15
#define DHTTYPE DHT22
#define FAN_PIN 2
#define SERVO_PIN 13

DHT dht(DHTPIN, DHTTYPE);
Servo doorLock;

void setup() {
  Serial.begin(115200);
  Serial.println("Khoi dong he thong Smart Home...");

  pinMode(FAN_PIN, OUTPUT);
  digitalWrite(FAN_PIN, LOW);
  dht.begin();

  doorLock.attach(SERVO_PIN);
  doorLock.write(0);
  Serial.println("Trang thai khoa cua: DANG DONG");
  Serial.println("-----------------------------------");
}

void loop() {
  delay(2000); // Đợi 2 giây để cảm biến lấy mẫu

  // Đọc nhiệt độ và độ ẩm
  float t = dht.readTemperature();
  float h = dht.readHumidity();

  // Kiểm tra xem có lỗi đọc dữ liệu không
  if (isnan(t) || isnan(h)) {
    Serial.println("Loi: Khong the doc du lieu tu DHT!");
    return;
  }

  // In ra màn hình Terminal theo hàng ngang cho dễ nhìn
  Serial.print("Nhiet do: ");
  Serial.print(t);
  Serial.print(" *C  |  ");
  Serial.print("Do am: ");
  Serial.print(h);
  Serial.println(" %");

  // Logic xử lý cảnh báo
  if (t >= 35.0) {
    digitalWrite(FAN_PIN, HIGH);
    Serial.println("=> CANH BAO: Nhiet do cao. Da bat quat!");
  } else {
    digitalWrite(FAN_PIN, LOW);
  }
}