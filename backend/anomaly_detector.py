import numpy as np
from typing import List, Dict, Any


def predict_battery_ticks_remaining(
    ticks: List[int],
    battery_readings: List[float],
    rtl_threshold: float = 20.0
) -> Dict[str, Any]:
    """
    Uses linear regression (least squares) to estimate battery drain rate
    and predict remaining flight ticks before hitting the RTL safety threshold.
    """
    if len(ticks) < 2 or len(ticks) != len(battery_readings):
        return {
            "drain_rate_per_tick": 0.0,
            "estimated_ticks_remaining": None,
            "low_battery_risk": False
        }

    x = np.array(ticks, dtype=float)
    y = np.array(battery_readings, dtype=float)

    # Fit first-degree polynomial: battery = slope * tick + intercept
    slope, intercept = np.polyfit(x, y, 1)
    current_battery = float(y[-1])

    if slope >= -1e-6:
        return {
            "drain_rate_per_tick": round(float(slope), 4),
            "estimated_ticks_remaining": None,
            "low_battery_risk": current_battery <= rtl_threshold
        }

    target_tick = (rtl_threshold - intercept) / slope
    remaining = max(0.0, float(target_tick - x[-1]))

    return {
        "drain_rate_per_tick": round(float(slope), 4),
        "estimated_ticks_remaining": round(remaining, 1),
        "low_battery_risk": remaining <= 15.0 or current_battery <= rtl_threshold
    }


def detect_sensor_anomalies(
    values: List[float],
    z_threshold: float = 2.5
) -> List[int]:
    """
    Identifies indices of anomalous telemetry readings using Z-score outlier detection.
    """
    if len(values) < 4:
        return []

    arr = np.array(values, dtype=float)
    mean = float(np.mean(arr))
    std = float(np.std(arr))

    if std < 1e-6:
        return []

    z_scores = np.abs((arr - mean) / std)
    return [int(idx) for idx in np.where(z_scores > z_threshold)[0]]


if __name__ == "__main__":
    sample_ticks = [0, 1, 2, 3, 4, 5]
    sample_battery = [100.0, 99.55, 99.10, 98.65, 98.20, 97.75]
    print("Battery forecast:", predict_battery_ticks_remaining(sample_ticks, sample_battery))

    sample_altitudes = [120.0, 120.2, 119.9, 120.1, 120.3, 185.0, 120.0]
    print("Altitude anomaly indices:", detect_sensor_anomalies(sample_altitudes, z_threshold=2.0))
