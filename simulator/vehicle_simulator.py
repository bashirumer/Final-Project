"""
Vehicle Simulator
Publishes speed, steering angle, battery level, and engine fault
into Eclipse Kuksa Databroker.

Functional Modification:
  EngineFault is set to True when speed exceeds 120 km/h,
  simulating an overspeed fault condition.

Iteration 2 additions:
  - Variable publish rate via command line argument
  - Allows testing system behavior at different signal frequencies
  - Usage: python3 vehicle_simulator.py [rate]
  - Example: python3 vehicle_simulator.py 0.5  (publishes every 0.5s)
  - Default rate is 1.0 second if no argument provided
"""

import time
import math
import random
import json
import sys
from kuksa_client import KuksaClientThread

KUKSA_HOST = "localhost"
KUKSA_PORT = 55556

OVERSPEED_THRESHOLD   = 120.0   # km/h
BATTERY_LOW_THRESHOLD = 20.0    # percent

def get_config():
    return {
        "ip": KUKSA_HOST,
        "port": KUKSA_PORT,
        "protocol": "grpc",
        "insecure": True,
    }

def simulate():
    # Get publish rate from command line argument, default to 1.0 second
    publish_rate = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0

    print("[Simulator] Connecting to Kuksa Databroker...")
    client = KuksaClientThread(get_config())
    client.start()
    client.authorize("")
    print("[Simulator] Connected. Starting signal publishing...\n")
    print(f"[Simulator] Publish rate: every {publish_rate}s "
          f"({1/publish_rate:.1f} messages/sec)\n")

    t = 0
    battery = 100.0

    while True:
        # Speed: sine wave between 0 and 140 km/h
        speed = round(70 + 70 * math.sin(t * 0.05), 2)

        # Steering: oscillates between -30 and +30 degrees
        steering = round(30 * math.sin(t * 0.1), 2)

        # Battery: slowly drains over time
        battery = round(max(0.0, battery - random.uniform(0.01, 0.05)), 2)

        # Iteration 1 Functional Modification: fault triggered above 120 km/h
        engine_fault = speed > OVERSPEED_THRESHOLD

        # Iteration 2 Extension: battery critical warning below 20%
        battery_warning = battery < BATTERY_LOW_THRESHOLD

        # Publish all signals to Kuksa
        client.setValue("Vehicle.Speed",          str(speed))
        client.setValue("Vehicle.SteeringAngle",  str(steering))
        client.setValue("Vehicle.BatteryLevel",   str(battery))
        client.setValue("Vehicle.EngineFault",    str(engine_fault).lower())
        client.setValue("Vehicle.BatteryWarning", str(battery_warning).lower())

        print(
            f"t={t:4d} | "
            f"Speed={speed:6.1f} km/h | "
            f"Steering={steering:5.1f} deg | "
            f"Battery={battery:5.1f}% | "
            f"EngFault={'YES ⚠️ ' if engine_fault    else 'no '} | "
            f"BattWarn={'YES 🔋 ' if battery_warning else 'no '} | "
            f"Rate={publish_rate}s"
        )

        t += 1
        time.sleep(publish_rate)

if __name__ == "__main__":
    simulate()