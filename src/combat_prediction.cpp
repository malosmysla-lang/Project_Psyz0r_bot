#include "psyz0r/combat_prediction.hpp"
#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace psyz0r {
namespace {
bool finite(const PredictionPoint& p) {
    return std::all_of(p.begin(), p.end(), [](double v) { return std::isfinite(v); });
}
PredictionPoint add(const PredictionPoint& p, const PredictionPoint& v, double t) {
    return {p[0]+v[0]*t, p[1]+v[1]*t, p[2]+v[2]*t};
}
PredictionPoint sub(const PredictionPoint& a, const PredictionPoint& b) {
    return {a[0]-b[0], a[1]-b[1], a[2]-b[2]};
}
double dot(const PredictionPoint& a, const PredictionPoint& b) {
    return a[0]*b[0]+a[1]*b[1]+a[2]*b[2];
}
std::optional<PredictionPoint> angles(const PredictionPoint& from, const PredictionPoint& to) {
    const auto d = sub(to, from);
    if (!finite(d) || dot(d,d) < 1e-12) return std::nullopt;
    constexpr double degrees = 180.0 / 3.14159265358979323846;
    return PredictionPoint{-std::atan2(d[2], std::hypot(d[0],d[1]))*degrees,
                           std::atan2(d[1],d[0])*degrees, 0};
}
}
CombatPredictor::CombatPredictor(PredictionSettings s) : settings_(s) {
    if (!std::isfinite(s.max_sample_gap) || s.max_sample_gap <= 0 ||
        !std::isfinite(s.memory_seconds) || s.memory_seconds <= 0 ||
        !std::isfinite(s.max_flight_seconds) || s.max_flight_seconds <= 0 ||
        !std::isfinite(s.max_observed_speed) || s.max_observed_speed <= 0)
        throw std::invalid_argument("Invalid prediction settings");
}
void CombatPredictor::reset() { last_.reset(); velocity_={}; velocity_known_=false; motion_confidence_=1; }
bool CombatPredictor::observe(const VisibleTargetSample& s) {
    if (!s.visible_with_los || s.source.empty() || !finite(s.position) ||
        !std::isfinite(s.time) || s.time < 0 || (last_ && s.time <= last_->time)) return false;
    const auto old_velocity=velocity_;
    const bool had_velocity=velocity_known_;
    motion_confidence_=1;
    velocity_known_ = false;
    velocity_ = {};
    if (last_ && s.time-last_->time <= settings_.max_sample_gap) {
        const double dt=s.time-last_->time;
        const auto delta=sub(s.position,last_->position);
        for (int i=0;i<3;++i) velocity_[i]=delta[i]/dt;
        velocity_known_=finite(velocity_) &&
            std::sqrt(dot(velocity_,velocity_)) <= settings_.max_observed_speed;
        if (velocity_known_ && had_velocity) {
            const auto change=sub(velocity_,old_velocity);
            const double scale=std::max({1.0,std::sqrt(dot(velocity_,velocity_)),
                                        std::sqrt(dot(old_velocity,old_velocity))});
            motion_confidence_=1/(1+std::sqrt(dot(change,change))/scale);
        }
        if (!velocity_known_) velocity_={}; // teleport/discontinuity: reacquire
    }
    last_=s;
    return true;
}
std::optional<TargetEstimate> CombatPredictor::estimate(double now) const {
    if (!last_ || !velocity_known_ || !std::isfinite(now)) return std::nullopt;
    const double age=now-last_->time;
    if (age < 0 || age >= settings_.memory_seconds) return std::nullopt;
    auto position=add(last_->position,velocity_,age);
    if (!finite(position)) return std::nullopt;
    return TargetEstimate{position,velocity_,age,motion_confidence_*(1-age/settings_.memory_seconds)};
}
std::optional<AimPrediction> CombatPredictor::projectile_aim(
    const PredictionPoint& muzzle,double now,const ProjectileProfile& p,double delay) const {
    if (!finite(muzzle) || !p.verified_for_current_rules || !std::isfinite(p.speed) ||
        p.speed <= 0 || !std::isfinite(delay) || delay < 0) return std::nullopt;
    const auto e=estimate(now);
    if (!e || e->age+delay >= settings_.memory_seconds) return std::nullopt;
    const auto launch_target=add(e->position,e->velocity,delay);
    const auto r=sub(launch_target,muzzle);
    const double a=dot(e->velocity,e->velocity)-p.speed*p.speed;
    const double b=2*dot(r,e->velocity), c=dot(r,r);
    if (!std::isfinite(a) || !std::isfinite(b) || !std::isfinite(c) || c < 1e-12)
        return std::nullopt;
    double t=-1;
    if (std::abs(a) < 1e-9*std::max(1.0,p.speed*p.speed)) {
        if (std::abs(b) > 1e-12) t=-c/b;
    } else {
        const double disc=b*b-4*a*c;
        if (!std::isfinite(disc) || disc < 0) return std::nullopt;
        // Stable quadratic roots, including a target moving toward the muzzle.
        const double q=-0.5*(b+std::copysign(std::sqrt(disc),b));
        const double t1=q/a, t2=q!=0?c/q:-1;
        if (t1>0) t=t1;
        if (t2>0 && (t<0 || t2<t)) t=t2;
    }
    if (!std::isfinite(t) || t<=0 || t>=settings_.max_flight_seconds) return std::nullopt;
    const auto point=add(launch_target,e->velocity,t);
    const auto view=angles(muzzle,point);
    if (!view) return std::nullopt;
    const double confidence=motion_confidence_*(1-(e->age+delay)/settings_.memory_seconds)*
                            (1-t/settings_.max_flight_seconds);
    return AimPrediction{point,*view,t,confidence,true};
}
std::optional<AimPrediction> CombatPredictor::hitscan_aim(
    const PredictionPoint& eye,double now,bool visible) const {
    // No extrapolated rail tracking through walls, and no perfect aim implied.
    if (!visible || !finite(eye) || !last_ || !std::isfinite(now) ||
        now!=last_->time) return std::nullopt;
    const auto view=angles(eye,last_->position);
    if (!view) return std::nullopt;
    return AimPrediction{last_->position,*view,0,1,false};
}
}
