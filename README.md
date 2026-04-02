# SOFE3290: Software Quality & Project Management
## Iteration 2: Extended SDV Pipeline — Fault Detection, Latency Measurement & Variable Publish Rate
**Project Group: 24**

**Members:** Umer Bashir, Abdul Aziz Syed, Nathan Tenn, Shahyan Soltani, Aryan Kumar

---

## Project Overview

This repository contains the complete Iteration 1 and Iteration 2 implementation of our Software-Defined Vehicle (SDV) pipeline. Simulated vehicle telemetry is generated, normalized by Eclipse Kuksa, passed through a middleware bridge, and persisted in an Eclipse Ditto Digital Twin backend. A Flask dashboard provides live monitoring of vehicle state.

Iteration 2 extends the baseline with three additions: a **battery critical warning fault**, **configurable signal publish rates** for load testing, and **end-to-end latency measurement** across the pipeline.

---

## System Architecture
```
Vehicle Simulator (Python)
        ↓  *VSS signals via gRPC*
Eclipse Kuksa Databroker  (Docker)
        ↓  *Python middleware bridge (500ms simulated transport delay)*
Eclipse Ditto  (Docker Compose)
        ↓
Flask Dashboard (OpenSOVD style) → http://127.0.0.1:5050/state
```

---

## Pipeline Components

| Component | Role |
|-----------|------|
| `simulator/vehicle_simulator.py` | Generates simulated vehicle signals (speed, steering, battery, engineFault, batteryWarning) |
| Eclipse Kuksa Databroker | Vehicle data abstraction layer — receives and stores VSS signals |
| `bridge/bridge.py` | Middleware layer — reads from Kuksa, applies 500ms delay, pushes to Ditto, logs latency |
| Eclipse Ditto | Digital twin backend — persists and represents vehicle state |
| `dashboard/dashboard.py` | OpenSOVD-style monitoring interface at `http://127.0.0.1:5050/state` |
| `experiments/analyze_latency.py` | Reads `latency_log.csv` and prints summary statistics |
| `experiments/validate_pipeline.py` | Automated end-to-end functional validation script |

---

## Iteration 1 — Functional Modification

An engine fault detection rule is implemented in the simulator. When `Vehicle.Speed` exceeds **120 km/h**, the `EngineFault` flag is automatically set to `true` and propagated through the full pipeline into the Ditto digital twin.
```python
engine_fault = speed > 120.0
```

---

## Iteration 2 — Extensions

### Extension 1: Battery Critical Warning Fault

A second fault condition was added. When `Vehicle.BatteryLevel` drops below **20%**, the `BatteryWarning` flag is set to `true` and propagated through the full pipeline into Ditto.
```python
BATTERY_LOW_THRESHOLD = 20.0
battery_warning = battery < BATTERY_LOW_THRESHOLD
client.setValue("Vehicle.BatteryWarning", str(battery_warning).lower())
```

`Vehicle.BatteryWarning` was added to `VSS_signals.json`, `ditto/thing.json`, and the `SIGNALS` list in `bridge/bridge.py`.

---

### Extension 2: Variable Signal Publish Rate

The simulator accepts an optional command-line argument to set the publish rate, enabling structured load testing without any code changes between trials:
```bash
python3 simulator/vehicle_simulator.py 1.0   # 1 msg/s (default — matches Iteration 1)
python3 simulator/vehicle_simulator.py 0.5   # 2 msg/s
python3 simulator/vehicle_simulator.py 0.1   # 10 msg/s
```

If no argument is provided the simulator defaults to **1 msg/s**, preserving Iteration 1 behavior exactly.

---

### Extension 3: End-to-End Latency Measurement

The bridge now measures time elapsed from the start of each Kuksa read cycle to the completion of all Ditto HTTP PUT requests. Latency is printed inline in the bridge terminal and automatically logged to `latency_log.csv`.
```
latency_log.csv  →  timestamp, latency_ms, speed, engineFault
```

To analyze results after a trial:
```bash
python3 experiments/analyze_latency.py
```

---

## Vehicle Signals

| Signal | VSS Path | Unit | Description |
|--------|----------|------|-------------|
| Speed | `Vehicle.Speed` | km/h | Vehicle speed (sine wave 0–140) |
| Steering Angle | `Vehicle.SteeringAngle` | degrees | Steering wheel angle (±30°) |
| Battery Level | `Vehicle.BatteryLevel` | percent | State of charge (slowly drains) |
| Engine Fault | `Vehicle.EngineFault` | boolean | `true` when speed > 120 km/h |
| **Battery Warning** | `Vehicle.BatteryWarning` | boolean | `true` when battery < 20% |

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

Wait ~60 seconds for all containers to initialize. Verify:
```bash
curl -u ditto:ditto http://localhost:8080/api/2/things
```

### Step 2 — Start Eclipse Kuksa Databroker
```bash
docker run --rm -it \
  -p 55556:55555 \
  -v "$(pwd)/VSS_signals.json:/VSS_signals.json" \
  ghcr.io/eclipse-kuksa/kuksa-databroker:main \
  --insecure --vss /VSS_signals.json
```

> **macOS note:** Port 55555 is unavailable on macOS. We map host port **55556** to container port 55555.

### Step 3 — Set Up Python Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install kuksa-client requests flask
```

### Step 4 — Initialize the Ditto Digital Twin
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

Both commands should return `201`. Verify:
```bash
curl -u ditto:ditto http://localhost:8080/api/2/things/org.eclipse.sdv:vehicle-001
```

---

## Running the Pipeline

You need **5 terminals**. Activate the virtual environment in terminals 3, 4, and 5.

**Terminal 1 — Eclipse Ditto** (already running from setup)

**Terminal 2 — Eclipse Kuksa** (already running from setup)

**Terminal 3 — Middleware Bridge**
```bash
source venv/bin/activate
python3 bridge/bridge.py
```

**Terminal 4 — Vehicle Simulator**
```bash
source venv/bin/activate
python3 simulator/vehicle_simulator.py        # default 1 msg/s
python3 simulator/vehicle_simulator.py 0.5    # or specify a rate
```

**Terminal 5 — Dashboard**
```bash
source venv/bin/activate
python3 dashboard/dashboard.py
```

Open **http://127.0.0.1:5050/state** in your browser to see the live vehicle state.

---

## Dashboard Endpoints

| Endpoint | Description |
|----------|-------------|
| `/state` | Full snapshot of vehicle state |
| `/vehicle/signals/speed` | Current vehicle speed |
| `/vehicle/signals/steering-angle` | Current steering angle |
| `/vehicle/powertrain/battery` | Battery level |
| `/diagnostics/status` | Overall diagnostic status |
| `/diagnostics/faults` | List of active faults |

---

## Verifying the Pipeline
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
                "engineFault": true,
                "batteryWarning": false
            }
        }
    }
}
```

---

## Running Latency Experiments
```bash
# Clear previous results
rm latency_log.csv

# Run simulator for 60 seconds at desired rate, then Ctrl+C
python3 simulator/vehicle_simulator.py 1.0

# Analyze
python3 experiments/analyze_latency.py
```

Repeat for each rate (`1.0`, `0.5`, `0.1`) and record the summary statistics.

---

## Branch Structure

| Branch | Contents |
|--------|----------|
| `main` | Iteration 1 stable baseline |
| `iteration-2` | All Iteration 2 extensions |

---

## TA Collaborator Access

The TA has been added as a collaborator using GitHub username **zubxxr**.
