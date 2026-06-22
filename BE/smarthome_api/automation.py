import threading

from .config import (
    AUTO_GAS_THRESHOLD,
    AUTO_POLL_INTERVAL_SECONDS,
    AUTO_PRESENCE_FAN,
    AUTO_PRESENCE_LIGHT,
    AUTO_TEMPERATURE_FAN,
    AUTO_TEMPERATURE_THRESHOLD,
    DOOR_DEVICE_NAMES,
    LIGHT_DEVICE_NAMES,
)
from .realtime import emit_home_state_delta
from .storage import (
    append_home_log,
    build_default_home_payload,
    clone_payload,
    get_current_home_payload,
    get_latest_sensor_snapshot,
    save_home_state_payload,
    set_device_state,
)


class AutomationEngine:
    def __init__(self, ws_server):
        self.ws_server = ws_server
        self.stop_event = threading.Event()
        self.thread = None
        self.last_processed_sensor_id = 0

    def start(self):
        if self.thread and self.thread.is_alive():
            return
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=3)
        self.thread = None

    def _run(self):
        while not self.stop_event.wait(AUTO_POLL_INTERVAL_SECONDS):
            latest_sensor = get_latest_sensor_snapshot()
            if latest_sensor is None:
                continue
            sensor_id = int(latest_sensor.get("id") or 0)
            if sensor_id <= self.last_processed_sensor_id:
                continue
            self.apply_sensor_automation(latest_sensor)
            self.last_processed_sensor_id = sensor_id

    def apply_sensor_automation(self, sensor_payload: dict) -> bool:
        previous_payload = get_current_home_payload() or build_default_home_payload()
        next_payload = clone_payload(previous_payload)
        changed = False
        automation_settings = previous_payload.get("automation", {})
        auto_temperature_enabled = automation_settings.get("autoTemperatureEnabled", False) is True
        auto_temperature_threshold = automation_settings.get(
            "autoTemperatureThreshold", AUTO_TEMPERATURE_THRESHOLD
        )
        auto_gas_enabled = automation_settings.get("autoGasEnabled", True) is True
        auto_motion_enabled = automation_settings.get("autoMotionEnabled", False) is True

        temperature = sensor_payload.get("temperature")
        if (
            auto_temperature_enabled
            and isinstance(temperature, (int, float))
            and temperature >= float(auto_temperature_threshold)
        ):
            if set_device_state(next_payload, AUTO_TEMPERATURE_FAN, True):
                changed = True
                append_home_log(
                    next_payload,
                    "AUTO",
                    f"Nhiệt độ {temperature:.1f}°C cao, tự động bật quạt phòng khách.",
                    "warning",
                )

        if auto_motion_enabled and sensor_payload.get("pir") is True:
            presence_changed = False
            presence_changed |= set_device_state(next_payload, AUTO_PRESENCE_LIGHT, True)
            presence_changed |= set_device_state(next_payload, AUTO_PRESENCE_FAN, True)
            if presence_changed:
                changed = True
                append_home_log(
                    next_payload,
                    "AUTO",
                    "Phát hiện chuyển động phòng khách, tự động bật đèn và quạt phòng khách.",
                    "success",
                )

        gas_alarm = sensor_payload.get("gas_alarm") is True
        gas_ppm = sensor_payload.get("gas_ppm")
        if not gas_alarm and isinstance(gas_ppm, (int, float)):
            gas_alarm = gas_ppm >= AUTO_GAS_THRESHOLD

        if auto_gas_enabled and gas_alarm:
            gas_changed = False
            for device_name in LIGHT_DEVICE_NAMES:
                gas_changed |= set_device_state(next_payload, device_name, True)
            for device_name in DOOR_DEVICE_NAMES:
                gas_changed |= set_device_state(next_payload, device_name, True)
            
            for fan_name in ("fan", "fan_bedroom"):
                gas_changed |= set_device_state(next_payload, fan_name, True)
                if "fanSpeeds" not in next_payload:
                    next_payload["fanSpeeds"] = {}
                if next_payload["fanSpeeds"].get(fan_name) != 80:
                    next_payload["fanSpeeds"][fan_name] = 80
                    gas_changed = True
                    
            if gas_changed:
                changed = True
                append_home_log(
                    next_payload,
                    "AUTO",
                    "Khí gas quá cao, tự động bật toàn bộ đèn, quạt và mở toàn bộ cửa.",
                    "danger",
                )

        if not changed:
            return False

        updated_at, revision = save_home_state_payload(next_payload)
        emit_home_state_delta(self.ws_server, previous_payload, next_payload, revision, updated_at)
        return True
