#pragma once
#include <deque>
#include <optional>
#include <string>
#include <vector>
namespace psyz0r {
struct RoutePatternSettings {
    int min_repeats=3, max_pattern_zones=6, max_observations=64;
    double history_seconds=60, forecast_ttl=15, timing_tolerance=0.3;
    double minimum_confidence=0.6, mismatch_decay=0.35;
    double initial_confidence=0.8;
    static RoutePatternSettings load(const std::string& path);
};
struct ZoneObservation {
    std::string zone, source;
    double time=0;
    bool perceptible=false;
};
struct RouteForecast {
    std::string next_zone;
    double expected_time=0, confidence=0, expires_at=0;
    std::vector<std::string> pattern;
    // This is a prediction of a zone, never the current hidden player position.
};
class RoutePredictor {
public:
    explicit RoutePredictor(RoutePatternSettings settings={});
    bool observe(const ZoneObservation& observation);
    std::optional<RouteForecast> forecast(double now) const;
    void reset();
private:
    RoutePatternSettings settings_;
    std::deque<ZoneObservation> history_;
    std::optional<RouteForecast> prediction_;
    double last_time_=-1;
};
}
