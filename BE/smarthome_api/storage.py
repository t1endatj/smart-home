import copy
import json
import sqlite3
from datetime import datetime

from .config import (
    AUTO_GAS_THRESHOLD,
    DB_PATH,
    DEVICE_API_KEYS,
    MAX_CONTEXT_LOGS,
    MAX_HOME_LOGS,
    VALID_DEVICE_NAMES,
)


def gas_alarm_from_values(gas_alarm_value, gas_ppm) -> bool:
    if gas_alarm_value is not None:
        return bool(gas_alarm_value)
    if gas_ppm is not None:
        return float(gas_ppm) >= AUTO_GAS_THRESHOLD
    return False


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sensor_logs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            temperature REAL NOT NULL,
            humidity    REAL NOT NULL,
            pir         INTEGER,
            gas_ppm     REAL,
            gas_alarm   INTEGER,
            timestamp   TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS home_state (
            id         INTEGER PRIMARY KEY CHECK (id = 1),
            payload    TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            revision   INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    for statement in (
        "ALTER TABLE sensor_logs ADD COLUMN pir INTEGER",
        "ALTER TABLE sensor_logs ADD COLUMN gas_ppm REAL",
        "ALTER TABLE sensor_logs ADD COLUMN gas_alarm INTEGER",
        "ALTER TABLE home_state ADD COLUMN revision INTEGER NOT NULL DEFAULT 0",
    ):
        try:
            conn.execute(statement)
        except sqlite3.OperationalError:
            pass
    conn.commit()
    conn.close()


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

    gas_alarm = data.get("gas_alarm")
    if gas_alarm is None:
        gas_alarm = data.get("gasAlarm")
    if gas_alarm is not None:
        gas_alarm = bool(gas_alarm)

    return {
        "temperature": temperature,
        "humidity": humidity,
        "pir": pir,
        "gas_ppm": gas_ppm,
        "gas_alarm": gas_alarm,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def store_sensor_data(sensor_payload: dict):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO sensor_logs (temperature, humidity, pir, gas_ppm, gas_alarm, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
        (
            sensor_payload["temperature"],
            sensor_payload["humidity"],
            None if sensor_payload["pir"] is None else int(bool(sensor_payload["pir"])),
            sensor_payload["gas_ppm"],
            None if sensor_payload["gas_alarm"] is None else int(bool(sensor_payload["gas_alarm"])),
            sensor_payload["timestamp"],
        ),
    )
    conn.commit()
    conn.close()
    print(
        f"[{sensor_payload['timestamp']}] Nhiet do: {sensor_payload['temperature']}°C"
        f"  |  Do am: {sensor_payload['humidity']}%"
        f"  |  PIR: {sensor_payload['pir']}  |  Gas: {sensor_payload['gas_ppm']}  |  Gas Alarm: {sensor_payload['gas_alarm']}"
    )


def get_latest_sensor_snapshot() -> dict | None:
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT id, temperature, humidity, pir, gas_ppm, gas_alarm, timestamp FROM sensor_logs ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()
    if row is None:
        return None
    return {
        "id": row[0],
        "temperature": row[1],
        "humidity": row[2],
        "pir": None if row[3] is None else bool(row[3]),
        "gas_ppm": row[4],
        "gas_alarm": gas_alarm_from_values(row[5], row[4]),
        "timestamp": row[6],
    }


def list_sensor_snapshots(limit: int = 20) -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT temperature, humidity, pir, gas_ppm, gas_alarm, timestamp FROM sensor_logs ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    result = []
    for row in rows:
        gas_alarm = gas_alarm_from_values(row[4], row[3])
        result.append(
            {
                "temperature": row[0],
                "humidity": row[1],
                "pir": None if row[2] is None else bool(row[2]),
                "gas_ppm": row[3],
                "gas_alarm": gas_alarm,
                "gasAlarm": gas_alarm,
                "timestamp": row[5],
            }
        )
    return result


def get_current_home_payload() -> dict | None:
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT payload FROM home_state WHERE id = 1").fetchone()
    conn.close()
    if row is None:
        return None
    try:
        return json.loads(row[0])
    except Exception:
        return None


def get_home_state_record() -> dict:
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT payload, updated_at, revision FROM home_state WHERE id = 1").fetchone()
    conn.close()
    if row is None:
        return {"payload": None, "updated_at": None, "revision": 0}
    try:
        payload = json.loads(row[0])
    except Exception:
        payload = None
    return {"payload": payload, "updated_at": row[1], "revision": row[2]}


def build_default_home_payload() -> dict:
    return {
        "deviceStates": {device_name: False for device_name in VALID_DEVICE_NAMES},
        "logs": [],
        "automation": {
            "autoGasEnabled": True,
        },
    }


def normalize_home_payload(payload: dict | None) -> dict:
    normalized = build_default_home_payload()
    if not isinstance(payload, dict):
        return normalized

    device_states = payload.get("deviceStates")
    if isinstance(device_states, dict):
        normalized["deviceStates"].update(
            {
                device_name: status
                for device_name, status in device_states.items()
                if device_name in VALID_DEVICE_NAMES and isinstance(status, bool)
            }
        )

    logs = payload.get("logs")
    if isinstance(logs, list):
        normalized["logs"] = logs[-MAX_HOME_LOGS:]

    automation = payload.get("automation")
    if isinstance(automation, dict) and isinstance(automation.get("autoGasEnabled"), bool):
        normalized["automation"]["autoGasEnabled"] = automation["autoGasEnabled"]

    return normalized


def append_home_log(payload: dict, tag: str, msg: str, type_: str = "info"):
    logs = payload.get("logs")
    if not isinstance(logs, list):
        logs = []
    logs.append(
        {
            "time": datetime.now().strftime("%H:%M:%S"),
            "tag": tag,
            "msg": msg,
            "type": type_,
        }
    )
    payload["logs"] = logs[-MAX_HOME_LOGS:]


def compact_recent_logs(payload: dict) -> list[dict]:
    recent_logs = payload.get("logs", [])
    if not isinstance(recent_logs, list):
        return []
    return recent_logs[-MAX_CONTEXT_LOGS:]


def set_device_state(payload: dict, device_name: str, status: bool) -> bool:
    device_states = payload.get("deviceStates")
    if not isinstance(device_states, dict):
        device_states = {}
        payload["deviceStates"] = device_states
    current_status = device_states.get(device_name)
    if current_status is status:
        return False
    device_states[device_name] = status
    return True


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
        if previous_states.get(device_name) is next_status:
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


def save_home_state_payload(payload: dict) -> tuple[str, int]:
    ts = datetime.now().isoformat(timespec="milliseconds")
    payload_json = json.dumps(payload, ensure_ascii=False)
    conn = sqlite3.connect(DB_PATH)
    current_revision_row = conn.execute("SELECT revision FROM home_state WHERE id = 1").fetchone()
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
    return ts, next_revision


def clone_payload(payload: dict) -> dict:
    return copy.deepcopy(payload)
