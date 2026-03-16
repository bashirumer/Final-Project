import zenoh
import time
import requests

DITTO_AUTH = ("ditto", "ditto")

def getStats():
    with zenoh.open(zenoh.Config()) as session:
        payload = {}
        battery = 0
        steering_angle = 0
        speed = 0
        engine_fault = False

        replies = session.get('myvehicle/stats/*')
        for reply in replies:
            if reply.ok.key_expr == "myvehicle/stats/batteryLevel":
                battery = reply.ok.payload.to_string()
                payload['batteryLevel'] = battery
            elif reply.ok.key_expr == "myvehicle/stats/steeringAngle":
                steering_angle = reply.ok.payload.to_string()
                payload['steeringAngle'] = steering_angle
            elif reply.ok.key_expr == "myvehicle/stats/speed":
                speed = reply.ok.payload.to_string()
                payload['speed'] = speed
            elif reply.ok.key_expr == "myvehicle/stats/engineFault":
                engine_fault = reply.ok.payload.to_string()
                payload['engineFault'] = engine_fault

        session.close()
        return payload

def main():
    while True:
        payload = getStats()

        if payload:
            for prop_key, prop_value in payload.items():
                prop_url = (
                    "http://localhost:8080/api/2/things/"
                    f"org.eclipse.sdv:vehicle-001/features/telemetry/properties/{prop_key}")
                requests.put(
                    prop_url,
                    json=prop_value,
                    auth=DITTO_AUTH,
                    headers={"Content-Type": "application/json"}
                )
            print(f"[Bridge] → Ditto pushed | {payload}")
        else:
            print("[Bridge] No data yet...")

        time.sleep(1)
 
if __name__ == "__main__":
    main()
