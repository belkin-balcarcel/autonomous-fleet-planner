#include "Telemetry.h"
#include <iostream>
#include <iomanip>
#include <sstream>
#include <cmath>

FlightSimulator::FlightSimulator(const std::string& id, double start_lat, double start_lon, double dest_lat, double dest_lon)
    : target_lat(dest_lat), target_lon(dest_lon) {
    state.aircraft_id = id;
    state.tick = 0;
    state.latitude = start_lat;
    state.longitude = start_lon;
    state.altitude_m = 120.0;
    state.airspeed_mps = 22.5;
    state.battery_pct = 100.0;
    state.status = "EN_ROUTE";
}

void FlightSimulator::step(double dt_seconds) {
    if (state.status == "ARRIVED" || state.status == "LOW_BATTERY_RTL") {
        return;
    }

    state.tick++;

    double dlat = target_lat - state.latitude;
    double dlon = target_lon - state.longitude;
    double dist = std::sqrt(dlat * dlat + dlon * dlon);

    if (dist < 0.0005) {
        state.latitude = target_lat;
        state.longitude = target_lon;
        state.airspeed_mps = 0.0;
        state.status = "ARRIVED";
        return;
    }

    double step_size = 0.0008 * dt_seconds;
    state.latitude += (dlat / dist) * step_size;
    state.longitude += (dlon / dist) * step_size;
    state.altitude_m += std::sin(state.tick * 0.3) * 0.4;
    state.battery_pct -= 0.45 * dt_seconds;

    if (state.battery_pct <= 20.0) {
        state.battery_pct = 20.0;
        state.status = "LOW_BATTERY_RTL";
    }
}

std::string FlightSimulator::toJson() const {
    std::ostringstream oss;
    oss << std::fixed << std::setprecision(6)
        << "{\"aircraft_id\":\"" << state.aircraft_id << "\","
        << "\"tick\":" << state.tick << ","
        << "\"latitude\":" << state.latitude << ","
        << "\"longitude\":" << state.longitude << ","
        << "\"altitude_m\":" << std::setprecision(2) << state.altitude_m << ","
        << "\"airspeed_mps\":" << state.airspeed_mps << ","
        << "\"battery_pct\":" << state.battery_pct << ","
        << "\"status\":\"" << state.status << "\"}";
    return oss.str();
}

bool FlightSimulator::isMissionComplete() const {
    return state.status == "ARRIVED" || state.status == "LOW_BATTERY_RTL";
}

int main(int argc, char* argv[]) {
    std::string id = (argc > 1) ? argv[1] : "VBAT-01";
    double start_lat = (argc > 2) ? std::stod(argv[2]) : 32.7767;
    double start_lon = (argc > 3) ? std::stod(argv[3]) : -96.7970;
    double dest_lat  = (argc > 4) ? std::stod(argv[4]) : 32.7850;
    double dest_lon  = (argc > 5) ? std::stod(argv[5]) : -96.7850;

    FlightSimulator sim(id, start_lat, start_lon, dest_lat, dest_lon);
    std::cout << sim.toJson() << std::endl;

    while (!sim.isMissionComplete() && sim.toJson().find("\"tick\":200") == std::string::npos) {
        sim.step(1.0);
        std::cout << sim.toJson() << std::endl;
    }

    return 0;
}
