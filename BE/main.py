import asyncio
from datetime import datetime
import json
import os
import re
import sqlite3
import threading
from typing import Optional

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from websockets.asyncio.server import serve
from websockets.exceptions import ConnectionClosed

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
WS_HOST = os.environ.get("WS_HOST", "0.0.0.0")
WS_PORT = int(os.environ.get("WS_PORT", "8765"))

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

DEVICE_API_KEYS = {
    "Đèn Hành Lang": "light_hallway",
    "Đèn Phòng Ngủ": "light_bedroom",
    "Đèn Nhà Vệ Sinh": "light_toilet",
    "Đèn Chùm Trung Tâm": "light_livingroom",
    "Đèn Nhà Bếp": "light_kitchen",
    "Đèn Khu KT": "light_tech",
    "Quạt Phòng Ngủ": "fan_bedroom",
    "Quạt Nhà Bếp": "fan_kitchen",
    "Quạt Trần Phòng Khách": "fan",
    "Cửa Chính": "door",
    "Cửa Nhà Vệ Sinh": "door_toilet",
    "Cửa Phòng Ngủ": "door_bedroom",
    "Cửa Nhà Bếp": "door_kitchen",
    "Cửa Khu KT": "door_tech",
}

MAX_CONTEXT_LOGS = 3
MAX_LOG_MESSAGE_LENGTH = 120
MAX_USER_REQUEST_LENGTH = 500

AI_SYSTEM_PROMPT = """
Bạn là bộ não điều phối nhà thông minh bằng tiếng Việt.
Nhiệm vụ của bạn là đọc yêu cầu người dùng cùng trạng thái nhà hiện tại, rồi suy ra các hành động hợp lý, an toàn, tiết kiệm thao tác.
Bạn phải ưu tiên an toàn trước, sau đó là tiện nghi và tính hợp lý theo ngữ cảnh.
Chỉ trả về JSON hợp lệ, không markdown, không thêm chữ ngoài JSON.

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
- Chỉ trả về action cho những thay đổi thực sự cần thiết. Nếu thiết bị đã ở đúng trạng thái mong muốn thì không cần lặp lại.
- Được phép suy luận từ ngữ cảnh và trạng thái nhà hiện tại, không cần bám đúng từng từ người dùng nói.
- Nếu người dùng nói "tắt hết", "đi ngủ", "về nhà", có thể set scenario là: "alloff" | "sleep" | "welcome".
- Nếu tình huống khẩn cấp như cháy, khói, gas, nguy hiểm: ưu tiên mở lối thoát, bật đèn cần thiết, bật quạt phù hợp, không khóa người trong nhà.
- Nếu chủ về nhà: ưu tiên mở cửa chính nếu đang khóa, bật đèn hợp lý ở lối vào/phòng khách, có thể bật quạt phòng khách nếu phù hợp.
- Nếu đi ngủ: ưu tiên khóa các cửa, tắt phần lớn đèn/quạt không cần thiết, có thể giữ đèn phòng ngủ hoặc quạt phòng ngủ nếu phù hợp.
- Nếu không chắc chắn hoặc không liên quan nhà thông minh: actions=[] và scenario=null.

Nguyên tắc suy luận quan trọng:
- Không tạo tên thiết bị mới ngoài danh sách hợp lệ.
- Không trả về action mâu thuẫn nhau cho cùng một thiết bị.
- Không bật/tắt bừa bãi tất cả thiết bị nếu yêu cầu chỉ nhắm vào một khu vực.
- Nếu câu nói mơ hồ, hãy ưu tiên hành động ít rủi ro hơn.
- Nếu người dùng hỏi trạng thái hoặc hỏi tư vấn, có thể không cần action nhưng vẫn trả lời ngắn gọn dựa trên context.

Ví dụ suy luận:
- "Tôi về nhà" -> mở Cửa Chính, bật Đèn Hành Lang hoặc Đèn Chùm Trung Tâm nếu đang tắt.
- "Tôi đi ngủ" -> khóa các cửa đang mở, tắt đèn không cần thiết, giữ Đèn Phòng Ngủ hoặc Quạt Phòng Ngủ nếu hợp lý.
- "Có cháy ở bếp" -> mở Cửa Chính nếu cần thoát hiểm, bật Đèn Hành Lang/Đèn Nhà Bếp nếu tối, bật Quạt Nhà Bếp, không khóa cửa.
- "Khói nhiều quá" -> ưu tiên an toàn, có thể dùng scenario "sos" nếu phù hợp.
- "Phòng khách nóng" -> bật Quạt Trần Phòng Khách, chỉ thêm đèn nếu người dùng có ý cần sáng.

Schema:
{
  "response": "câu trả lời ngắn (<= 2 câu)",
  "actions": [{"device": "Tên thiết bị", "status": true}],
  "scenario": null
}
""".strip()


class WebSocketBroadcastServer:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.clients = set()
        self.loop = None
        self.thread = None
        self.started = threading.Event()
        self.server = None
        self.stop_future = None

    async def _broadcast(self, message: str):
        stale_clients = []
        for client in list(self.clients):
            try:
                await client.send(message)
            except ConnectionClosed:
                stale_clients.append(client)
            except Exception:
                stale_clients.append(client)

        for client in stale_clients:
            self.clients.discard(client)

    async def _emit_event(self, event: str, data: dict):
        payload = {
            "event": event,
            "timestamp": datetime.now().isoformat(timespec="milliseconds"),
            "data": data,
        }
        await self._broadcast(json.dumps(payload, ensure_ascii=False))

    async def _send_event(self, websocket, event: str, data: dict):
        payload = {
            "event": event,
            "timestamp": datetime.now().isoformat(timespec="milliseconds"),
            "data": data,
        }
        await websocket.send(json.dumps(payload, ensure_ascii=False))

    async def _handle_client(self, websocket):
        self.clients.add(websocket)
        try:
            initial_payload = get_current_home_payload() or {}
            await self._send_event(
                websocket,
                "device.sync",
                {
                    "commands": build_full_device_commands(initial_payload),
                    "full_state": True,
                },
            )
            async for raw_message in websocket:
                try:
                    parsed = json.loads(raw_message)
                except json.JSONDecodeError:
                    parsed = {"message": raw_message}

                event = str(parsed.get("event") or "ws.client_message")
                data = parsed.get("data")
                if not isinstance(data, dict):
                    data = {"payload": parsed}
                await self._handle_incoming_event(event, data)
        finally:
            self.clients.discard(websocket)

    async def _handle_incoming_event(self, event: str, data: dict):
        if event == "sensor.sync":
            sensor_payload = normalize_sensor_payload(data)
            if sensor_payload is None:
                return
            store_sensor_data(sensor_payload)
            await self._emit_event("sensor.updated", sensor_payload)
            return

        await self._emit_event(
            event,
            {
                **data,
                "clients": len(self.clients),
            },
        )

    async def _run_server(self):
        self.stop_future = self.loop.create_future()
        self.server = await serve(self._handle_client, self.host, self.port)
        self.started.set()
        try:
            await self.stop_future
        finally:
            self.server.close()
            await self.server.wait_closed()
            self.server = None
            self.stop_future = None

    def _run_forever(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        server_task = self.loop.create_task(self._run_server())
        try:
            self.loop.run_forever()
        finally:
            pending_tasks = [
                task for task in asyncio.all_tasks(self.loop)
                if task is not server_task and not task.done()
            ]
            for task in pending_tasks:
                task.cancel()
            if pending_tasks:
                self.loop.run_until_complete(
                    asyncio.gather(*pending_tasks, return_exceptions=True)
                )
            if not server_task.done():
                server_task.cancel()
                self.loop.run_until_complete(
                    asyncio.gather(server_task, return_exceptions=True)
                )
            self.loop.close()
            self.loop = None

    def start(self):
        if self.thread and self.thread.is_alive():
            return
        self.started.clear()
        self.thread = threading.Thread(target=self._run_forever, daemon=True)
        self.thread.start()
        self.started.wait(timeout=3)

    def stop(self):
        if self.loop is None:
            return

        def shutdown():
            if self.stop_future is not None and not self.stop_future.done():
                self.stop_future.set_result(None)
            self.loop.stop()

        self.loop.call_soon_threadsafe(shutdown)
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=3)
        self.thread = None

    def emit(self, event: str, data: dict):
        if self.loop is None:
            return
        future = asyncio.run_coroutine_threadsafe(
            self._emit_event(event, data),
            self.loop,
        )
        try:
            future.result(timeout=1)
        except Exception:
            pass


ws_server = WebSocketBroadcastServer(WS_HOST, WS_PORT)

def get_latest_sensor_snapshot() -> dict | None:
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT temperature, humidity, pir, gas_ppm, timestamp FROM sensor_logs ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()

    if row is None:
        return None

    return {
        "temperature": row[0],
        "humidity": row[1],
        "pir": None if row[2] is None else bool(row[2]),
        "gas_ppm": row[3],
        "timestamp": row[4],
    }


def normalize_sensor_payload(data: dict) -> dict | None:
    try:
        temperature = float(data["temperature"])
        humidity = float(data["humidity"])
    except (KeyError, TypeError, ValueError):
        return None

    pir = data.get("pir")
    if pir is not None:
        pir = bool(pir)

    gas_value = data.get("gas_ppm")
    if gas_value is None:
        gas_value = data.get("gas")
    try:
        gas_ppm = None if gas_value is None else float(gas_value)
    except (TypeError, ValueError):
        gas_ppm = None

    return {
        "temperature": temperature,
        "humidity": humidity,
        "pir": pir,
        "gas_ppm": gas_ppm,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def store_sensor_data(sensor_payload: dict):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO sensor_logs (temperature, humidity, pir, gas_ppm, timestamp) VALUES (?, ?, ?, ?, ?)",
        (
            sensor_payload["temperature"],
            sensor_payload["humidity"],
            None if sensor_payload["pir"] is None else int(bool(sensor_payload["pir"])),
            sensor_payload["gas_ppm"],
            sensor_payload["timestamp"],
        )
    )
    conn.commit()
    conn.close()
    print(
        f"[{sensor_payload['timestamp']}] Nhiet do: {sensor_payload['temperature']}°C"
        f"  |  Do am: {sensor_payload['humidity']}%"
        f"  |  PIR: {sensor_payload['pir']}  |  Gas: {sensor_payload['gas_ppm']}"
    )


def get_current_home_payload() -> dict | None:
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT payload FROM home_state WHERE id = 1"
    ).fetchone()
    conn.close()

    if row is None:
        return None

    try:
        return json.loads(row[0])
    except Exception:
        return None


def build_ai_context_message(user_text: str) -> str:
    home_payload = get_current_home_payload() or {}
    latest_sensor = get_latest_sensor_snapshot()

    device_states = home_payload.get("deviceStates", {})
    recent_logs = home_payload.get("logs", [])
    if isinstance(recent_logs, list):
        recent_logs = recent_logs[-MAX_CONTEXT_LOGS:]
    else:
        recent_logs = []

    compact_logs = []
    for entry in recent_logs:
        if not isinstance(entry, dict):
            continue
        compact_logs.append(
            {
                "time": str(entry.get("time", ""))[:16],
                "tag": str(entry.get("tag", ""))[:24],
                "msg": str(entry.get("msg", ""))[:MAX_LOG_MESSAGE_LENGTH],
                "type": str(entry.get("type", ""))[:16],
            }
        )

    context = {
        "user_request": user_text[:MAX_USER_REQUEST_LENGTH],
        "current_home_state": {
            "deviceStates": device_states,
            "recentLogs": compact_logs,
            "latestSensor": latest_sensor,
        },
        "instruction": (
            "Hãy suy luận dựa trên trạng thái hiện tại. "
            "Chỉ trả về các action cần thay đổi so với trạng thái hiện tại."
        ),
    }
    return json.dumps(context, ensure_ascii=False)


def extract_first_json_object(text: str) -> str | None:
    start = text.find("{")
    if start == -1:
        return None

    depth = 0
    in_string = False
    escaped = False

    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]

    return None


def parse_ai_json(content: str) -> dict:
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        extracted = extract_first_json_object(content)
        if extracted:
            return json.loads(extracted)

        sanitized = re.sub(r"[\x00-\x1f]+", " ", content).strip()
        extracted = extract_first_json_object(sanitized)
        if extracted:
            return json.loads(extracted)

        raise

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


@app.on_event("startup")
def start_websocket_server():
    ws_server.start()


@app.on_event("shutdown")
def stop_websocket_server():
    ws_server.stop()


def broadcast_home_state(payload: dict, revision: int, updated_at: str):
    previous_payload = get_current_home_payload() or {}
    commands = build_device_commands(previous_payload, payload)
    if not commands:
        return
    ws_server.emit(
        "device.sync",
        {
            "commands": commands,
            "revision": revision,
            "updated_at": updated_at,
        },
    )


def build_device_commands(previous_payload: dict, next_payload: dict) -> list[dict]:
    previous_states = previous_payload.get("deviceStates", {})
    next_states = next_payload.get("deviceStates", {})
    if not isinstance(previous_states, dict):
        previous_states = {}
    if not isinstance(next_states, dict):
        next_states = {}

    commands = []
    for device_name, next_status in next_states.items():
        if device_name not in VALID_DEVICE_NAMES or not isinstance(next_status, bool):
            continue

        previous_status = previous_states.get(device_name)
        if previous_status is next_status:
            continue

        commands.append(
            {
                "device": device_name,
                "key": DEVICE_API_KEYS.get(device_name, "unknown"),
                "status": next_status,
            }
        )
    return commands


def build_full_device_commands(payload: dict) -> list[dict]:
    device_states = payload.get("deviceStates", {})
    if not isinstance(device_states, dict):
        device_states = {}

    commands = []
    for device_name, status in device_states.items():
        if device_name not in VALID_DEVICE_NAMES or not isinstance(status, bool):
            continue
        commands.append(
            {
                "device": device_name,
                "key": DEVICE_API_KEYS.get(device_name, "unknown"),
                "status": status,
            }
        )
    return commands

class SensorData(BaseModel):
    temperature: float
    humidity: float
    pir: Optional[bool] = None
    gas_ppm: Optional[float] = None

@app.post("/api/sensor")
def receive_sensor(data: SensorData):
    sensor_payload = {
        "temperature": data.temperature,
        "humidity": data.humidity,
        "pir": data.pir,
        "gas_ppm": data.gas_ppm,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    store_sensor_data(sensor_payload)
    ws_server.emit("sensor.updated", sensor_payload)
    return {"status": "ok", **sensor_payload}

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
        {"role": "user", "content": build_ai_context_message(user_text)},
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
                    "max_tokens": 450,
                    "response_format": {"type": "json_object"},
                },
            )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"].strip()
        parsed = parse_ai_json(content)
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
    payload = data.model_dump()
    payload_json = json.dumps(payload, ensure_ascii=False)
    previous_payload = get_current_home_payload() or {}

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
    commands = build_device_commands(previous_payload, payload)
    if commands:
        ws_server.emit(
            "device.sync",
            {
                "commands": commands,
                "revision": next_revision,
                "updated_at": ts,
            },
        )
    return {"status": "ok", "updated_at": ts, "revision": next_revision}
