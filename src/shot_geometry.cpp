#include "psyz0r/shot_geometry.hpp"
#include <algorithm>
#include <cmath>

namespace psyz0r {
namespace {
bool finite(const PredictionPoint& p) {
    return std::all_of(p.begin(),p.end(),[](double x){return std::isfinite(x);});
}
}
ShotPathStatus check_shot_path(const ShotPathRequest& r,const ShotGeometry& g) {
    if (!finite(r.muzzle) || !finite(r.aim_point) || !std::isfinite(r.now) || r.now<0 ||
        !std::isfinite(r.geometry_max_age) || r.geometry_max_age<0 ||
        !std::isfinite(r.projectile_radius) || r.projectile_radius<0 ||
        !std::isfinite(r.minimum_impact_distance) || r.minimum_impact_distance<0)
        return ShotPathStatus::InvalidInput;
    if (!g.coverage_verified) return ShotPathStatus::UnknownGeometry;
    if (!std::isfinite(g.sampled_at) || g.sampled_at<0 || g.sampled_at>r.now)
        return ShotPathStatus::InvalidInput;
    if (r.now-g.sampled_at>r.geometry_max_age) return ShotPathStatus::StaleGeometry;
    PredictionPoint delta{};
    for(int axis=0;axis<3;++axis) delta[axis]=r.aim_point[axis]-r.muzzle[axis];
    const double distance=std::hypot(delta[0],delta[1],delta[2]);
    if (!finite(delta) || !std::isfinite(distance)) return ShotPathStatus::InvalidInput;
    if (distance<=r.minimum_impact_distance) return ShotPathStatus::TooClose;
    // Validate all boxes first: a malformed scene is not a valid collision query.
    for(const auto& b:g.solids) {
        if (!finite(b.minimum) || !finite(b.maximum)) return ShotPathStatus::InvalidInput;
        for(int axis=0;axis<3;++axis)
            if (b.minimum[axis]>b.maximum[axis] ||
                !std::isfinite(b.minimum[axis]-r.projectile_radius) ||
                !std::isfinite(b.maximum[axis]+r.projectile_radius))
                return ShotPathStatus::InvalidInput;
    }
    for(const auto& b:g.solids) {
        double enter=0,leave=1;
        bool intersects=true;
        for(int axis=0;axis<3;++axis) {
            const double lo=b.minimum[axis]-r.projectile_radius;
            const double hi=b.maximum[axis]+r.projectile_radius;
            if (delta[axis]==0) {
                if(r.muzzle[axis]<lo || r.muzzle[axis]>hi) { intersects=false;break; }
            } else {
                double a=(lo-r.muzzle[axis])/delta[axis];
                double z=(hi-r.muzzle[axis])/delta[axis];
                if(a>z) std::swap(a,z);
                enter=std::max(enter,a);leave=std::min(leave,z);
                if(enter>leave) { intersects=false;break; }
            }
        }
        if(intersects) return ShotPathStatus::Blocked;
    }
    return ShotPathStatus::Clear;
}
}
