import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from fastapi.testclient import TestClient
os.environ['DISABLE_MQTT'] = '1'
from app.main import app
import sqlite3
from app.main import DB_FILE

conn = sqlite3.connect(DB_FILE)
cur = conn.cursor()
cur.execute("DELETE FROM telemetry WHERE vehicle_id='veh-test-stats'")
conn.commit()
conn.close()


client = TestClient(app)

def test_valid_command():
    r = client.post("/vehicles/veh-001/commands", json={"command": "start"})
    assert r.status_code == 202
    assert r.json()["published"] is True

def test_invalid_command():
    r = client.post("/vehicles/veh-001/commands", json={"command": "fly"})
    assert r.status_code == 400
