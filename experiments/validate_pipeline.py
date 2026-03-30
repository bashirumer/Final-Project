"""
Functional Validation Script
Queries Ditto and verifies vehicle state is being updated
"""
import requests
import time

DITTO_URL = "http://localhost:8080/api/2/things/org.eclipse.sdv:vehicle-001"
AUTH = ("ditto", "ditto")

print("[Validation] Checking pipeline...")

# Take two readings 3 seconds apart
r1 = requests.get(DITTO_URL, auth=AUTH).json()
props1 = r1["features"]["telemetry"]["properties"]
print(f"[t=0s] Speed: {props1['speed']:.2f} km/h")

time.sleep(3)

r2 = requests.get(DITTO_URL, auth=AUTH).json()
props2 = r2["features"]["telemetry"]["properties"]
print(f"[t=3s] Speed: {props2['speed']:.2f} km/h")

# Check values changed
if props1["speed"] != props2["speed"]:
    print("[PASS] Pipeline is live — values are updating correctly")
else:
    print("[FAIL] Values did not change — pipeline may be stopped")

# Check engine fault logic
speed = props2["speed"]
fault = props2["engineFault"]
if speed > 120 and fault == True:
    print("[PASS] Engine fault logic correct — fault active above 120 km/h")
elif speed <= 120 and fault == False:
    print("[PASS] Engine fault logic correct — no fault below 120 km/h")
else:
    print("[FAIL] Engine fault logic mismatch")
```

---

## Step 6 — Updated Folder Structure

Your repo on the `iteration-2` branch should look like:
```
sdv-pipeline/
├── bridge/
│   └── bridge.py              ← updated with latency measurement
├── simulator/
│   └── vehicle_simulator.py   ← updated with variable rate
├── experiments/
│   ├── analyze_latency.py     ← new
│   └── validate_pipeline.py   ← new
├── dashboard/
│   └── dashboard.py
├── ditto/
│   ├── policy.json
│   └── thing.json
├── VSS_signals.json
├── latency_log.csv            ← generated when bridge runs
└── README.md                  ← updated