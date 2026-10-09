#include "psyz0r/movement.hpp"
#include <algorithm>
#include <cmath>
#include <fstream>
#include <stdexcept>
#include <unordered_set>
#include <utility>

namespace psyz0r {
namespace {
constexpr double pi=3.14159265358979323846;
double degrees(double r) {return r*180/pi;}
double radians(double d) {return d*pi/180;}
double wrap(double d) {return std::remainder(d,360.0);}
double distance(const std::array<float,3>& a,const std::array<float,3>& b) {
    return std::hypot(std::hypot(a[0]-b[0],a[1]-b[1]),a[2]-b[2]);
}
bool finite(const std::array<float,3>& a) {return std::all_of(a.begin(),a.end(),[](float v){return std::isfinite(v);});}
double turn(double from,double to,double max_delta) {return wrap(from+std::clamp(wrap(to-from),-max_delta,max_delta));}
}
MovementSettings MovementSettings::load(const std::string& path) {
    std::ifstream f(path);if(!f) throw std::runtime_error("Cannot open movement settings");
    MovementSettings s;std::string key;double value;std::unordered_set<std::string> seen;
    while(f>>key) {
        if(!(f>>value)||!std::isfinite(value)||value<=0||!seen.insert(key).second) throw std::invalid_argument("Invalid movement setting");
        if(key=="waypoint_radius") s.waypoint_radius=value;
        else if(key=="vertical_tolerance") s.vertical_tolerance=value;
        else if(key=="max_yaw_rate") s.max_yaw_rate=value;
        else if(key=="stall_seconds") s.stall_seconds=value;
        else if(key=="progress_distance") s.progress_distance=value;
        else if(key=="discontinuity_distance") s.discontinuity_distance=value;
        else if(key=="max_sample_gap_ms") s.max_sample_gap_ms=value;
        else if(key=="command_duration_ms"&&value==std::floor(value)&&value<=100) s.command_duration_ms=static_cast<int>(value);
        else if(key=="jump_ack_timeout_ms"&&value==std::floor(value)&&value<=1000) s.jump_ack_timeout_ms=static_cast<int>(value);
        else throw std::invalid_argument("Unknown or invalid movement setting: "+key);
    }
    return s;
}
MovementController::MovementController(MovementSettings settings):settings_(settings) {
    const double values[]={settings.waypoint_radius,settings.vertical_tolerance,settings.max_yaw_rate,
        settings.stall_seconds,settings.progress_distance,settings.discontinuity_distance,settings.max_sample_gap_ms};
    for(double v:values) if(!std::isfinite(v)||v<=0) throw std::invalid_argument("Invalid movement settings");
    if(settings.command_duration_ms<=0||settings.command_duration_ms>100) throw std::invalid_argument("Command lifetime outside limits");
    if(settings.jump_ack_timeout_ms<settings.command_duration_ms||settings.jump_ack_timeout_ms>1000)
        throw std::invalid_argument("Invalid jump acknowledgement timeout");
}
void MovementController::reset() {
    waypoint_=0;previous_.reset();progress_time_=0;replan_required_=jump_requested_=saw_air_=false;beat_=1;
    progress_goal_distance_=0;jump_request_time_=0;
}
void MovementController::set_route(MovementRoute route) {
    if(route.map.empty()||route.source.empty()||(route.physics!="classic"&&route.physics!="pql")||route.points.empty())
        throw std::invalid_argument("Route lacks map, physics or provenance");
    for(const auto& point:route.points) if(!finite(point)) throw std::invalid_argument("Invalid route point");
    route_=std::move(route);reset();
}
double MovementController::optimal_air_angle(double speed,double wish,double acceleration,double dt) {
    if(!std::isfinite(speed)||!std::isfinite(wish)||!std::isfinite(acceleration)||!std::isfinite(dt)||
        speed<=0||wish<=0||acceleration<=0||dt<=0||dt>.1) throw std::invalid_argument("Invalid measured acceleration parameters");
    // Q3-family projection model; parameters must be measured for the selected QL physics.
    const double step=acceleration*wish*dt;
    return degrees(std::acos(std::clamp((wish-step)/speed,-1.0,1.0)));
}
MovementOutput MovementController::update(const MovementInput& in) {
    MovementOutput out;const auto& s=in.own;
    out.command.id=++command_id_;out.command.server_time_ms=s.server_time_ms;
    if(s.view_angles_valid&&finite(s.view_angles)) out.command.view_angles=s.view_angles;
    out.command.weapon=s.weapon;out.waypoint=waypoint_;
    auto stop=[&](const char* why,bool replan=false) {
        out.command.forward=out.command.right=out.command.valid_for_ms=0;
        out.command.jump=out.command.attack=out.command.quiet_walk=false;out.mode=MovementMode::Hold;
        out.reason=why;out.request_replan=replan;
        if(replan) replan_required_=true;
        previous_=s;return out;
    };
    if(!s.state_verified||!s.view_angles_valid||!finite(s.position)||!finite(s.velocity)||!finite(s.view_angles)||s.server_time_ms<0)
        return stop("movement_unverified_own_state");
    if(!s.alive) {reset();return stop("movement_dead");}
    double dt=0;
    if(previous_) {
        dt=(s.server_time_ms-previous_->server_time_ms)/1000.0;
        if(dt<=0) return stop("movement_nonmonotonic_time",true);
        if(dt*1000>settings_.max_sample_gap_ms||distance(s.position,previous_->position)>settings_.discontinuity_distance)
            return stop("movement_state_discontinuity",true);
    } else {progress_position_=s.position;progress_time_=s.server_time_ms;return stop("movement_wait_second_sample");}
    if(replan_required_) return stop("movement_wait_replanned_route",true);
    if(in.map!=route_.map||in.physics!=route_.physics) return stop("movement_map_or_physics_mismatch",true);
    if(!route_.geometry_verified||!in.corridor_clear) return stop("movement_unknown_clearance",true);
    if(in.combat.active&&(!in.combat.visible_with_wall_los||!finite(in.combat.view_angles)||
                         in.combat.strafe_direction<-1||in.combat.strafe_direction>1||
                         (in.combat.strafe_direction&&!in.combat.strafe_clear)))
        return stop("movement_invalid_combat_request");
    if(in.technique==MovementMode::Hold) return stop("movement_explicit_hold");
    while(waypoint_<route_.points.size() &&
          std::hypot(s.position[0]-route_.points[waypoint_][0],s.position[1]-route_.points[waypoint_][1])<=settings_.waypoint_radius &&
          std::abs(s.position[2]-route_.points[waypoint_][2])<=settings_.vertical_tolerance) {
        ++waypoint_;progress_position_=s.position;progress_time_=s.server_time_ms;progress_goal_distance_=0;
    }
    out.waypoint=waypoint_;
    if(waypoint_>=route_.points.size()) {out.route_complete=true;return stop("movement_route_complete");}
    double goal_distance=distance(s.position,route_.points[waypoint_]);
    if(progress_goal_distance_==0||progress_goal_distance_-goal_distance>=settings_.progress_distance) {
        progress_position_=s.position;progress_time_=s.server_time_ms;progress_goal_distance_=goal_distance;
    } else if(s.server_time_ms-progress_time_>=settings_.stall_seconds*1000) return stop("movement_no_observed_progress",true);
    const auto& target=route_.points[waypoint_];
    const double dx=target[0]-s.position[0],dy=target[1]-s.position[1],length=std::hypot(dx,dy);
    if(length<1) return stop("movement_vertical_segment_needs_maneuver",true);
    double ux=dx/length,uy=dy/length,yaw=degrees(std::atan2(uy,ux));
    out.mode=MovementMode::Run;
    const bool danger=in.behavior.fast_escape_requested||in.combat.immediate_danger;
    const bool quiet=in.behavior.quiet_walk_requested&&!danger;
    const bool recover=in.behavior.intent==Intent::Recover||in.behavior.mood==Mood::PressureEscape;
    const bool air_requested=in.speed_route_requested&&!quiet&&!recover&&!in.combat.active&&in.behavior.jump_scale>=1;
    if(air_requested&&(in.technique==MovementMode::SingleBeat||in.technique==MovementMode::HalfBeat)) {
        if(in.physics!="classic"||!in.air.measured_for_current_physics) return stop("movement_unverified_air_physics");
        if(in.air.wish_speed<=0||in.air.acceleration<=0||!std::isfinite(in.air.wish_speed)||!std::isfinite(in.air.acceleration))
            return stop("movement_invalid_air_profile");
        if(dt>.1) return stop("movement_air_sample_gap",true);
        if(jump_requested_&&s.on_ground&&!saw_air_&&s.server_time_ms-jump_request_time_>settings_.jump_ack_timeout_ms)
            return stop("movement_jump_not_observed",true);
        if(!s.on_ground) saw_air_=true;
        if(s.on_ground&&saw_air_) {beat_=-beat_;saw_air_=false;jump_requested_=false;}
        out.command.jump=s.on_ground&&!jump_requested_;
        if(out.command.jump) {jump_requested_=true;jump_request_time_=s.server_time_ms;}
        const double speed=std::hypot(s.velocity[0],s.velocity[1]);
        if(speed>1&&!s.on_ground) {
            const double v_heading=degrees(std::atan2(s.velocity[1],s.velocity[0]));
            const double wish_heading=v_heading+beat_*optimal_air_angle(speed,in.air.wish_speed,in.air.acceleration,dt);
            const bool half_second=in.technique==MovementMode::HalfBeat&&beat_<0;
            yaw=wish_heading+(half_second?90:beat_*45);
            // World wish vector stays independent of the view rate limiter.
            ux=std::cos(radians(wish_heading));uy=std::sin(radians(wish_heading));
        }
        out.mode=in.technique;
    } else {jump_requested_=saw_air_=false;}
    if(quiet) {out.mode=MovementMode::Quiet;out.command.quiet_walk=true;}
    if(in.combat.active) {
        yaw=in.combat.view_angles[1];
        out.command.view_angles[0]=static_cast<float>(turn(s.view_angles[0],in.combat.view_angles[0],settings_.max_yaw_rate*dt));
        if(in.combat.strafe_direction) {
            // Q3 horizontal right basis: yaw0 => world -Y. Keep the route planner separate.
            ux=in.combat.strafe_direction*std::sin(radians(yaw));
            uy=-in.combat.strafe_direction*std::cos(radians(yaw));
        }
    }
    yaw=turn(s.view_angles[1],yaw,settings_.max_yaw_rate*dt);
    out.command.view_angles[1]=static_cast<float>(yaw);
    const double magnitude=quiet?64:127;
    const double forward=ux*std::cos(radians(yaw))+uy*std::sin(radians(yaw));
    const double right=ux*std::sin(radians(yaw))-uy*std::cos(radians(yaw));
    // Q3 CmdScale depends on max axis, so preserve full input magnitude on diagonals.
    // This mapping still requires a retail QL usercmd verification.
    const double scale=magnitude/std::max(std::abs(forward),std::abs(right));
    out.command.forward=static_cast<int>(std::lround(scale*forward));
    out.command.right=static_cast<int>(std::lround(scale*right));
    out.command.valid_for_ms=settings_.command_duration_ms;
    out.reason=in.combat.active?"movement_observed_combat_strafe":quiet?"movement_quiet_route":
        air_requested?"movement_requested_air_technique":"movement_route_follow";
    previous_=s;return out;
}
}
