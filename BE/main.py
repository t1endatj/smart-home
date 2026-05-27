from datetime import datetime
import json
import sqlite3

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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
    conn.execute("""
        CREATE TABLE IF NOT EXISTS home_state (
            id         INTEGER PRIMARY KEY CHECK (id = 1),
            payload    TEXT NOT NULL,
            updated_at TEXT NOT NULL
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


class HomeStatePayload(BaseModel):
    deviceStates: dict
    logs: list | None = None


@app.get("/api/state")
def get_home_state():
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT payload, updated_at FROM home_state WHERE id = 1"
    ).fetchone()
    conn.close()

    if row is None:
        return {"payload": None, "updated_at": None}

    payload_json, updated_at = row
    try:
        payload = json.loads(payload_json)
    except Exception:
        payload = None
    return {"payload": payload, "updated_at": updated_at}


@app.post("/api/state")
def set_home_state(data: HomeStatePayload):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    payload_json = json.dumps(data.model_dump(), ensure_ascii=False)

    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        INSERT INTO home_state (id, payload, updated_at)
        VALUES (1, ?, ?)
        ON CONFLICT(id) DO UPDATE SET payload=excluded.payload, updated_at=excluded.updated_at
        """,
        (payload_json, ts),
    )
    conn.commit()
    conn.close()
    return {"status": "ok", "updated_at": ts}
