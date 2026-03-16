"""
Simple Vehicle Dashboard
Reads live vehicle state from Eclipse Ditto and displays it at
http://127.0.0.1:5050/state
"""

from flask import Flask, jsonify
import requests

app = Flask(__name__)

DITTO_URL = "http://localhost:8080/api/2/things/org.eclipse.sdv:vehicle-001"
DITTO_AUTH = ("ditto", "ditto")

@app.route("/state")
def state():
    response = requests.get(DITTO_URL, auth=DITTO_AUTH)
    if response.status_code == 200:
        thing = response.json()
        props = thing.get("features", {}).get("telemetry", {}).get("properties", {})
        return jsonify({
            "vehicle_id": "org.eclipse.sdv:vehicle-001",
            "speed_kmh": props.get("speed"),
            "steering_angle_deg": props.get("steeringAngle"),
            "battery_level_pct": props.get("batteryLevel"),
            "engine_fault": props.get("engineFault"),
            "status": "FAULT DETECTED" if props.get("engineFault") else "NORMAL"
        })
    return jsonify({"error": "Could not reach Ditto"}), 500

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5050, debug=True)