from pydantic import BaseModel, Field, field_validator
from datetime import datetime, timezone, timedelta
from typing import Literal


# Modelo para la posición GPS
class GPS(BaseModel):
    lat: float = Field(..., ge=-90, le=90, description="Latitud entre -90 y 90")
    lon: float = Field(..., ge=-180, le=180, description="Longitud entre -180 y 180")


# Modelo para telemetría
class Telemetry(BaseModel):
    vehicle_id: str
    ts: datetime  # timestamp en formato ISO
    speed_kmh: float
    temperature_c: float
    battery_pct: float = Field(..., ge=0, le=100)
    range_km: float
    odometer_km: float
    gps: GPS
    smoke_detected: bool
    status: Literal["moving", "stopped"]

    @field_validator("ts")
    @classmethod

    def validate_ts(cls, value: datetime):
        # Asegurar que value está en UTC
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        elif value.tzinfo != timezone.utc:
            value = value.astimezone(timezone.utc)
        
        now = datetime.now(timezone.utc)
        
        
        if value > now + timedelta(minutes=10):
            raise ValueError("timestamp en el futuro no válido")
        
        if value < now - timedelta(days=365):
            raise ValueError("timestamp demasiado antiguo")
        
        return value


# Modelo para comandos
class Command(BaseModel):
    command: Literal["start", "stop", "start_telemetry", "stop_telemetry"]
