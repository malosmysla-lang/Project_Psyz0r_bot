#pragma once
#include "psyz0r/behavior.hpp"
#include "psyz0r/game_interface.hpp"
#include <optional>
#include <string>
#include <vector>

namespace psyz0r {
enum class MovementMode { Hold, Run, Quiet, SingleBeat, HalfBeat };
struct MovementSettings {
    double waypoint_radius=24, vertical_tolerance=24, max_yaw_rate=240;
    double stall_seconds=2, progress_distance=8, discontinuity_distance=256;
    double max_sample_gap_ms=100;
    int command_duration_ms=50;
    int jump_ack_timeout_ms=300;
    static MovementSettings load(const std::string& path);
};
struct MovementRoute {
    std::string map, physics, source;
    std::vector<std::array<float,3>> points;
    // Review of geometry/clearance is required separately from demo extraction.
    bool geometry_verified=false;
};
struct AirAccelerationProfile {
    double wish_speed=0, acceleration=0;
    bool measured_for_current_physics=false;
};
struct CombatMovementRequest {
    bool active=false, visible_with_wall_los=false, immediate_danger=false;
    // Absolute desired view from the separate combat module, no hidden target positions.
    std::array<float,3> view_angles{};
    int strafe_direction=0;
    bool strafe_clear=false;
};
struct MovementInput {
    OwnState own;
    Decision behavior;
    std::string map, physics;
    bool corridor_clear=false, speed_route_requested=false;
    MovementMode technique=MovementMode::Run;
    AirAccelerationProfile air;
    CombatMovementRequest combat;
};
struct MovementOutput {
    GameCommand command;
    MovementMode mode=MovementMode::Hold;
    std::string reason;
    std::size_t waypoint=0;
    bool request_replan=false, route_complete=false;
    // This class produces a proposal; it never calls GameInterface::submit.
    bool game_command_sent=false;
};
class MovementController {
public:
    explicit MovementController(MovementSettings settings={});
    void set_route(MovementRoute route);
    void reset();
    MovementOutput update(const MovementInput& input);
    static double optimal_air_angle(double speed,double wish_speed,double acceleration,double dt);
private:
    MovementSettings settings_;
    MovementRoute route_;
    std::size_t waypoint_=0;
    std::uint64_t command_id_=0;
    std::optional<OwnState> previous_;
    std::array<float,3> progress_position_{};
    std::int64_t progress_time_=0;
    double progress_goal_distance_=0;
    std::int64_t jump_request_time_=0;
    bool replan_required_=false, jump_requested_=false, saw_air_=false;
    int beat_=1;
};
}
