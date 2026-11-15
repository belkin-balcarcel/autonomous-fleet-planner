import json
import math
import os
import subprocess
from contextlib import asynccontextmanager
from typing import List, Tuple

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.anomaly_detector import detect_sensor_anomalies, predict_battery_ticks_remaining
from backend.database import init_db, list_aircraft, list_missions, log_mission
from backend.pathfinder import astar_route


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Autonomous Fleet & Mission Planner API",
    description="Real-time flight telemetry, A* obstacle avoidance, and ML anomaly detection.",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class MissionRequest(BaseModel):
    aircraft_id: str = "VBAT-01"
    start: Tuple[int, int] = (1, 1)
    goal: Tuple[int, int] = (14, 14)
    no_fly_zones: List[Tuple[int, int]] = [(6, 5), (6, 6), (6, 7), (7, 7), (8, 7)]
    grid_size: int = 20


def run_cpp_or_fallback_sim(
    aircraft_id: str, start_lat: float, start_lon: float, dest_lat: float, dest_lon: float
) -> List[dict]:
    """Executes the compiled C++ telemetry engine if available, with a deterministic fallback."""
    exe_path = os.path.join("cpp-engine", "telemetry_sim.exe")
    if os.path.exists(exe_path):
        proc = subprocess.run(
            [exe_path, aircraft_id, str(start_lat), str(start_lon), str(dest_lat), str(dest_lon)],
            capture_output=True,
            text=True,
            check=True
        )
        return [json.loads(line) for line in proc.stdout.strip().splitlines() if line.strip()]

    # Cross-platform fallback for Linux cloud containers
    packets = []
    lat, lon = start_lat, start_lon
    battery = 100.0
    for tick in range(0, 60):
        dlat, dlon = dest_lat - lat, dest_lon - lon
        dist = math.hypot(dlat, dlon)
        status = "ARRIVED" if dist < 0.0005 else ("LOW_BATTERY_RTL" if battery <= 20.0 else "EN_ROUTE")
        packets.append({
            "aircraft_id": aircraft_id,
            "tick": tick,
            "latitude": round(lat, 6),
            "longitude": round(lon, 6),
            "altitude_m": round(120.0 + math.sin(tick * 0.3) * 0.4, 2),
            "airspeed_mps": 0.0 if status != "EN_ROUTE" else 22.5,
            "battery_pct": round(battery, 2),
            "status": status
        })
        if status != "EN_ROUTE":
            break
        lat += (dlat / dist) * 0.0008
        lon += (dlon / dist) * 0.0008
        battery = max(20.0, battery - 0.45)
    return packets


@app.get("/api/health")
def health_check():
    return {"status": "online", "service": "autonomous-fleet-planner"}


@app.get("/api/fleet")
def get_fleet():
    return {"aircraft": list_aircraft()}


@app.get("/api/missions")
def get_missions():
    return {"missions": list_missions()}


@app.post("/api/missions/simulate")
def simulate_mission(req: MissionRequest):
    obstacles = set(req.no_fly_zones)
    waypoints = astar_route(req.start, req.goal, obstacles, grid_size=req.grid_size)
    if waypoints is None:
        raise HTTPException(status_code=400, detail="No safe route found around no-fly zones.")

    # Map grid coordinates to Dallas-Fort Worth airspace coordinates
    base_lat, base_lon = 32.7767, -96.7970
    start_lat = base_lat + req.start * 0.001
    start_lon = base_lon + req.start * 0.001
    dest_lat = base_lat + req.goal * 0.001
    dest_lon = base_lon + req.goal * 0.001

    telemetry = run_cpp_or_fallback_sim(req.aircraft_id, start_lat, start_lon, dest_lat, dest_lon)
    ticks = [p["tick"] for p in telemetry]
    batteries = [p["battery_pct"] for p in telemetry]
    altitudes = [p["altitude_m"] for p in telemetry]

    ml_forecast = predict_battery_ticks_remaining(ticks, batteries)
    anomalies = detect_sensor_anomalies(altitudes)
    final_packet = telemetry[-1]

    mission_id = log_mission(
        aircraft_id=req.aircraft_id,
        start_coord=f"{req.start},{req.start}",
        goal_coord=f"{req.goal},{req.goal}",
        waypoint_count=len(waypoints),
        final_status=final_packet["status"],
        final_battery_pct=final_packet["battery_pct"]
    )

    return {
        "mission_id": mission_id,
        "aircraft_id": req.aircraft_id,
        "waypoints": waypoints,
        "no_fly_zones": req.no_fly_zones,
        "telemetry": telemetry,
        "ml_battery_forecast": ml_forecast,
        "altitude_anomaly_ticks": anomalies,
        "summary": final_packet
    }
