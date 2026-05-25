#include <Arduino.h>
#include <DHT.h>
#include <ESP32Servo.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

#define DHTPIN 15
#define DHTTYPE DHT22
#define FAN_PIN 2
#define SERVO_PIN 13

// Thông tin mạng WiFi mô phỏng của Wokwi (Mặc định không có pass)
const char* ssid = "Wokwi-GUEST";
const char* password = "";

// ĐỊA CHỈ API CỦA FASTAPI (Thay 192.168.1.X bằng IP máy tính của bạn)
const char* serverName = "http://192.168.1.159:8000/api/sensor";

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

  // --- KẾT NỐI WIFI ---
  WiFi.begin(ssid, password);
  Serial.print("Dang ket noi WiFi");
  while(WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n=> Da ket noi WiFi thanh cong!");
  Serial.print("IP cua ESP32: ");
  Serial.println(WiFi.localIP());
  Serial.println("-----------------------------------");
}

void loop() {
  delay(5000); // Gửi dữ liệu mỗi 5 giây (Trong thực tế nên để 5 phút)

  float t = dht.readTemperature();
  float h = dht.readHumidity();

  if (isnan(t) || isnan(h)) {
    Serial.println("Loi: Khong the doc du lieu tu DHT!");
    return;
  }

  Serial.print("Nhiet do: "); Serial.print(t); Serial.print(" *C  |  ");
  Serial.print("Do am: "); Serial.print(h); Serial.println(" %");

  // Xử lý quạt nội bộ
  if (t >= 35.0) {
    digitalWrite(FAN_PIN, HIGH);
  } else {
    digitalWrite(FAN_PIN, LOW);
  }

  // --- GỬI DỮ LIỆU LÊN FASTAPI CHỈ KHI CÓ WIFI ---
  if(WiFi.status() == WL_CONNECTED){
    HTTPClient http;
    http.begin(serverName); // Mở kết nối tới FastAPI
    http.addHeader("Content-Type", "application/json"); // Báo cho server biết mình gửi JSON

    // Đóng gói dữ liệu thành JSON
    JsonDocument doc; 
    doc["temperature"] = t;
    doc["humidity"] = h;
    String requestBody;
    serializeJson(doc, requestBody);

    // Gửi phương thức POST
    int httpResponseCode = http.POST(requestBody);

    if (httpResponseCode > 0) {
      Serial.print("=> Gui data len Server thanh cong. Ma phan hoi: ");
      Serial.println(httpResponseCode);
      // Bạn có thể in ra nội dung server trả về:
      // String response = http.getString();
      // Serial.println(response);
    } else {
      Serial.print("=> Loi gui data: ");
      Serial.println(httpResponseCode);
    }
    
    http.end(); // Đóng kết nối
  } else {
    Serial.println("=> Mat ket noi WiFi");
  }
}