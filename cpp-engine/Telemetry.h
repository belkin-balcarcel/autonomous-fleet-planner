#ifndef TELEMETRY_H
#define TELEMETRY_H

#include <string>

struct TelemetryPacket {
    std::string aircraft_id;
    int tick;
    double latitude;
    double longitude;
    double altitude_m;
    double airspeed_mps;
    double battery_pct;
    std::string status;
};

class FlightSimulator {
private:
    TelemetryPacket state;
    double target_lat;
    double target_lon;

public:
    FlightSimulator(const std::string& id, double start_lat, double start_lon, double dest_lat, double dest_lon);
    void step(double dt_seconds);
    std::string toJson() const;
    bool isMissionComplete() const;
};

#endif
