from fastapi import FastAPI
from app.models import Telemetry
import sqlite3
from fastapi import HTTPException
from datetime import datetime, timedelta, timezone  # Añadido timezone aquí

app = FastAPI(title="Vehicle Telemetry API")

# --- Configuración de la base de datos simple ---
DB_FILE = "data.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS telemetry (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vehicle_id TEXT,
        ts TEXT,
        speed_kmh REAL,
        temperature_c REAL,
        battery_pct REAL,
        range_km REAL,
        odometer_km REAL,
        lat REAL,
        lon REAL,
        smoke_detected INTEGER,
        status TEXT,
        UNIQUE(vehicle_id, ts)
    )
    """)
    conn.commit()
    conn.close()

init_db()

# --- Endpoint POST /ingest ---
@app.post("/ingest")
def ingest_telemetry(data: Telemetry):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        cursor.execute("""
        INSERT INTO telemetry (
            vehicle_id, ts, speed_kmh, temperature_c, battery_pct, range_km, odometer_km,
            lat, lon, smoke_detected, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.vehicle_id,
            data.ts.isoformat(),
            data.speed_kmh,
            data.temperature_c,
            data.battery_pct,
            data.range_km,
            data.odometer_km,
            data.gps.lat,
            data.gps.lon,
            int(data.smoke_detected),
            data.status
        ))
        conn.commit()
    except sqlite3.IntegrityError:
        # Si ya existe un registro con mismo vehicle_id + ts → idempotencia
        conn.close()
        return {"saved": False, "reason": "duplicate"}
    
    conn.close()
    return {"saved": True, "vehicle_id": data.vehicle_id, "ts": data.ts.isoformat()}


# --- Devolver telemetría ---
def _row_to_telemetry_dict(row: sqlite3.Row):
    return {
        "vehicle_id": row["vehicle_id"],
        "ts": row["ts"],
        "speed_kmh": row["speed_kmh"],
        "temperature_c": row["temperature_c"],
        "battery_pct": row["battery_pct"],
        "range_km": row["range_km"],
        "odometer_km": row["odometer_km"],
        "gps": {"lat": row["lat"], "lon": row["lon"]},
        "smoke_detected": bool(row["smoke_detected"]),
        "status": row["status"]
    }


# --- Devolver última telemetría válida ---
@app.get("/vehicles/{vehicle_id}/latest")
def get_latest(vehicle_id: str):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM telemetry WHERE vehicle_id=? ORDER BY ts DESC LIMIT 1", (vehicle_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="not found")
    return _row_to_telemetry_dict(row)

# --- Que el servidor calcule estadísticas básicas de un vehículo en una ventana de tiempo (por defecto, los últimos 60 minutos) ---
@app.get("/vehicles/{vehicle_id}/stats")
def get_stats(vehicle_id: str, minutes: int = 60):
    now = datetime.now(timezone.utc)  # Cambiado de datetime.utcnow()
    window_min = now - timedelta(minutes=minutes)

    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        """
        SELECT speed_kmh, temperature_c, battery_pct, ts
        FROM telemetry
        WHERE vehicle_id=? AND ts BETWEEN ? AND ?
        """,
        (vehicle_id, window_min.isoformat(), now.isoformat())
    )
    rows = cur.fetchall()
    conn.close()

    if not rows:
        raise HTTPException(status_code=404, detail="no data in window")

    def extract_stats(values):
        vals = [v for v in values if v is not None]
        return {
            "min": min(vals),
            "max": max(vals),
            "avg": sum(vals) / len(vals)
        }

    stats = {
        "speed_kmh": extract_stats([r["speed_kmh"] for r in rows]),
        "temperature_c": extract_stats([r["temperature_c"] for r in rows]),
        "battery_pct": extract_stats([r["battery_pct"] for r in rows]),
    }

    return {
        "window_min": window_min.isoformat(),
        "window_max": now.isoformat(),
        "count": len(rows),
        "stats": stats,
    }


# Enviar comandos al vehículo vía MQTT

VALID_COMMANDS = {"start", "stop", "start_telemetry", "stop_telemetry"}

from pydantic import BaseModel

class CommandIn(BaseModel):
    command: str

@app.post("/vehicles/{vehicle_id}/commands", status_code=202)
def send_command(vehicle_id: str, cmd: CommandIn):
    if cmd.command not in VALID_COMMANDS:
        raise HTTPException(status_code=400, detail="invalid command")

    import os
    if os.getenv("DISABLE_MQTT") == "1":
        # modo pruebas sin MQTT
        return {"published": True, "simulated": True}

    import paho.mqtt.publish as publish
    topic = f"vehicles/{vehicle_id}/commands"
    publish.single(topic, cmd.json(), hostname="localhost", port=1883)
    return {"published": True}
