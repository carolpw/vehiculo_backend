import requests
from datetime import datetime, timezone
import random

URL = "http://127.0.0.1:8000/ingest"

data = {
    "vehicle_id": "veh-001",
    "ts": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
    "speed_kmh": random.uniform(0, 120),
    "temperature_c": random.uniform(20, 80),
    "battery_pct": random.uniform(10, 100),
    "range_km": random.uniform(50, 400),
    "odometer_km": 12345.0,
    "gps": {"lat": 40.4168, "lon": -3.7038},
    "smoke_detected": False,
    "status": random.choice(["moving", "stopped"])
}

resp = requests.post(URL, json=data)
print(resp.json())