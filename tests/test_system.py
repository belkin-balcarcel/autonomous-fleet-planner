from backend.anomaly_detector import detect_sensor_anomalies, predict_battery_ticks_remaining
from backend.app import MissionRequest, get_fleet, health_check, simulate_mission
from backend.database import init_db
from backend.pathfinder import astar_route


def test_astar_avoids_no_fly_zones():
    obstacles = {(3, 1), (3, 2), (3, 3), (3, 4), (3, 5)}
    route = astar_route((0, 0), (6, 6), obstacles, grid_size=10)
    assert route is not None
    assert next(iter(route)) == (0, 0)
    assert tuple(route)[-1] == (6, 6)
    for point in route:
        assert point not in obstacles


def test_astar_returns_none_when_blocked():
    obstacles = {
        (4, 4), (4, 5), (4, 6),
        (5, 4),         (5, 6),
        (6, 4), (6, 5), (6, 6)
    }
    route = astar_route((0, 0), (5, 5), obstacles, grid_size=10)
    assert route is None


def test_ml_battery_prediction_and_anomalies():
    ticks = list((0, 1, 2, 3, 4))
    batteries = list((100.0, 99.0, 98.0, 97.0, 96.0))
    forecast = predict_battery_ticks_remaining(ticks, batteries, rtl_threshold=20.0)
    assert forecast.get("drain_rate_per_tick") == -1.0
    assert forecast.get("estimated_ticks_remaining") == 76.0
    assert forecast.get("low_battery_risk") is False

    altitudes = list((120.0, 120.1, 119.9, 120.0, 120.2, 210.0, 120.0))
    anomalies = detect_sensor_anomalies(altitudes, z_threshold=2.0)
    assert 5 in anomalies


def test_api_endpoints_and_mission_simulation():
    init_db()
    health = health_check()
    assert health.get("status") == "online"

    fleet = get_fleet()
    assert len(fleet.get("aircraft")) >= 3

    req = MissionRequest(
        aircraft_id="VBAT-01",
        start=(1, 1),
        goal=(10, 10),
        no_fly_zones=list(((5, 4), (5, 5), (5, 6))),
        grid_size=15
    )
    data = simulate_mission(req)
    assert data.get("aircraft_id") == "VBAT-01"
    assert len(data.get("waypoints")) > 0
    assert len(data.get("telemetry")) > 0
