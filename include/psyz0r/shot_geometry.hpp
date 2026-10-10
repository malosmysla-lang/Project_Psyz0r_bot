#pragma once
#include "psyz0r/combat_prediction.hpp"
#include <vector>

namespace psyz0r {
struct SolidBox { PredictionPoint minimum{}, maximum{}; };
struct ShotGeometry {
    // Complete conservative collision coverage for this segment, including
    // relevant dynamic blockers. Empty is safe only when verified as clear.
    std::vector<SolidBox> solids;
    double sampled_at = 0;
    bool coverage_verified = false;
};
enum class ShotPathStatus { Clear, InvalidInput, UnknownGeometry, StaleGeometry, TooClose, Blocked };
struct ShotPathRequest {
    PredictionPoint muzzle{}, aim_point{};
    double now = 0, geometry_max_age = 0;
    double projectile_radius = 0, minimum_impact_distance = 0;
};
// Geometric proposal check, never a command to fire. No splash/ricochet model.
ShotPathStatus check_shot_path(const ShotPathRequest&, const ShotGeometry&);
}
