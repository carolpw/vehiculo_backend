import os
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from fastapi.testclient import TestClient
os.environ['DISABLE_MQTT'] = '1'
from app.main import app
from datetime import datetime, timezone

client = TestClient(app)

def test_latest_endpoint():
    # Generar timestamp actual
    current_ts = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    
    payload = {
        "vehicle_id": "veh-test-latest",
        "ts": current_ts,  # Timestamp dinámico
        "speed_kmh": 12.0,
        "temperature_c": 20.0,
        "battery_pct": 90.0,
        "range_km": 200.0,
        "odometer_km": 500.0,
        "gps": {"lat": 0.0, "lon": 0.0},
        "smoke_detected": False,
        "status": "moving"
    }
    # Ingestar
    r = client.post("/ingest", json=payload)
    assert r.status_code in (200,201)
    # Consultar latest
    r2 = client.get("/vehicles/veh-test-latest/latest")
    assert r2.status_code == 200
    body = r2.json()
    assert body["vehicle_id"] == "veh-test-latest"
    assert "ts" in body
