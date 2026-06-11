#!/usr/bin/env bash
set -euo pipefail

PROJECT_FOLDER="${PROJECT_FOLDER:-/home/phuchoangsrc/smart-home/HW}"
BOARD="${BOARD:-esp32:esp32:nodemcu-32s:UploadSpeed=921600}"
PORT="${PORT:-/dev/ttyUSB0}"
SKETCH_NAME="${SKETCH_NAME:-Smart_Home_HardW}"
SKETCH_FILE="${SKETCH_FILE:-$PROJECT_FOLDER/${SKETCH_NAME}.ino}"
BUILD_DIR="${BUILD_DIR:-$PROJECT_FOLDER/build}"
CLEAN_BUILD="${CLEAN_BUILD:-1}"
STAGING_DIR="${STAGING_DIR:-/tmp/${SKETCH_NAME}-cli}"
STAGING_SKETCH_DIR="$STAGING_DIR/$SKETCH_NAME"

if [ ! -f "$SKETCH_FILE" ]; then
    echo "Error: Sketch file not found: $SKETCH_FILE"
    exit 1
fi

if ! command -v arduino-cli >/dev/null 2>&1; then
    echo "Error: arduino-cli not found"
    exit 1
fi

if [ "$CLEAN_BUILD" = "1" ]; then
    rm -rf "$BUILD_DIR"
fi

mkdir -p "$BUILD_DIR"
rm -rf "$STAGING_SKETCH_DIR"
mkdir -p "$STAGING_SKETCH_DIR"

cp "$SKETCH_FILE" "$STAGING_SKETCH_DIR/${SKETCH_NAME}.ino"

for path in src lib include diagram.json wokwi.toml; do
    if [ -e "$PROJECT_FOLDER/$path" ]; then
        cp -R "$PROJECT_FOLDER/$path" "$STAGING_SKETCH_DIR/$path"
    fi
done

arduino-cli compile \
    -j "$(nproc)" \
    --fqbn "$BOARD" \
    --build-path "$BUILD_DIR" \
    "$STAGING_SKETCH_DIR"

arduino-cli upload \
    -p "$PORT" \
    --fqbn "$BOARD" \
    --input-dir "$BUILD_DIR" \
    "$STAGING_SKETCH_DIR"

"$PROJECT_FOLDER/monitor.sh"
