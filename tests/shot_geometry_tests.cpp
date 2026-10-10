#include "psyz0r/shot_geometry.hpp"
#include <iostream>
#include <limits>
using namespace psyz0r;
int main() {
    int failures=0;
    auto check=[&](bool ok,const char* name){if(!ok){++failures;std::cerr<<name<<'\n';}};
    ShotPathRequest r{{0,0,0},{100,0,0},1,0.1,0,20};
    ShotGeometry g{{},1,false};
    check(check_shot_path(r,g)==ShotPathStatus::UnknownGeometry,"empty unverified scene is unknown");
    g.coverage_verified=true;
    check(check_shot_path(r,g)==ShotPathStatus::Clear,"verified empty corridor");
    g.sampled_at=0.5;
    check(check_shot_path(r,g)==ShotPathStatus::StaleGeometry,"reject stale geometry");
    g.sampled_at=2;
    check(check_shot_path(r,g)==ShotPathStatus::InvalidInput,"reject future geometry");
    g.sampled_at=1;
    g.solids={{{40,-10,-10},{50,10,10}}};
    check(check_shot_path(r,g)==ShotPathStatus::Blocked,"wall across segment");
    g.solids={{{40,2,-10},{50,4,10}}};
    check(check_shot_path(r,g)==ShotPathStatus::Clear,"parallel clear segment");
    r.projectile_radius=2;
    check(check_shot_path(r,g)==ShotPathStatus::Blocked,"radius grazing wall blocked");
    r.projectile_radius=0;
    g.solids={{{110,-10,-10},{120,10,10}}};
    check(check_shot_path(r,g)==ShotPathStatus::Clear,"obstacle beyond target ignored");
    g.solids={{{-20,-10,-10},{-10,10,10}}};
    check(check_shot_path(r,g)==ShotPathStatus::Clear,"obstacle behind muzzle ignored");
    g.solids={{{-1,-1,-1},{1,1,1}}};
    check(check_shot_path(r,g)==ShotPathStatus::Blocked,"muzzle inside solid");
    g.solids={};r.aim_point={10,0,0};
    check(check_shot_path(r,g)==ShotPathStatus::TooClose,"impact too close");
    r.aim_point={0,0,0};r.minimum_impact_distance=0;
    check(check_shot_path(r,g)==ShotPathStatus::TooClose,"zero length rejected");
    r.aim_point={100,0,0};
    g.solids={{{50,0,0},{40,1,1}}};
    check(check_shot_path(r,g)==ShotPathStatus::InvalidInput,"inverted box rejected");
    g.solids={};r.projectile_radius=std::numeric_limits<double>::quiet_NaN();
    check(check_shot_path(r,g)==ShotPathStatus::InvalidInput,"NaN rejected");
    // Integration: predictor proposal must still pass independent collision query.
    CombatPredictor predictor;
    predictor.observe({{100,0,0},0,true,"synthetic"});
    predictor.observe({{100,0,0},0.1,true,"synthetic"});
    auto aim=predictor.projectile_aim({0,0,0},0.1,{1000,true});
    check(aim.has_value(),"intercept available");
    if(aim) {
        r={{0,0,0},aim->point,0.1,0,0,20};
        g={{{{40,-10,-10},{50,10,10}}},0.1,true};
        check(check_shot_path(r,g)==ShotPathStatus::Blocked,"valid intercept does not bypass wall");
    }
    return failures?1:0;
}
