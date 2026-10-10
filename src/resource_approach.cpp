#include "psyz0r/resource_approach.hpp"
#include <cmath>
#include <stdexcept>
#include <utility>
namespace psyz0r {
void ResourceApproach::set_goal(ResourceGoal goal) {
    if(goal.map.empty()||goal.id.empty()||(goal.physics!="classic"&&goal.physics!="pql")||goal.item_protocol_id<0)
        throw std::invalid_argument("Resource goal lacks identity/physics");
    for(auto v:goal.approach_position) if(!std::isfinite(v)) throw std::invalid_argument("Invalid resource position");
    goal_=std::move(goal);phase_=ResourcePhase::Approach;start_=last_=arrived_=-1;
}
ResourceProgress ResourceApproach::update(const OwnState& own,const std::string& map,const std::string& physics,
                                        const std::optional<PickupEvidence>& pickup) {
    if(phase_==ResourcePhase::Replan) return {phase_,"resource_replan_required"};
    if(!own.state_verified||!own.alive||!goal_.position_reviewed||map!=goal_.map||physics!=goal_.physics||
       own.server_time_ms<0||(last_>=0&&(own.server_time_ms<last_||own.server_time_ms-last_>100))) {
        phase_=ResourcePhase::Replan;return {phase_,"resource_invalid_context"};
    }
    if(start_<0) start_=own.server_time_ms;
    last_=own.server_time_ms;
    if(phase_==ResourcePhase::Complete) return {phase_,"resource_pickup_confirmed"};
    if(pickup&&pickup->own_pickup_verified&&pickup->goal_id==goal_.id&&
       pickup->item_protocol_id==goal_.item_protocol_id&&pickup->server_time_ms>=start_&&
       pickup->server_time_ms<=own.server_time_ms&&own.server_time_ms-pickup->server_time_ms<=100) {
        phase_=ResourcePhase::Complete;return {phase_,"resource_pickup_confirmed"};
    }
    for(auto v:own.position) if(!std::isfinite(v)) {phase_=ResourcePhase::Replan;return {phase_,"resource_invalid_position"};}
    const auto& a=goal_.approach_position;
    bool near=std::hypot(own.position[0]-a[0],own.position[1]-a[1])<=32 && std::abs(own.position[2]-a[2])<=24;
    if(near) {
        if(arrived_<0) arrived_=own.server_time_ms;
        if(own.server_time_ms-arrived_>=1500) {phase_=ResourcePhase::Replan;return {phase_,"resource_not_picked_up"};}
        phase_=ResourcePhase::AwaitPickup;return {phase_,"resource_near_but_unconfirmed"};
    }
    arrived_=-1;phase_=ResourcePhase::Approach;return {phase_,"resource_follow_existing_movement_route"};
}
}
