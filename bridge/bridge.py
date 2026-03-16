"""
Middleware Bridge
Subscribes to Eclipse Kuksa Databroker, applies a simulated
500ms transport delay, then pushes vehicle state to Eclipse Ditto.
"""

import time
import json
import requests
from kuksa_client import KuksaClientThread

KUKSA_HOST      = "localhost"
KUKSA_PORT      = 55556
DITTO_AUTH      = ("ditto", "ditto")
TRANSPORT_DELAY = 0.5

SIGNALS = [
    "Vehicle.Speed",
    "Vehicle.SteeringAngle",
    "Vehicle.BatteryLevel",
    "Vehicle.EngineFault",
]

def run_bridge():
    config = {
        "ip": KUKSA_HOST,
        "port": KUKSA_PORT,
        "protocol": "grpc",
        "insecure": True,
    }

    print("[Bridge] Connecting to Kuksa Databroker...")
    client = KuksaClientThread(config)
    client.start()
    time.sleep(2)
    print("[Bridge] Connected. Waiting for data...\n")

    while True:
        try:
            payload = {}

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
                print(f"[Bridge] → Ditto pushed | {payload}")
            else:
                print("[Bridge] No data yet...")

        except Exception as e:
            print(f"[Bridge] Error: {e}")

        time.sleep(1)

if __name__ == "__main__":
    run_bridge()