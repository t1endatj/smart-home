import io
import json
import re
import base64
import httpx
try:
    from gtts import gTTS
except ImportError:
    gTTS = None

from .config import (
    AI_SYSTEM_PROMPT,
    GROK_API_KEY,
    GROK_API_URL,
    GROK_MODEL,
    MAX_USER_REQUEST_LENGTH,
    VALID_DEVICE_NAMES,
)
from .storage import get_current_home_payload, get_latest_sensor_snapshot


def build_ai_context_message(user_text: str) -> str:
    home_payload = get_current_home_payload() or {}
    latest_sensor = get_latest_sensor_snapshot()
    device_states = home_payload.get("deviceStates", {})

    context = {
        "user_request": user_text[:MAX_USER_REQUEST_LENGTH],
        "current_home_state": {
            "deviceStates": device_states,
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


def handle_ai_command(user_text: str) -> dict:
    user_text = (user_text or "").strip()
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
        parsed = parse_ai_json(resp.json()["choices"][0]["message"]["content"].strip())
    except Exception as exc:
        return {
            "response": f"Lỗi gọi Grok: {exc}",
            "actions": [],
            "scenario": None,
        }

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

    scenario = parsed.get("scenario", None)
    if scenario not in (None, "welcome", "sleep", "sos", "alloff"):
        scenario = None

    response_text = str(parsed.get("response") or "Đã nhận lệnh.").strip()
    audio_base64 = None

    if gTTS is not None and response_text:
        try:
            tts = gTTS(response_text, lang='vi')
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            fp.seek(0)
            audio_base64 = base64.b64encode(fp.read()).decode('utf-8')
        except Exception as e:
            print(f"Lỗi tạo TTS: {e}")

    return {
        "response": response_text,
        "actions": normalized_actions,
        "scenario": scenario,
        "audio_base64": audio_base64,
    }
