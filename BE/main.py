from datetime import datetime
import json
import os
import sqlite3
from typing import Optional

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

app = FastAPI(title="Smart Home API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "sensor_data.db"

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

GROK_API_URL = os.environ.get("GROK_API_URL") or os.environ.get("XAI_API_URL") or "https://api.x.ai/v1/chat/completions"
GROK_MODEL = os.environ.get("GROK_MODEL") or os.environ.get("XAI_MODEL") or "grok-4-1-fast-non-reasoning"
GROK_API_KEY = os.environ.get("GROK_API_KEY") or os.environ.get("XAI_API_KEY") or ""

VALID_DEVICE_NAMES = {
    "Đèn Hành Lang",
    "Đèn Phòng Ngủ",
    "Đèn Nhà Vệ Sinh",
    "Đèn Chùm Trung Tâm",
    "Đèn Nhà Bếp",
    "Đèn Khu KT",
    "Quạt Phòng Ngủ",
    "Quạt Trần Phòng Khách",
    "Quạt Nhà Bếp",
    "Cửa Chính",
    "Cửa Nhà Vệ Sinh",
    "Cửa Phòng Ngủ",
    "Cửa Nhà Bếp",
    "Cửa Khu KT",
}

AI_SYSTEM_PROMPT = """
Bạn là trợ lý điều khiển nhà thông minh bằng tiếng Việt.
Nhiệm vụ: chuyển yêu cầu người dùng thành các hành động điều khiển thiết bị trong dashboard.
Chỉ trả về JSON hợp lệ, không markdown, không giải thích dài dòng.

Danh sách thiết bị hợp lệ (đúng chính tả):
- Đèn Hành Lang
- Đèn Phòng Ngủ
- Đèn Nhà Vệ Sinh
- Đèn Chùm Trung Tâm
- Đèn Nhà Bếp
- Đèn Khu KT
- Quạt Phòng Ngủ
- Quạt Trần Phòng Khách
- Quạt Nhà Bếp
- Cửa Chính
- Cửa Nhà Vệ Sinh
- Cửa Phòng Ngủ
- Cửa Nhà Bếp
- Cửa Khu KT

Quy ước:
- status=true nghĩa là BẬT/MỞ, status=false nghĩa là TẮT/ĐÓNG.
- Nếu người dùng nói "tắt hết", "đi ngủ", "về nhà", có thể set scenario là: "alloff" | "sleep" | "welcome".
- Nếu không chắc chắn hoặc không liên quan nhà thông minh: actions=[] và scenario=null.

Schema:
{
  "response": "câu trả lời ngắn (<= 2 câu)",
  "actions": [{"device": "Tên thiết bị", "status": true}],
  "scenario": null
}
""".strip()

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sensor_logs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            temperature REAL NOT NULL,
            humidity    REAL NOT NULL,
            pir         INTEGER,
            gas_ppm     REAL,
            timestamp   TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS home_state (
            id         INTEGER PRIMARY KEY CHECK (id = 1),
            payload    TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            revision   INTEGER NOT NULL DEFAULT 0
        )
    """)

    # Backward-compatible migrations for older DB files.
    try:
        conn.execute("ALTER TABLE sensor_logs ADD COLUMN pir INTEGER")
    except sqlite3.OperationalError:
        pass
    try:
        conn.execute("ALTER TABLE sensor_logs ADD COLUMN gas_ppm REAL")
    except sqlite3.OperationalError:
        pass
    try:
        conn.execute(
            "ALTER TABLE home_state ADD COLUMN revision INTEGER NOT NULL DEFAULT 0"
        )
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()

init_db()

class SensorData(BaseModel):
    temperature: float
    humidity: float
    pir: Optional[bool] = None
    gas_ppm: Optional[float] = None

@app.post("/api/sensor")
def receive_sensor(data: SensorData):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO sensor_logs (temperature, humidity, pir, gas_ppm, timestamp) VALUES (?, ?, ?, ?, ?)",
        (
            data.temperature,
            data.humidity,
            None if data.pir is None else int(bool(data.pir)),
            data.gas_ppm,
            ts,
        )
    )
    conn.commit()
    conn.close()
    print(
        f"[{ts}] Nhiet do: {data.temperature}°C  |  Do am: {data.humidity}%"
        f"  |  PIR: {data.pir}  |  Gas: {data.gas_ppm}"
    )
    return {
        "status": "ok",
        "timestamp": ts,
        "pir": data.pir,
        "gas_ppm": data.gas_ppm,
    }

@app.get("/api/sensor")
def get_sensor(limit: int = 20):
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT temperature, humidity, pir, gas_ppm, timestamp FROM sensor_logs ORDER BY id DESC LIMIT ?",
        (limit,)
    ).fetchall()
    conn.close()
    return [
        {
            "temperature": r[0],
            "humidity": r[1],
            "pir": None if r[2] is None else bool(r[2]),
            "gas_ppm": r[3],
            "timestamp": r[4],
        }
        for r in rows
    ]

@app.get("/api/sensor/latest")
def get_latest():
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT temperature, humidity, pir, gas_ppm, timestamp FROM sensor_logs ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()
    if row is None:
        return {"message": "Chưa có dữ liệu"}
    return {
        "temperature": row[0],
        "humidity": row[1],
        "pir": None if row[2] is None else bool(row[2]),
        "gas_ppm": row[3],
        "timestamp": row[4],
    }

class ControlData(BaseModel):
    device: str
    status: bool

@app.post("/api/control")
def control_device(data: ControlData):
    print(f"Dieu khien: {data.device} -> {'BAT' if data.status else 'TAT'}")
    return {"status": "ok", "device": data.device, "value": data.status}

class AICommandRequest(BaseModel):
    command: str


@app.post("/api/ai/command")
def ai_command(req: AICommandRequest):
    user_text = (req.command or "").strip()
    if not user_text:
        return {"response": "Bạn muốn mình làm gì?", "actions": [], "scenario": None}

    if not GROK_API_KEY:
        return {
            "response": "Chưa cấu hình GROK_API_KEY trên backend.",
            "actions": [],
            "scenario": None,
        }

    messages = [
        {"role": "system", "content": AI_SYSTEM_PROMPT},
        {"role": "user", "content": user_text},
    ]

    try:
        with httpx.Client(timeout=30) as client:
            resp = client.post(
                GROK_API_URL,
                headers={
                    "Authorization": f"Bearer {GROK_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": GROK_MODEL,
                    "messages": messages,
                    "temperature": 0.1,
                    "max_tokens": 200,
                    "response_format": {"type": "json_object"},
                },
            )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"].strip()
        parsed = json.loads(content)
    except Exception as exc:
        return {
            "response": f"Lỗi gọi Grok: {exc}",
            "actions": [],
            "scenario": None,
        }

    response = str(parsed.get("response") or "Đã nhận lệnh.").strip()
    scenario = parsed.get("scenario", None)
    actions = parsed.get("actions", [])
    if not isinstance(actions, list):
        actions = []

    normalized_actions = []
    for action in actions:
        if not isinstance(action, dict):
            continue
        device = str(action.get("device") or "").strip()
        status = action.get("status", None)
        if device not in VALID_DEVICE_NAMES or not isinstance(status, bool):
            continue
        normalized_actions.append({"device": device, "status": status})

    if scenario not in (None, "welcome", "sleep", "sos", "alloff"):
        scenario = None

    return {"response": response, "actions": normalized_actions, "scenario": scenario}


class HomeStatePayload(BaseModel):
    deviceStates: dict
    logs: list | None = None


@app.get("/api/state")
def get_home_state():
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT payload, updated_at, revision FROM home_state WHERE id = 1"
    ).fetchone()
    conn.close()

    if row is None:
        return {"payload": None, "updated_at": None, "revision": 0}

    payload_json, updated_at, revision = row
    try:
        payload = json.loads(payload_json)
    except Exception:
        payload = None
    return {"payload": payload, "updated_at": updated_at, "revision": revision}


@app.post("/api/state")
def set_home_state(data: HomeStatePayload):
    ts = datetime.now().isoformat(timespec="milliseconds")
    payload_json = json.dumps(data.model_dump(), ensure_ascii=False)

    conn = sqlite3.connect(DB_PATH)
    current_revision_row = conn.execute(
        "SELECT revision FROM home_state WHERE id = 1"
    ).fetchone()
    next_revision = (current_revision_row[0] if current_revision_row else 0) + 1
    conn.execute(
        """
        INSERT INTO home_state (id, payload, updated_at, revision)
        VALUES (1, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            payload=excluded.payload,
            updated_at=excluded.updated_at,
            revision=excluded.revision
        """,
        (payload_json, ts, next_revision),
    )
    conn.commit()
    conn.close()
    return {"status": "ok", "updated_at": ts, "revision": next_revision}
