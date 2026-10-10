#pragma once
#include <array>
#include <optional>
#include <string>

namespace psyz0r {
using PredictionPoint = std::array<double, 3>;
struct PredictionSettings {
    double max_sample_gap = 0.25;
    double memory_seconds = 0.5;
    double max_flight_seconds = 2.0;
    double max_observed_speed = 2000;
};
struct VisibleTargetSample {
    PredictionPoint position{};
    double time = 0;
    bool visible_with_los = false;
    std::string source;
};
struct TargetEstimate {
    PredictionPoint position{}, velocity{};
    double age = 0, confidence = 0;
    // Extrapolation only; this is never a current hidden player coordinate.
};
struct ProjectileProfile {
    double speed = 0;
    bool verified_for_current_rules = false;
    // This solver supports straight, constant-speed projectiles only.
};
struct AimPrediction {
    PredictionPoint point{}, view_angles{}; // pitch, yaw, roll in degrees
    double flight_seconds = 0, confidence = 0;
    bool extrapolated = false;
    // Proposal only. No firing/visibility/clearance permission is implied.
};
class CombatPredictor {
public:
    explicit CombatPredictor(PredictionSettings settings = {});
    bool observe(const VisibleTargetSample& sample);
    void reset(); // required on map/match/opponent changes or respawn
    std::optional<TargetEstimate> estimate(double now) const;
    std::optional<AimPrediction> projectile_aim(
        const PredictionPoint& muzzle, double now,
        const ProjectileProfile& projectile, double launch_delay = 0) const;
    std::optional<AimPrediction> hitscan_aim(
        const PredictionPoint& eye, double now, bool currently_visible_with_los) const;
private:
    PredictionSettings settings_;
    std::optional<VisibleTargetSample> last_;
    PredictionPoint velocity_{};
    bool velocity_known_ = false;
    double motion_confidence_ = 1;
};
}
