#include "psyz0r/movement.hpp"
#include <iostream>
#include <cmath>
using namespace psyz0r;
int main(int argc,char** argv) {
    int failed=0;
    auto check=[&](bool ok,const char* name){if(!ok){++failed;std::cerr<<name<<'\n';}};
    MovementRoute route{"bloodrun","classic","synthetic_test",{{{0,0,0}},{{200,0,0}}},true};
    MovementInput in;in.map="bloodrun";in.physics="classic";in.corridor_clear=true;
    in.own.state_verified=in.own.view_angles_valid=in.own.alive=in.own.on_ground=true;
    in.own.health=100;in.own.weapon=5;
    MovementController mover;mover.set_route(route);
    check(mover.update(in).command.valid_for_ms==0,"first sample waits");
    in.own.server_time_ms=50;
    auto out=mover.update(in);
    check(out.command.forward==127&&out.command.right==0&&!out.command.attack&&!out.game_command_sent,"run proposal only");
    check(out.command.valid_for_ms==50,"finite command lifetime");
    Behavior bot;Observation seen;seen.time=20;
    in.behavior=bot.decide(seen);in.behavior.quiet_walk_requested=true;
    in.own.server_time_ms=100;out=mover.update(in);
    check(out.mode==MovementMode::Quiet&&out.command.quiet_walk&&!out.command.jump,"behavior quiet route");
    in.behavior.fast_escape_requested=true;in.own.server_time_ms=150;out=mover.update(in);
    check(out.mode==MovementMode::Run&&!out.command.quiet_walk,"danger overrides quiet");
    in.own.position={200,0,0};in.own.server_time_ms=200;
    check(mover.update(in).route_complete,"completion uses observed position");
    mover.set_route(route);in.own={};in.own.alive=true;
    check(mover.update(in).reason=="movement_unverified_own_state","unavailable view/state blocks");
    in.own.state_verified=in.own.view_angles_valid=in.own.on_ground=true;
    mover.set_route(route);mover.update(in);in.own.server_time_ms=50;in.corridor_clear=false;
    check(mover.update(in).request_replan,"unknown clearance blocks");
    in.corridor_clear=true;in.own.server_time_ms=100;
    check(mover.update(in).reason=="movement_wait_replanned_route","failure remains latched until route reset");
    mover.set_route(route);in.own.server_time_ms=0;mover.update(in);in.own.server_time_ms=50;in.physics="pql";
    check(mover.update(in).request_replan,"physics mismatch");in.physics="classic";
    mover.set_route(route);in.own.server_time_ms=0;mover.update(in);in.own.server_time_ms=500;
    check(mover.update(in).request_replan,"sample gap blocks");
    mover.set_route(route);in.own.server_time_ms=0;mover.update(in);
    for(int i=1;i<=42;++i){in.own.server_time_ms=i*50;out=mover.update(in);}
    check(out.request_replan,"stalled route requests replan");
    mover.set_route(route);in.own.server_time_ms=0;mover.update(in);in.own.server_time_ms=50;
    in.speed_route_requested=true;in.technique=MovementMode::SingleBeat;in.behavior={};
    check(mover.update(in).reason=="movement_unverified_air_physics","no imported Q3 constants");
    in.air={320,1,true};in.own.server_time_ms=100;out=mover.update(in);
    check(out.command.jump,"one synthetic grounded jump request");
    in.own.server_time_ms=150;out=mover.update(in);check(!out.command.jump,"no repeated jump pulse");
    in.own.on_ground=false;in.own.velocity={600,0,200};in.own.server_time_ms=200;
    out=mover.update(in);check(out.mode==MovementMode::SingleBeat&&!out.command.jump,"synthetic air proposal");
    in.behavior.mood=Mood::PressureEscape;in.own.server_time_ms=250;out=mover.update(in);
    check(out.mode==MovementMode::Run&&!out.command.jump,"pressure disables speed technique");
    in.behavior={};in.speed_route_requested=false;in.combat.active=true;in.combat.view_angles={0,90,0};
    in.combat.strafe_direction=1;in.own.server_time_ms=300;
    check(mover.update(in).reason=="movement_invalid_combat_request","no unseen target tracking");
    in.combat.visible_with_wall_los=in.combat.strafe_clear=true;in.own.server_time_ms=350;
    out=mover.update(in);check(out.reason=="movement_observed_combat_strafe"&&!out.command.attack,"combat coordinated but not shooting");
    check(std::abs(out.command.view_angles[1]-in.own.view_angles[1])<=12.001,"yaw rate limit");
    check(MovementController::optimal_air_angle(1000,320,1,.05)>MovementController::optimal_air_angle(600,320,1,.05),"angle depends on speed");
    mover.set_route(route);in.combat={};in.own.on_ground=true;in.own.server_time_ms=0;in.speed_route_requested=true;
    mover.update(in);
    for(int i=1;i<=9;++i){in.own.server_time_ms=i*50;out=mover.update(in);}
    check(out.request_replan&&!out.command.jump,"unobserved jump does not silently continue");
    MovementSettings quick;quick.max_yaw_rate=3600;
    MovementController half_mover(quick);half_mover.set_route(route);
    MovementInput half;half.map="bloodrun";half.physics="classic";half.corridor_clear=true;
    half.own.alive=half.own.state_verified=half.own.view_angles_valid=half.own.on_ground=true;
    half.speed_route_requested=true;half.technique=MovementMode::HalfBeat;half.air={320,1,true};
    half_mover.update(half);half.own.server_time_ms=50;half_mover.update(half);
    half.own.on_ground=false;half.own.velocity={600,0,200};half.own.server_time_ms=100;
    auto phase_one=half_mover.update(half);
    check(phase_one.command.forward==127&&phase_one.command.right==127,"half beat diagonal phase uses full axes");
    half.own.on_ground=true;half.own.velocity[2]=0;half.own.server_time_ms=150;half_mover.update(half);
    half.own.on_ground=false;half.own.velocity[2]=200;half.own.server_time_ms=200;
    auto phase_two=half_mover.update(half);
    check(phase_two.command.forward==0&&phase_two.command.right==127,"half beat side-only phase after observed landing");
    if(argc>1) {
        auto loaded=MovementSettings::load(argv[1]);
        check(loaded.command_duration_ms==50&&loaded.jump_ack_timeout_ms==300,"load actual movement configuration");
    }
    return failed?1:0;
}
