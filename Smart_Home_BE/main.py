from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import sqlite3

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