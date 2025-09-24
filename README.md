# Vehicle Backend (Python / FastAPI)

Microservicio para telemetría de vehículos con soporte para MQTT opcional.

## 1. Requisitos

- Python 3.10+
- pip
- SQLite (ya incluido, no requiere instalación)
- Broker MQTT (opcional, para funcionalidad de comandos)
- Paquetes Python: instálalos con:

```bash
pip install -r requirements.txt
```

## 2. Levantar el servidor

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Para desarrollo sin MQTT:**
```bash
DISABLE_MQTT=1 uvicorn app.main:app --reload
```

Swagger UI disponible en: http://127.0.0.1:8000/docs

## 3. Endpoints principales

### POST /ingest
Recibe telemetría en formato JSON.

```bash
curl -X POST "http://127.0.0.1:8000/ingest" \
-H "Content-Type: application/json" \
-d '{
  "vehicle_id": "veh-001",
  "ts": "2025-09-24T06:47:00Z",
  "speed_kmh": 50.5,
  "temperature_c": 75.2,
  "battery_pct": 80,
  "range_km": 150,
  "odometer_km": 12345.6,
  "gps": {"lat": 40.4168, "lon": -3.7038},
  "smoke_detected": false,
  "status": "moving"
}'
```

**⚠️ Importante:** El timestamp debe ser la hora actual en UTC. Usar timestamps en el futuro causará errores de validación.

### GET /vehicles/{vehicle_id}/latest
Obtiene la última telemetría:

```bash
curl http://127.0.0.1:8000/vehicles/veh-001/latest
```

### GET /vehicles/{vehicle_id}/stats?minutes=60
Obtiene estadísticas (min, max, avg) de las últimas `minutes`:

```bash
curl http://127.0.0.1:8000/vehicles/veh-001/stats?minutes=60
```

### POST /vehicles/{vehicle_id}/commands
Envía comandos al vehículo (requiere broker MQTT):

```bash
curl -X POST http://127.0.0.1:8000/vehicles/veh-001/commands \
-H "Content-Type: application/json" \
-d '{"command": "start"}'
```

**Comandos soportados:** `start`, `stop`, `start_telemetry`, `stop_telemetry`

## 4. Configuración MQTT

### Instalar broker MQTT (Mosquitto)

**Con Docker:**
```bash
docker run -it -p 1883:1883 eclipse-mosquitto
```

**En Windows (Chocolatey):**
```bash
choco install mosquitto
mosquitto -v
```

**Sin MQTT (para desarrollo):**
```bash
export DISABLE_MQTT=1        # Linux/Mac
set DISABLE_MQTT=1           # Windows CMD
$env:DISABLE_MQTT="1"        # Windows PowerShell
```

## 5. Tests

Ejecutar tests:

```bash
pytest -q
```

Los tests incluyen validación de:
- Ingestión de telemetría
- Endpoint latest
- Estadísticas (stats)
- Comandos (con MQTT deshabilitado)

## 6. Validaciones implementadas

- **battery_pct:** entre 0 y 100
- **status:** debe ser `moving` o `stopped`  
- **GPS:** lat/lon dentro de rangos válidos (-90/90, -180/180)
- **timestamp:** no más de 10 minutos en el futuro, no más de 1 año en el pasado
- **Idempotencia:** mensajes duplicados (mismo vehicle_id + ts) se ignoran

## 7. Base de datos

- Persistencia en SQLite (`data.db`)
- Fácilmente reemplazable por PostgreSQL/MySQL
- Tabla `telemetry` con índice único en (vehicle_id, ts)

## 8. Script de ejemplo

### `publish_example.py` — Generar telemetría simulada

```python
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
```

Ejecutar varias veces para generar datos de prueba.

## 9. Estructura del proyecto

```
vehiculo_backend/
├── app/
│   ├── main.py          # Aplicación FastAPI
│   └── models.py        # Modelos Pydantic
├── tests/
│   └── test_*.py        # Tests unitarios
├── requirements.txt     # Dependencias
├── data.db             # Base de datos SQLite
└── README.md           # Este archivo
```