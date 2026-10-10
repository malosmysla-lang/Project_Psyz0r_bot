#pragma once
#include "psyz0r/game_interface.hpp"
#include <string>
#include <optional>
namespace psyz0r {
struct ResourceGoal {
    std::string map, physics, id;
    std::array<float,3> approach_position{};
    int item_protocol_id=-1;
    bool position_reviewed=false;
};
struct PickupEvidence {
    std::string goal_id;
    int item_protocol_id=-1;
    std::int64_t server_time_ms=0;
    bool own_pickup_verified=false;
};
enum class ResourcePhase { Approach, AwaitPickup, Complete, Replan };
struct ResourceProgress { ResourcePhase phase; std::string reason; };
// Tracks one chosen resource. Selection remains in Behavior; motion in MovementController.
class ResourceApproach {
public:
    void set_goal(ResourceGoal goal);
    ResourceProgress update(const OwnState&,const std::string& map,const std::string& physics,
                            const std::optional<PickupEvidence>& pickup={});
private:
    ResourceGoal goal_;
    ResourcePhase phase_=ResourcePhase::Replan;
    std::int64_t start_=-1, last_=-1, arrived_=-1;
};
}
