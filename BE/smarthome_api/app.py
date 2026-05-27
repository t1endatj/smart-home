from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .ai_service import handle_ai_command
from .automation import AutomationEngine
from .config import WS_HOST, WS_PORT
from .realtime import emit_home_state_delta
from .schemas import AICommandRequest, ControlData, HomeStatePayload, SensorData
from .storage import (
    build_full_device_commands,
    get_current_home_payload,
    get_home_state_record,
    get_latest_sensor_snapshot,
    init_db,
    list_sensor_snapshots,
    normalize_sensor_payload,
    save_home_state_payload,
    store_sensor_data,
)
from .websocket_server import WebSocketBroadcastServer


def build_initial_ws_event():
    initial_payload = get_current_home_payload() or {}
    return (
        "device.sync",
        {
            "commands": build_full_device_commands(initial_payload),
            "full_state": True,
        },
    )


app = FastAPI(title="Smart Home API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()


async def handle_ws_event(event: str, data: dict):
    if event == "sensor.sync":
        sensor_payload = normalize_sensor_payload(data)
        if sensor_payload is None:
            return
        store_sensor_data(sensor_payload)
        await ws_server.emit_async("sensor.updated", sensor_payload)
        return

    await ws_server.emit_async(event, {**data, "clients": len(ws_server.clients)})


ws_server = WebSocketBroadcastServer(
    WS_HOST,
    WS_PORT,
    initial_data_factory=build_initial_ws_event,
    incoming_event_handler=handle_ws_event,
)
automation_engine = AutomationEngine(ws_server)


@app.on_event("startup")
def start_services():
    ws_server.start()
    automation_engine.start()


@app.on_event("shutdown")
def stop_services():
    automation_engine.stop()
    ws_server.stop()


@app.post("/api/sensor")
def receive_sensor(data: SensorData):
    sensor_payload = {
        "temperature": data.temperature,
        "humidity": data.humidity,
        "pir": data.pir,
        "gas_ppm": data.gas_ppm,
        "gas_alarm": data.gas_alarm,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    store_sensor_data(sensor_payload)
    ws_server.emit("sensor.updated", sensor_payload)
    return {"status": "ok", **sensor_payload}


@app.get("/api/sensor")
def get_sensor(limit: int = 20):
    return list_sensor_snapshots(limit)


@app.get("/api/sensor/latest")
def get_latest():
    latest = get_latest_sensor_snapshot()
    if latest is None:
        return {"message": "Chưa có dữ liệu"}
    return {
        "temperature": latest["temperature"],
        "humidity": latest["humidity"],
        "pir": latest["pir"],
        "gas_ppm": latest["gas_ppm"],
        "gas_alarm": latest["gas_alarm"],
        "gasAlarm": latest["gas_alarm"],
        "timestamp": latest["timestamp"],
    }


@app.post("/api/control")
def control_device(data: ControlData):
    print(f"Dieu khien: {data.device} -> {'BAT' if data.status else 'TAT'}")
    return {"status": "ok", "device": data.device, "value": data.status}


@app.post("/api/ai/command")
def ai_command(req: AICommandRequest):
    return handle_ai_command(req.command)


@app.get("/api/state")
def get_home_state():
    return get_home_state_record()


@app.post("/api/state")
def set_home_state(data: HomeStatePayload):
    previous_payload = get_current_home_payload() or {}
    payload = data.model_dump()
    updated_at, revision = save_home_state_payload(payload)
    emit_home_state_delta(ws_server, previous_payload, payload, revision, updated_at)
    return {"status": "ok", "updated_at": updated_at, "revision": revision}

