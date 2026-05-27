from .storage import build_device_commands


def emit_home_state_delta(ws_server, previous_payload: dict, payload: dict, revision: int, updated_at: str):
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

