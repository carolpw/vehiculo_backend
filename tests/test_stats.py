import os
from fastapi.testclient import TestClient
os.environ['DISABLE_MQTT'] = '1'
from app.main import app
from datetime import datetime, timedelta, timezone 

client = TestClient(app)

def test_stats_endpoint():
    vehicle_id = "veh-test-stats"
    now = datetime.now(timezone.utc)
    
    payloads = [
        {
            "vehicle_id": vehicle_id,
            "ts": (now - timedelta(minutes=10)).isoformat(),
            "speed_kmh": 10.0,
            "temperature_c": 20.0,
            "battery_pct": 90.0,
            "range_km": 200.0,
            "odometer_km": 500.0,
            "gps": {"lat": 0.0, "lon": 0.0},
            "smoke_detected": False,
            "status": "moving"
        },
        {
            "vehicle_id": vehicle_id,
            "ts": (now - timedelta(minutes=5)).isoformat(),
            "speed_kmh": 20.0,
            "temperature_c": 30.0,
            "battery_pct": 80.0,
            "range_km": 190.0,
            "odometer_km": 510.0,
            "gps": {"lat": 0.0, "lon": 0.0},
            "smoke_detected": False,
            "status": "moving"
        }
    ]
    
    # Insertar los datos
    for p in payloads:
        r = client.post("/ingest", json=p)
        assert r.status_code in (200, 201)
    
    # Consultar estadísticas
    r2 = client.get(f"/vehicles/{vehicle_id}/stats?minutes=60")
    assert r2.status_code == 200
    body = r2.json()
    assert body["count"] == 2
    assert "stats" in body
    assert "speed_kmh" in body["stats"]
    
    # Verificaciones adicionales más específicas
    assert body["stats"]["speed_kmh"]["min"] == 10.0
    assert body["stats"]["speed_kmh"]["max"] == 20.0
    assert body["stats"]["speed_kmh"]["avg"] == 15.0
    
    assert body["stats"]["temperature_c"]["min"] == 20.0
    assert body["stats"]["temperature_c"]["max"] == 30.0
    assert body["stats"]["temperature_c"]["avg"] == 25.0