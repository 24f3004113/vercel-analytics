from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
import numpy as np
from pathlib import Path

app = FastAPI(title="eShopCo Latency Checker")

# CORS as required
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],          # or just ["POST"]
    allow_headers=["*"],
)

# Load data once at startup
DATA_PATH = Path(__file__).parent.parent / "telemetry.json"  # root of project

try:
    with open(DATA_PATH, "r") as f:
        raw_data = json.load(f)
    # Convert to list of dicts → DataFrame-like structure
    data = raw_data
except Exception as e:
    raise RuntimeError(f"Cannot load telemetry.json: {e}")

# Optional: pre-group for speed (recommended in serverless)
from collections import defaultdict
grouped = defaultdict(list)
for record in data:
    grouped[record["region"]].append(record)

@app.post("/")
async def check_latency(request: Request):
    try:
        body = await request.json()
        regions = body.get("regions", [])
        threshold = float(body.get("threshold_ms", 0))
    except:
        raise HTTPException(400, "Invalid JSON body")

    if not isinstance(regions, list) or not regions:
        raise HTTPException(400, "'regions' must be a non-empty list")

    result = {}

    for region in regions:
        records = grouped.get(region, [])
        if not records:
            result[region] = {
                "avg_latency": 0.0,
                "p95_latency": 0.0,
                "avg_uptime": 0.0,
                "breaches": 0
            }
            continue

        latencies = np.array([r["latency_ms"] for r in records])
        uptimes   = np.array([r["uptime_pct"] / 100.0 for r in records])  # % → 0-1

        avg_latency = float(np.mean(latencies))
        p95_latency = float(np.percentile(latencies, 95))
        avg_uptime  = float(np.mean(uptimes))
        breaches    = int(np.sum(latencies > threshold))

        result[region] = {
            "avg_latency": round(avg_latency, 2),
            "p95_latency": round(p95_latency, 2),
            "avg_uptime":  round(avg_uptime,  3),
            "breaches": breaches
        }

    return result