# Autonomous Fleet & Mission Planner

**Live Demo:** https://autonomous-fleet-planner.onrender.com

A full-stack autonomous aircraft mission-planning and real-time flight telemetry platform built with **C++17**, **Python (FastAPI)**, **SQLite**, **NumPy**, and an interactive **HTML5/CSS3/JavaScript** tactical radar interface.

## Architecture & Engineering Highlights
- **Deterministic C++17 Flight Telemetry Engine (`cpp-engine/`):** Simulates fixed-tick aircraft kinematics (GPS coordinates, altitude oscillation, airspeed, battery depletion, and automatic `LOW_BATTERY_RTL` safety triggers) outputting structured JSON telemetry packets.
- **A* (A-Star) Obstacle-Avoidance Pathfinder (`backend/pathfinder.py`):** Implements an 8-directional spatial graph search using a min-heap priority queue (`heapq`) and Euclidean heuristic cost function to compute collision-free routes around dynamic no-fly zones.
- **Statistical ML Battery & Anomaly Detection (`backend/anomaly_detector.py`):** Uses NumPy least-squares linear regression (`np.polyfit`) to predict remaining flight ticks until the 20% Return-to-Launch threshold, paired with Z-score outlier detection for sensor spikes.
- **FastAPI REST Backend & Relational SQL Persistence (`backend/app.py`, `backend/database.py`):** Orchestrates C++ simulation runs, persists fleet status and mission history in normalized SQLite tables, and serves the interactive web dashboard.
- **Automated Testing & CI/CD (`.github/workflows/ci.yml`, `tests/`):** Automated `pytest` suite and GitHub Actions workflow that compiles the C++ engine and runs unit/integration tests on every push.

## Local Quick Start
```bash
# 1. Compile the C++ telemetry engine
g++ -std=c++17 cpp-engine/main.cpp -o cpp-engine/telemetry_sim.exe

# 2. Create virtual environment and install dependencies
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 3. Run automated tests
pytest -v

# 4. Launch the live web dashboard
uvicorn backend.app:app --reload
```
Once the local server is running, open `http://127.0.0.1:8000` in your browser—or test the live cloud deployment anytime at **[https://autonomous-fleet-planner.onrender.com](https://autonomous-fleet-planner.onrender.com)**.


