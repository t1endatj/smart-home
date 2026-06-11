#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="${BUILD_DIR:-$SCRIPT_DIR/build}"
CLEAN_BUILD="${CLEAN_BUILD:-1}"
FQBN="${FQBN:-esp32:esp32:esp32}"
SKETCH_NAME="${SKETCH_NAME:-Smart_Home_HardW}"
SKETCH_FILE="${SKETCH_FILE:-$SCRIPT_DIR/${SKETCH_NAME}.ino}"
STAGING_DIR="${STAGING_DIR:-/tmp/${SKETCH_NAME}-cli}"
STAGING_SKETCH_DIR="$STAGING_DIR/$SKETCH_NAME"

if ! command -v arduino-cli >/dev/null 2>&1; then
  echo "arduino-cli not found. Please install Arduino CLI first." >&2
  exit 1
fi

if [ ! -f "$SKETCH_FILE" ]; then
  echo "Sketch file not found: $SKETCH_FILE" >&2
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
  if [ -e "$SCRIPT_DIR/$path" ]; then
    cp -R "$SCRIPT_DIR/$path" "$STAGING_SKETCH_DIR/$path"
  fi
done

exec arduino-cli compile \
  --fqbn "$FQBN" \
  --build-path "$BUILD_DIR" \
  "$STAGING_SKETCH_DIR"
