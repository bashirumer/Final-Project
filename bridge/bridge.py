"""
Middleware Bridge
Subscribes to Eclipse Kuksa Databroker, applies a simulated
500ms transport delay, then pushes vehicle state to Eclipse Ditto.

Iteration 2 additions:
- Latency measurement from Kuksa read to Ditto confirmation
- Latency results logged to latency_log.csv for analysis
"""

import time
import json
import csv
import os
import requests
from kuksa_client import KuksaClientThread

KUKSA_HOST      = "localhost"
KUKSA_PORT      = 55556
DITTO_AUTH      = ("ditto", "ditto")
TRANSPORT_DELAY = 0.5
LATENCY_LOG     = "latency_log.csv"

SIGNALS = [
    "Vehicle.Speed",
    "Vehicle.SteeringAngle",
    "Vehicle.BatteryLevel",
    "Vehicle.EngineFault",
    "Vehicle.BatteryWarning",
]

def init_latency_log():
    if not os.path.exists(LATENCY_LOG):
        with open(LATENCY_LOG, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "latency_ms", "speed", "engineFault"])

def log_latency(latency_ms, speed, engine_fault):
    with open(LATENCY_LOG, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            time.strftime("%H:%M:%S"),
            round(latency_ms, 2),
            round(speed, 2) if speed else 0,
            engine_fault
        ])

def run_bridge():
    config = {
        "ip": KUKSA_HOST,
        "port": KUKSA_PORT,
        "protocol": "grpc",
        "insecure": True,
    }

    init_latency_log()

    print("[Bridge] Connecting to Kuksa Databroker...")
    client = KuksaClientThread(config)
    client.start()
    time.sleep(2)
    print("[Bridge] Connected. Waiting for data...\n")
    print(f"[Bridge] Logging latency to: {LATENCY_LOG}\n")

    while True:
        try:
            payload = {}

            # Start latency timer — measures full round trip Kuksa → Ditto
            start_time = time.time()

            for signal in SIGNALS:
                result = client.getValue(signal)
                parsed = json.loads(result)
                value = parsed.get("value", {}).get("value")
                if value is not None:
                    key = signal.split(".")[-1]
                    key = key[0].lower() + key[1:]
                    if value is True or value == "true":
                        value = True
                    elif value is False or value == "false":
                        value = False
                    else:
                        try:
                            value = float(value)
                        except (ValueError, TypeError):
                            pass
                    if key == "engineFault":
                        value = bool(value)
                    payload[key] = value

            # After collecting all signals, push to Ditto
            if payload:
                time.sleep(TRANSPORT_DELAY)
                for prop_key, prop_value in payload.items():
                    prop_url = (
                        "http://localhost:8080/api/2/things/"
                        f"org.eclipse.sdv:vehicle-001/features/telemetry/properties/{prop_key}"
                    )
                    requests.put(
                        prop_url,
                        json=prop_value,
                        auth=DITTO_AUTH,
                        headers={"Content-Type": "application/json"}
                    )

                # Stop latency timer after Ditto confirms
                end_time = time.time()
                latency_ms = (end_time - start_time) * 1000

                # Log to CSV
                log_latency(
                    latency_ms,
                    payload.get("speed", 0),
                    payload.get("engineFault", False)
                )

                print(
                    f"[Bridge] → Ditto pushed | "
                    f"Latency: {latency_ms:.2f}ms | "
                    f"{payload}"
                )
            else:
                print("[Bridge] No data yet...")

        except Exception as e:
            print(f"[Bridge] Error: {e}")

        time.sleep(1)

if __name__ == "__main__":
    run_bridge()