"""
Vehicle Simulator
Publishes speed, steering angle, battery level, and engine fault
into Eclipse Kuksa Databroker.

Functional Modification:
  EngineFault is set to True when speed exceeds 120 km/h,
  simulating an overspeed fault condition.
"""

import time
import math
import random
import json
from kuksa_client import KuksaClientThread

KUKSA_HOST = "localhost"
KUKSA_PORT = 55556

def get_config():
    return {
        "ip": KUKSA_HOST,
        "port": KUKSA_PORT,
        "protocol": "grpc",
        "insecure": True,
    }

def simulate():
    print("[Simulator] Connecting to Kuksa Databroker...")
    client = KuksaClientThread(get_config())
    client.start()
    client.authorize("")
    print("[Simulator] Connected. Starting signal publishing...\n")

    t = 0
    battery = 100.0

    while True:
        # Speed: sine wave between 0 and 140 km/h
        speed = round(70 + 70 * math.sin(t * 0.05), 2)

        # Steering: oscillates between -30 and +30 degrees
        steering = round(30 * math.sin(t * 0.1), 2)

        # Battery: slowly drains over time
        battery = round(max(0.0, battery - random.uniform(0.01, 0.05)), 2)

        # Functional Modification: fault triggered above 120 km/h
        engine_fault = speed > 120.0

        client.setValue("Vehicle.Speed", str(speed))
        client.setValue("Vehicle.SteeringAngle", str(steering))
        client.setValue("Vehicle.BatteryLevel", str(battery))
        client.setValue("Vehicle.EngineFault", str(engine_fault).lower())

        print(
            f"t={t:4d} | "
            f"Speed={speed:6.1f} km/h | "
            f"Steering={steering:5.1f} deg | "
            f"Battery={battery:5.1f}% | "
            f"Fault={'YES ⚠️' if engine_fault else 'no'}"
        )

        t += 1
        time.sleep(1)

if __name__ == "__main__":
    simulate()