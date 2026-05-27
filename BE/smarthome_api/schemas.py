from typing import Optional

from pydantic import BaseModel


class SensorData(BaseModel):
    temperature: float
    humidity: float
    pir: Optional[bool] = None
    gas_ppm: Optional[float] = None
    gas_alarm: Optional[bool] = None


class ControlData(BaseModel):
    device: str
    status: bool


class AICommandRequest(BaseModel):
    command: str


class HomeStatePayload(BaseModel):
    deviceStates: dict
    logs: list | None = None

