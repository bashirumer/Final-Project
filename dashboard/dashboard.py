from flask import Flask, jsonify
import requests

app = Flask(__name__)

DITTO_URL = "http://localhost:8080/api/2/things/org.eclipse.sdv:vehicle-001"
DITTO_AUTH = ("ditto", "ditto")


def get_telemetry():
    response = requests.get(DITTO_URL, auth=DITTO_AUTH)
    if response.status_code != 200:
        return None

    thing = response.json()
    return thing.get("features", {}).get("telemetry", {}).get("properties", {})


@app.route("/state")
def state():
    props = get_telemetry()
    if props is None:
        return jsonify({"error": "Could not reach Ditto"}), 500

    engine_fault = props.get("engineFault")

    return jsonify({
        "vehicle_id": "org.eclipse.sdv:vehicle-001",
        "speed_kmh": props.get("speed"),
        "steering_angle_deg": props.get("steeringAngle"),
        "battery_level_pct": props.get("batteryLevel"),
        "engine_fault": engine_fault,
        "status": "FAULT DETECTED" if engine_fault else "NORMAL"
    })


@app.route("/vehicle/signals/speed")
def vehicle_speed():
    props = get_telemetry()
    if props is None:
        return jsonify({"error": "Could not reach Ditto"}), 500

    return jsonify({
        "name": "speed",
        "value": props.get("speed"),
        "unit": "km/h"
    })


@app.route("/vehicle/signals/steering-angle")
def steering_angle():
    props = get_telemetry()
    if props is None:
        return jsonify({"error": "Could not reach Ditto"}), 500

    return jsonify({
        "name": "steeringAngle",
        "value": props.get("steeringAngle"),
        "unit": "degrees"
    })


@app.route("/vehicle/powertrain/battery")
def battery():
    props = get_telemetry()
    if props is None:
        return jsonify({"error": "Could not reach Ditto"}), 500

    return jsonify({
        "name": "batteryLevel",
        "value": props.get("batteryLevel"),
        "unit": "percent"
    })


@app.route("/diagnostics/faults")
def diagnostics_faults():
    props = get_telemetry()
    if props is None:
        return jsonify({"error": "Could not reach Ditto"}), 500

    faults = []
    if props.get("engineFault"):
        faults.append({
            "code": "ENGINE_FAULT",
            "state": "active",
            "description": "Engine fault triggered because speed exceeded 120 km/h"
        })

    return jsonify({"faults": faults})


@app.route("/diagnostics/status")
def diagnostics_status():
    props = get_telemetry()
    if props is None:
        return jsonify({"error": "Could not reach Ditto"}), 500

    return jsonify({
        "status": "FAULT DETECTED" if props.get("engineFault") else "NORMAL"
    })


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5050, debug=True)
