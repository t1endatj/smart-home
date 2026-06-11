#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-/dev/ttyUSB0}"
CONFIG="${CONFIG:-115200}"

if ! command -v arduino-cli >/dev/null 2>&1; then
    echo "Error: arduino-cli not found"
    exit 1
fi

arduino-cli monitor -p "$PORT" -c "$CONFIG"
