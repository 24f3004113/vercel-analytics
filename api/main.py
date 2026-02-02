from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json
import os
import statistics

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

DATA_FILE = os.path.join(os.path.dirname(__file__), "telemetry.json")

with open(DATA_FILE, "r") as f:
    data = json.load(f)

@app.post("/")
def analytics(payload: dict):
    regions = payload.get("regions", [])
    threshold = payload.get("threshold_ms", 0)

    results = {}

    for region in regions:
        region_records = [r for r in data if r["region"] == region]

        latencies = [r["latency_ms"] for r in region_records]
        uptimes = [r["uptime_pct"] for r in region_records]

        avg_latency = statistics.mean(latencies)
        p95_latency = sorted(latencies)[int(0.95 * len(latencies)) - 1]
        avg_uptime = statistics.mean(uptimes)
        breaches = sum(1 for l in latencies if l > threshold)

        results[region] = {
            "avg_latency": avg_latency,
            "p95_latency": p95_latency,
            "avg_uptime": avg_uptime,
            "breaches": breaches
        }

    return results
