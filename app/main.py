from fastapi import FastAPI
from app.models import Telemetry
import sqlite3

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
