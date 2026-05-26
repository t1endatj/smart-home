from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import sqlite3
import os
import json
import httpx
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Smart Home API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "sensor_data.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sensor_logs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            temperature REAL NOT NULL,
            humidity    REAL NOT NULL,
            timestamp   TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

class SensorData(BaseModel):
    temperature: float
    humidity: float

@app.post("/api/sensor")
def receive_sensor(data: SensorData):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO sensor_logs (temperature, humidity, timestamp) VALUES (?, ?, ?)",
        (data.temperature, data.humidity, ts)
    )
    conn.commit()
    conn.close()
    print(f"[{ts}] Nhiet do: {data.temperature}°C  |  Do am: {data.humidity}%")
    return {"status": "ok", "timestamp": ts}

@app.get("/api/sensor")
def get_sensor(limit: int = 20):
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT temperature, humidity, timestamp FROM sensor_logs ORDER BY id DESC LIMIT ?",
        (limit,)
    ).fetchall()
    conn.close()
    return [
        {"temperature": r[0], "humidity": r[1], "timestamp": r[2]}
        for r in rows
    ]

@app.get("/api/sensor/latest")
def get_latest():
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT temperature, humidity, timestamp FROM sensor_logs ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()
    if row is None:
        return {"message": "Chưa có dữ liệu"}
    return {"temperature": row[0], "humidity": row[1], "timestamp": row[2]}

class ControlData(BaseModel):
    device: str
    status: bool

@app.post("/api/control")
def control_device(data: ControlData):
    print(f"Dieu khien: {data.device} -> {'BAT' if data.status else 'TAT'}")
    return {"status": "ok", "device": data.device, "value": data.status}

class AICommandRequest(BaseModel):
    command: str

SYSTEM_PROMPT = """Bạn là trợ lý AI điều khiển nhà thông minh. Nhiệm vụ của bạn là phân tích câu lệnh tiếng Việt của người dùng và chuyển thành các hành động điều khiển thiết bị hoặc kích hoạt kịch bản tương ứng dưới dạng JSON.

HỆ THỐNG THIẾT BỊ HỢP LỆ (chỉ được sử dụng chính xác các tên thiết bị sau, viết hoa đúng từng chữ):
- Đèn: 'Đèn Hành Lang', 'Đèn Phòng Ngủ', 'Đèn Nhà Vệ Sinh', 'Đèn Chùm Trung Tâm', 'Đèn Nhà Bếp', 'Đèn Khu KT'.
- Quạt: 'Quạt Phòng Ngủ', 'Quạt Trần Phòng Khách', 'Quạt Nhà Bếp'.
- Cửa/Khóa: 'Cửa Chính', 'Cửa Nhà Vệ Sinh', 'Cửa Phòng Ngủ', 'Cửa Nhà Bếp', 'Cửa Khu KT'.

KỊCH BẢN HỢP LỆ (chỉ được sử dụng các mã kịch bản sau, viết thường):
- 'welcome': Cảnh về nhà, vào nhà.
- 'sleep': Cảnh đi ngủ.
- 'sos': Cảnh báo động khói, khẩn cấp, SOS.
- 'alloff': Cảnh tắt hết thiết bị, đi ra ngoài.

YÊU CẦU ĐẦU RA:
Bạn phải trả về một đối tượng JSON duy nhất có cấu trúc chính xác như sau:
{
  "actions": [
    {"device": "Tên Thiết Bị Hợp Lệ", "status": true/false}
  ],
  "scenario": "mã_kịch_bản_hợp_lệ_hoặc_null",
  "response": "Câu trả lời thân thiện bằng tiếng Việt, có dấu, mô tả ngắn gọn những gì bạn đã làm."
}

QUY TẮC PHÂN TÍCH:
1. Nếu câu lệnh yêu cầu bật/mở thiết bị, set status = true. Nếu tắt/đóng thiết bị, set status = false.
2. Nếu câu lệnh trùng với kịch bản (ví dụ: "đi ngủ thôi", "kích hoạt cảnh về nhà", "báo động khẩn cấp", "tắt hết đi"), hãy set trường "scenario" tương ứng và để mảng "actions" rỗng.
3. Nếu thiết bị được yêu cầu không nằm trong danh sách thiết bị hợp lệ hoặc câu lệnh không chứa ý định điều khiển, trả về "actions" rỗng, "scenario" null, và "response" giải thích lịch sự bằng tiếng Việt rằng bạn chỉ điều khiển được các thiết bị nhà thông minh trong danh sách.
4. Phản hồi "response" phải ngắn gọn, tự nhiên, không quá dài dòng để tránh tràn màn hình.
"""

@app.post("/api/ai/command")
async def ai_command(data: AICommandRequest):
    grok_key = os.getenv("GROK_API_KEY", "")
    grok_url = os.getenv("GROK_API_URL", "https://api.xai.com/v1/chat/completions")
    grok_model = os.getenv("GROK_MODEL", "grok-2-1212")
    
    if not grok_key or grok_key == "YOUR_GROK_API_KEY_HERE" or grok_key.strip() == "":
        return {
            "actions": [],
            "scenario": None,
            "response": "Lỗi cấu hình: Chưa nhập API Key cho Grok trong file .env ở Backend."
        }
        
    headers = {
        "Authorization": f"Bearer {grok_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": grok_model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": data.command}
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(grok_url, headers=headers, json=payload)
            if response.status_code != 200:
                print(f"Grok API Error: Status {response.status_code}, Body: {response.text}")
                return {
                    "actions": [],
                    "scenario": None,
                    "response": f"Lỗi kết nối API Grok (Mã lỗi: {response.status_code})."
                }
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            parsed_result = json.loads(content)
            return parsed_result
            
    except Exception as e:
        print(f"Exception during AI parsing: {str(e)}")
        return {
            "actions": [],
            "scenario": None,
            "response": f"Đã xảy ra lỗi khi xử lý câu lệnh bằng AI: {str(e)}"
        }