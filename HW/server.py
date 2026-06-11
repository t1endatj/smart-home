#!/usr/bin/env python3
"""HTTP + TCP command bridge for the Wokwi ESP32 smart-home sketch."""

from __future__ import annotations

import argparse
import os
import re
import json
import socket
import subprocess
import tempfile
import threading
import uuid
import wave
from collections import defaultdict
from http import cookies
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Set
from urllib.parse import parse_qs, urlparse

import requests

try:
    import numpy as np
    import sounddevice as sd
except ImportError:
    np = None
    sd = None


BASE_DIR = Path(__file__).resolve().parent
VOICE_DIR = BASE_DIR / "voice-assistant"
VOICE_INDEX_PATH = VOICE_DIR / "index.html"
XAI_API_URL = "https://api.x.ai/v1/chat/completions"
PIPER_BIN = VOICE_DIR / "venv" / "bin" / "piper"
PIPER_MODEL = VOICE_DIR / "models" / "piper-vi" / "vi_VN-vais1000-medium.onnx"
PIPER_CONFIG = PIPER_MODEL.with_suffix(".onnx.json")
SESSION_COOKIE_NAME = "smart_home_voice_session"
MAX_HISTORY_MESSAGES = 8
TTS_ALLOWED_CHARS_RE = re.compile(r"[^0-9A-Za-zÀ-ỹ\s,]")

conversation_store = defaultdict(list)
conversation_lock = threading.Lock()


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        name, value = line.split("=", 1)
        name = name.strip()
        value = value.strip().strip("\"'")
        if name and name not in os.environ:
            os.environ[name] = value


load_dotenv(BASE_DIR / ".env")

XAI_MODEL = os.environ.get("XAI_MODEL", "grok-4-1-fast-non-reasoning")
XAI_API_KEY = os.environ.get("XAI_API_KEY", "")

CONTROL_SYSTEM_PROMPT = """
Ban la bo dieu khien nha thong minh bang tieng Viet.
Hay chuyen cau noi cua nguoi dung thanh cac lenh ESP32 can thiet neu co the.
Chi tra ve JSON hop le, khong markdown.

Bang lenh:
? = in menu
1 = bat tat ca den
0 = tat tat ca den
h = bat den hanh lang
H = tat den hanh lang
b = bat den phong ngu
B = tat den phong ngu
w = bat den nha ve sinh
W = tat den nha ve sinh
v = bat den phong khach
V = tat den phong khach
k = bat den nha bep
K = tat den nha bep
2 = bat tat ca quat
3 = tat tat ca quat
q = bat quat phong ngu
Q = tat quat phong ngu
f = bat quat phong khach
F = tat quat phong khach
o = mo cua chinh
c = khoa cua chinh
t = doc nhiet do do am
m = doc cam bien chuyen dong
g = doc cam bien gas
a = chay tu dong 1 lan
p = in trang thai

Duoc phep tu suy ra chuoi lenh can thiet tu yeu cau tu nhien.
Vi du:
- "toi di ngu" -> tat tat ca den, tat tat ca quat, khoa cua: ["0","3","c"]
- "bat phong khach" -> bat den phong khach: ["v"]
- "nha bep co mui gas" -> doc gas va kiem tra canh bao: ["g"]
- "toi ra ngoai" -> tat tat ca den, tat tat ca quat, khoa cua: ["0","3","c"]
- "mo cua va bat den hanh lang" -> ["o","h"]

Neu nguoi dung hoi chuyen binh thuong hoac yeu cau khong ro, commands phai la [].
Reply bang tieng Viet rat ngan gon, toi da 2 cau.
Schema: {"commands": ["cac lenh 1 ky tu theo dung thu tu"], "reply": "cau tra loi ngan"}
""".strip()

VALID_COMMANDS = set("?10hHbBwWvVkK23qQfFoctmgap".replace(" ", ""))


class ClientHub:
    def __init__(self) -> None:
        self._clients: Set[socket.socket] = set()
        self._lock = threading.Lock()

    def add(self, client: socket.socket) -> None:
        with self._lock:
            self._clients.add(client)
        print(f"[tcp] client connected: {client.getpeername()}")

    def remove(self, client: socket.socket) -> None:
        with self._lock:
            self._clients.discard(client)
        try:
            peer = client.getpeername()
        except OSError:
            peer = "unknown"
        print(f"[tcp] client disconnected: {peer}")

    def broadcast(self, command: str) -> int:
        payload = f"{command}\n".encode("utf-8")
        stale_clients: list[socket.socket] = []

        with self._lock:
            clients = list(self._clients)

        for client in clients:
            try:
                client.sendall(payload)
            except OSError:
                stale_clients.append(client)

        for client in stale_clients:
            self.remove(client)
            try:
                client.close()
            except OSError:
                pass

        return len(clients) - len(stale_clients)


def build_control_messages(session_id: str, user_text: str) -> list[dict[str, str]]:
    with conversation_lock:
        history = list(conversation_store[session_id])

    messages = [{"role": "system", "content": CONTROL_SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_text})
    return messages


def append_history(session_id: str, user_text: str, reply_text: str) -> None:
    with conversation_lock:
        history = conversation_store[session_id]
        history.append({"role": "user", "content": user_text})
        history.append({"role": "assistant", "content": reply_text})
        conversation_store[session_id] = history[-MAX_HISTORY_MESSAGES:]


def ask_control_llm(messages: list[dict[str, str]]) -> tuple[dict, str]:
    if not XAI_API_KEY:
        raise RuntimeError("Missing XAI_API_KEY")

    response = requests.post(
        XAI_API_URL,
        headers={
            "Authorization": f"Bearer {XAI_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": XAI_MODEL,
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": 120,
            "response_format": {"type": "json_object"},
        },
        timeout=30,
    )
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"].strip()
    print(f"[llm] raw_response={content}")
    return json.loads(content), content


def normalize_llm_commands(result: dict) -> list[str]:
    raw_commands = result.get("commands")
    if raw_commands is None:
        raw_commands = result.get("command")

    if raw_commands is None:
        return []
    if isinstance(raw_commands, str):
        raw_commands = [raw_commands]
    if not isinstance(raw_commands, list):
        return []

    commands: list[str] = []
    for raw_command in raw_commands:
        command = str(raw_command).strip()
        if len(command) != 1 or command not in VALID_COMMANDS:
            print(f"[llm] ignored_invalid_command={command!r}")
            continue
        commands.append(command)
    return commands


def sanitize_tts_text(text: str) -> str:
    cleaned = text.replace(".", ",").replace("!", ",").replace("?", ",")
    cleaned = cleaned.replace(";", ",").replace(":", ",")
    cleaned = cleaned.replace("(", " ").replace(")", " ")
    cleaned = cleaned.replace("\"", " ").replace("'", " ").replace("-", " ")
    cleaned = TTS_ALLOWED_CHARS_RE.sub(" ", cleaned)
    cleaned = re.sub(r",{2,}", ",", cleaned)
    cleaned = re.sub(r"\s+,", ",", cleaned)
    cleaned = cleaned.strip(" ,")
    return re.sub(r"\s+", " ", cleaned).strip()


def tts_is_available() -> bool:
    return bool(np is not None and sd is not None and PIPER_BIN.exists() and PIPER_MODEL.exists())


def synthesize_and_play(text: str) -> None:
    if not text or not tts_is_available():
        return

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as wav_file:
        wav_path = Path(wav_file.name)

    try:
        subprocess.run(
            [
                str(PIPER_BIN),
                "--model",
                str(PIPER_MODEL),
                "--config",
                str(PIPER_CONFIG),
                "--output-file",
                str(wav_path),
                "--sentence-silence",
                "0.0",
            ],
            input=text,
            text=True,
            capture_output=True,
            check=True,
        )

        with wave.open(str(wav_path), "rb") as wav_reader:
            sample_rate = wav_reader.getframerate()
            channels = wav_reader.getnchannels()
            sample_width = wav_reader.getsampwidth()
            frames = wav_reader.readframes(wav_reader.getnframes())

        if sample_width != 2:
            raise RuntimeError(f"Unsupported sample width: {sample_width}")

        audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
        if channels > 1:
            audio = audio.reshape(-1, channels)

        sd.play(audio, sample_rate)
        sd.wait()
    finally:
        wav_path.unlink(missing_ok=True)


def run_tcp_server(host: str, port: int, hub: ClientHub) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((host, port))
        server.listen()
        print(f"[tcp] listening on {host}:{port}")

        while True:
            client, _ = server.accept()
            threading.Thread(
                target=handle_tcp_client,
                args=(client, hub),
                daemon=True,
            ).start()


def handle_tcp_client(client: socket.socket, hub: ClientHub) -> None:
    hub.add(client)
    try:
        with client:
            while client.recv(1024):
                pass
    except OSError:
        pass
    finally:
        hub.remove(client)


def make_http_handler(hub: ClientHub) -> type[BaseHTTPRequestHandler]:
    class CommandHandler(BaseHTTPRequestHandler):
        def get_session_id(self) -> tuple[str, bool]:
            raw_cookie = self.headers.get("Cookie", "")
            cookie_jar = cookies.SimpleCookie()
            cookie_jar.load(raw_cookie)

            if SESSION_COOKIE_NAME in cookie_jar:
                return cookie_jar[SESSION_COOKIE_NAME].value, False

            return uuid.uuid4().hex, True

        def end_headers(self) -> None:
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            super().end_headers()

        def do_OPTIONS(self) -> None:
            self.send_response(204)
            self.end_headers()

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path == "/":
                self.send_json(
                    {
                        "ok": True,
                        "voice": "http://127.0.0.1:8000/voice",
                        "endpoints": [
                            "POST /command with {'command': '1'}",
                            "GET /send?cmd=1",
                            "POST /llm with {'text': 'bat den phong khach'}",
                            "LLM returns commands, deliveries, ai_response, raw_ai_response",
                        ],
                    }
                )
                return

            if parsed.path in ("/voice", "/voice/", "/index.html"):
                self.send_voice_index()
                return

            if parsed.path == "/health":
                self.send_json(
                    {
                        "ok": True,
                        "llm": bool(XAI_API_KEY),
                        "tts": tts_is_available(),
                    }
                )
                return

            if parsed.path != "/send":
                self.send_error(404, "Not found")
                return

            command = parse_qs(parsed.query).get("cmd", [""])[0]
            self.broadcast_command(command)

        def do_POST(self) -> None:
            if self.path == "/llm":
                self.handle_llm()
                return

            if self.path != "/command":
                self.send_error(404, "Not found")
                return

            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length).decode("utf-8").strip()
            command = ""

            if body:
                try:
                    data = json.loads(body)
                    command = str(data.get("command", ""))
                except json.JSONDecodeError:
                    command = body

            self.broadcast_command(command)

        def send_voice_index(self) -> None:
            if not VOICE_INDEX_PATH.exists():
                self.send_error(404, "Missing voice-assistant/index.html")
                return

            body = VOICE_INDEX_PATH.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def handle_llm(self) -> None:
            length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(length)

            try:
                payload = json.loads(raw_body.decode("utf-8"))
                text = str(payload.get("text", "")).strip()
                if not text:
                    self.send_json({"error": "Missing text"}, status=400)
                    return

                session_id, is_new_session = self.get_session_id()
                print(f"[llm] user={text}")
                result, raw_ai_response = ask_control_llm(
                    build_control_messages(session_id, text)
                )
                print(f"[llm] parsed_response={result}")

                reply = str(result.get("reply") or "Da nghe.").strip()
                commands = normalize_llm_commands(result)
                deliveries = []
                for command in commands:
                    delivered = hub.broadcast(command)
                    deliveries.append({"command": command, "delivered": delivered})
                    print(f"[llm] command={command!r}, delivered={delivered}")

                append_history(session_id, text, reply)
                tts_text = sanitize_tts_text(reply)
                if tts_text:
                    threading.Thread(
                        target=synthesize_and_play,
                        args=(tts_text,),
                        daemon=True,
                    ).start()

                extra_headers = {}
                if is_new_session:
                    extra_headers["Set-Cookie"] = (
                        f"{SESSION_COOKIE_NAME}={session_id}; Path=/; SameSite=Lax"
                    )
                self.send_json(
                    {
                        "reply": reply,
                        "commands": commands,
                        "deliveries": deliveries,
                        "ai_response": result,
                        "raw_ai_response": raw_ai_response,
                        "tts": tts_is_available(),
                    },
                    extra_headers=extra_headers,
                )
            except requests.HTTPError as exc:
                error_body = exc.response.text if exc.response is not None else str(exc)
                print(f"[llm] xai_http_error={error_body[:500]}")
                self.send_json({"error": error_body[:500]}, status=502)
            except Exception as exc:
                print(f"[llm] error={exc}")
                self.send_json({"error": str(exc)}, status=500)

        def broadcast_command(self, command: str) -> None:
            command = command.strip()
            if not command:
                self.send_error(400, "Missing command")
                return

            delivered = hub.broadcast(command)
            print(f"[http] command={command!r}, delivered={delivered}")
            self.send_json({"ok": True, "command": command, "delivered": delivered})

        def send_json(
            self,
            data: dict,
            status: int = 200,
            extra_headers: dict[str, str] | None = None,
        ) -> None:
            payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            if extra_headers:
                for name, value in extra_headers.items():
                    self.send_header(name, value)
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, format: str, *args: object) -> None:
            print(f"[http] {self.address_string()} - {format % args}")

    return CommandHandler


def main() -> None:
    parser = argparse.ArgumentParser(description="Smart Home command server")
    parser.add_argument("--tcp-host", default="0.0.0.0")
    parser.add_argument("--tcp-port", type=int, default=5001)
    parser.add_argument("--http-host", default="127.0.0.1")
    parser.add_argument("--http-port", type=int, default=8000)
    args = parser.parse_args()

    hub = ClientHub()
    threading.Thread(
        target=run_tcp_server,
        args=(args.tcp_host, args.tcp_port, hub),
        daemon=True,
    ).start()

    http_server = ThreadingHTTPServer(
        (args.http_host, args.http_port),
        make_http_handler(hub),
    )
    print(f"[http] listening on http://{args.http_host}:{args.http_port}")
    http_server.serve_forever()


if __name__ == "__main__":
    main()
