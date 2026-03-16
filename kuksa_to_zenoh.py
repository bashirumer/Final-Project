"""
Middleware Bridge
Subscribes to Eclipse Kuksa Databroker
"""

import time
import json
import requests
from kuksa_client import KuksaClientThread
import zenoh

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

battery_key = 'myvehicle/stats/batteryLevel'
steering_angle_key = 'myvehicle/stats/steeringAngle'
speed_key = 'myvehicle/stats/speed'
engine_fault_key = 'myvehicle/stats/engineFault'

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

    session = zenoh.open(zenoh.Config())
    battery_pub = session.declare_publisher(battery_key)
    steering_angle_pub = session.declare_publisher(steering_angle_key)
    speed_pub = session.declare_publisher(speed_key)
    engine_fault_pub = session.declare_publisher(engine_fault_key)

    while True:
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
                        if key == 'batteryLevel':
                            battery_pub.put(str(value))
                            print(f"Battery: {value}")
                        elif key == 'steeringAngle':
                            steering_angle_pub.put(str(value))
                            print(f"Angle: {value}")
                        elif key == 'speed':
                            speed_pub.put(str(value))
                            print(f"Speed: {value}")
                    except (ValueError, TypeError):
                        pass
                if key == "engineFault":
                    value = bool(value)
                    engine_fault_pub.put(str(value))
                    print(f"Fault: {value}")
                payload[key] = value
        time.sleep(5)
            
if __name__ == "__main__":
    run_bridge()