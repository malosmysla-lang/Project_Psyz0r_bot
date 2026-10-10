#include "psyz0r/combat_prediction.hpp"
#include <cmath>
#include <iostream>
#include <limits>
using namespace psyz0r;
int main() {
    int failures=0;
    auto check=[&](bool ok,const char* label){if(!ok){++failures;std::cerr<<label<<'\n';}};
    auto near=[](double a,double b){return std::abs(a-b)<1e-6;};
    CombatPredictor p;
    ProjectileProfile rocket{1000,true}; // synthetic, not retail QL configuration
    check(!p.observe({{100,0,0},0,false,"hidden"}),"reject hidden sample");
    check(!p.observe({{100,0,0},0,true,""}),"require provenance");
    p.observe({{100,0,0},0,true,"synthetic"});
    check(!p.projectile_aim({0,0,0},0,rocket),"one sample cannot establish velocity");
    p.observe({{100,0,0},0.1,true,"synthetic"});
    auto f=p.projectile_aim({0,0,0},0.1,rocket);
    check(f&&near(f->flight_seconds,0.1)&&near(f->point[0],100),"stationary interception");
    check(!p.projectile_aim({0,0,0},0.1,{1000,false}),"reject unverified projectile profile");
    check(!p.estimate(0.6),"memory expires");
    check(!p.estimate(0.09),"reject time reversal");
    check(!p.hitscan_aim({0,0,0},0.1,false),"rail requires current LOS");
    check(!p.hitscan_aim({0,0,0},0.2,true),"rail cannot use stale point");
    check(p.hitscan_aim({0,0,0},0.1,true).has_value(),"fresh rail proposal");
    p.reset();
    p.observe({{100,-10,0},0,true,"synthetic"});
    p.observe({{100,0,0},0.1,true,"synthetic"});
    f=p.projectile_aim({0,0,0},0.1,rocket);
    check(f&&f->point[1]>0&&f->view_angles[1]>0,"lateral lead and yaw");
    if(f) check(near(std::hypot(f->point[0],f->point[1]),1000*f->flight_seconds),
                "projectile and target arrive at the same point/time");
    auto delayed=p.projectile_aim({0,0,0},0.1,rocket,0.1);
    check(f&&delayed&&delayed->point[1]>f->point[1],"launch delay advances target");
    auto aged=p.projectile_aim({0,0,0},0.2,rocket);
    check(f&&aged&&aged->confidence<f->confidence,"age lowers confidence");
    check(!p.observe({{999,999,999},0.15,false,"hidden"}),"hidden update ignored");
    check(p.estimate(0.2)&&near(p.estimate(0.2)->position[0],100),"hidden sample cannot alter forecast");
    p.observe({{100,-10,0},0.2,true,"synthetic"});
    check(p.estimate(0.2)&&p.estimate(0.2)->velocity[1]<0,"visible reversal updates forecast");
    check(p.estimate(0.2)&&p.estimate(0.2)->confidence<0.5,"reversal reduces motion confidence");
    p.observe({{5000,0,0},0.3,true,"synthetic"});
    check(!p.estimate(0.3),"teleport invalidates velocity");
    p.observe({{5000,0,0},1,true,"synthetic"});
    check(!p.estimate(1),"large observation gap requires reacquisition");
    p.reset();
    p.observe({{100,0,0},0,true,"synthetic"});
    p.observe({{200,0,0},0.1,true,"synthetic"});
    check(!p.projectile_aim({0,0,0},0.1,rocket),"equal speed escaping target unreachable");
    p.reset();
    p.observe({{300,0,0},0,true,"synthetic"});
    p.observe({{200,0,0},0.1,true,"synthetic"});
    f=p.projectile_aim({0,0,0},0.1,rocket);
    check(f&&near(f->flight_seconds,0.1),"equal speed approaching target linear solution");
    check(!p.observe({{0,0,0},std::numeric_limits<double>::quiet_NaN(),true,"bad"}),"reject NaN");
    check(!p.projectile_aim({0,0,0},0.1,rocket,-1),"reject negative delay");
    p.reset();check(!p.estimate(0.1),"reset clears opponent memory");
    return failures?1:0;
}
