# SOFE3290: Software Quality & Project Management
## Iteration 1: Baseline SDV Pipeline Implementation
**Project Group:** 24

**Members:** Umer Bashir, Abdul Aziz Syed, Nathan Tenn, Shahyan Soltani, Aryan Kumar

---

## Project Overview

This repository contains the Iteration 1 implementation of our Software-Defined Vehicle (SDV) pipeline. It demonstrates a complete end-to-end data flow where simulated vehicle telemetry data is generated, normalized by Eclipse Kuksa (Vehicle Data Abstraction Layer), passed through a middleware bridge layer, and persisted in an Eclipse Ditto Digital Twin backend. A Flask dashboard provides a live monitoring interface for the vehicle state.

### System Architecture

```
Vehicle Simulator (Python)
        ↓  VSS signals via gRPC
Eclipse Kuksa Databroker  (Docker)
        ↓  Python middleware bridge (500ms simulated transport delay)
Eclipse Ditto  (Docker Compose)
        ↓
Flask Dashboard  → http://127.0.0.1:5050/state
```

### Pipeline Components

| Component | Role |
|---|---|
| `simulator/vehicle_simulator.py` | Generates simulated vehicle signals (speed, steering, battery, fault) |
| Eclipse Kuksa Databroker | Vehicle data abstraction layer — receives and stores VSS signals |
| `bridge/bridge.py` | Middleware layer — reads from Kuksa, applies 500ms delay, pushes to Ditto |
| Eclipse Ditto | Digital twin backend — persists and represents vehicle state |
| `dashboard/dashboard.py` | Monitoring interface — live vehicle state at `http://127.0.0.1:5050/state` |

### Functional Modification

An engine fault detection rule is implemented in the simulator. When `Vehicle.Speed` exceeds **120 km/h**, the `EngineFault` flag is automatically set to `true` and propagated through the full pipeline into the Ditto digital twin. This simulates an overspeed fault condition and demonstrates that the pipeline supports conditional vehicle behavior.

---

## Required Software and Dependencies

- Docker Desktop (running)
- Python 3.9+
- pip

---

## Setup Instructions

### Step 1 — Start Eclipse Ditto

```bash
cd ditto/deployment/docker
docker compose up -d
```

Wait about 60 seconds for all containers to initialize. Verify Ditto is running:

```bash
curl -u ditto:ditto http://localhost:8080/api/2/things
```

You should receive an empty JSON response `[]`.

### Step 2 — Start Eclipse Kuksa Databroker

Open a new terminal in the project root folder and run:

```bash
docker run --rm -it \
  -p 55556:55555 \
  -v "$(pwd)/VSS_signals.json:/VSS_signals.json" \
  ghcr.io/eclipse-kuksa/kuksa-databroker:main \
  --insecure --vss /VSS_signals.json
```

> **Note for macOS users:** Port 55555 is unavailable on macOS due to a system conflict. We map host port 55556 to container port 55555.

Leave this terminal running.

### Step 3 — Set Up Python Virtual Environment

Open a new terminal in the project root folder:

```bash
# macOS / Linux
python3 -m venv venv
source venv/bin/activate
pip install kuksa-client requests flask
```

### Step 4 — Initialize the Ditto Digital Twin

Run these two curl commands to create the vehicle policy and digital twin in Ditto:

```bash
# Create policy
curl -X PUT http://localhost:8080/api/2/policies/org.eclipse.sdv:vehicle-policy \
  -u ditto:ditto \
  -H "Content-Type: application/json" \
  -d @ditto/policy.json

# Create vehicle Thing
curl -X PUT http://localhost:8080/api/2/things/org.eclipse.sdv:vehicle-001 \
  -u ditto:ditto \
  -H "Content-Type: application/json" \
  -d @ditto/thing.json
```

Both commands should return a `201` response. Verify:

```bash
curl -u ditto:ditto http://localhost:8080/api/2/things/org.eclipse.sdv:vehicle-001
```

---

## Running the Pipeline

You need 4 terminals total. Make sure the virtual environment is activated in terminals 3, 4, and 5.

### Terminal 1 — Eclipse Ditto (already running from setup)

### Terminal 2 — Eclipse Kuksa (already running from setup)

### Terminal 3 — Middleware Bridge

```bash
source venv/bin/activate
python3 bridge/bridge.py
```

You should see:
```
[Bridge] Connecting to Kuksa Databroker...
[Bridge] Connected. Waiting for data...
```

### Terminal 4 — Vehicle Simulator

```bash
source venv/bin/activate
python3 simulator/vehicle_simulator.py
```

You should see:
```
[Simulator] Connected. Starting signal publishing...
t=   0 | Speed=  70.0 km/h | Steering=  0.0 deg | Battery=100.0% | Fault=no
t=  16 | Speed= 120.2 km/h | Steering= 30.0 deg | Battery= 99.4% | Fault=YES ⚠️
```

### Terminal 5 — Dashboard

```bash
source venv/bin/activate
python3 dashboard/dashboard.py
```

Open `http://127.0.0.1:5050/state` in your browser to see the live vehicle state.

---

## Verifying the Pipeline

Query the digital twin directly to confirm data is flowing end-to-end:

```bash
curl -u ditto:ditto \
  http://localhost:8080/api/2/things/org.eclipse.sdv:vehicle-001 \
  | python3 -m json.tool
```

Expected output:
```json
{
    "thingId": "org.eclipse.sdv:vehicle-001",
    "features": {
        "telemetry": {
            "properties": {
                "speed": 132.4,
                "steeringAngle": 24.2,
                "batteryLevel": 98.9,
                "engineFault": true
            }
        }
    }
}
```

---

## Vehicle Signals

| Signal | VSS Path | Unit | Description |
|---|---|---|---|
| Speed | `Vehicle.Speed` | km/h | Vehicle speed (sine wave 0–140) |
| Steering Angle | `Vehicle.SteeringAngle` | degrees | Steering wheel angle (±30°) |
| Battery Level | `Vehicle.BatteryLevel` | percent | State of charge (slowly drains) |
| Engine Fault | `Vehicle.EngineFault` | boolean | True when speed > 120 km/h |

---

## Functional Modification Description

**Location in architecture:** Simulator layer → Kuksa → Bridge → Ditto `telemetry.engineFault`

**What it does:** The `EngineFault` signal is computed in `simulator/vehicle_simulator.py` using the rule:

```python
engine_fault = speed > 120.0
```

When speed exceeds 120 km/h, `EngineFault` is set to `True`. This value is published into Kuksa, picked up by the bridge, and propagated into the Ditto digital twin where it updates the `engineFault` property in real time. The dashboard reflects this as `"status": "FAULT DETECTED"`.

---

## TA Collaborator Access

The TA has been added as a collaborator using GitHub username `zubxxr`.
