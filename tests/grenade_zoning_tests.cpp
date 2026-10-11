#include "psyz0r/grenade_zoning.hpp"
#include <stdexcept>
#include <limits>
using namespace psyz0r;
void check(bool v){if(!v)throw std::runtime_error("grenade zoning contract failed");}
int main(){
    GrenadeZoningInput x;
    x.map="bloodrun";x.zone=GrenadeZone::MegaFromGrenadePlatform;
    x.enemy_position_confirmed=true;x.observation_age=.1;
    x.fastest_approach_verified=true;x.enemy_fastest_approach_seconds=4;
    x.switch_and_escape_seconds=1;x.demonstrated_launch_position=true;
    x.trajectory_verified=x.safe_from_own_grenade=x.useful_to_delay_item_or_block_exit=true;
    x.grenade_launcher_owned=true;x.ammo=2;check(grenade_zoning(x).allowed);
    x.zone=GrenadeZone::UpperTeleportToRed;check(grenade_zoning(x).allowed);
    x.enemy_fastest_approach_seconds=1;check(!grenade_zoning(x).allowed);
    x.enemy_fastest_approach_seconds=4;x.fastest_approach_verified=false;
    check(!grenade_zoning(x).allowed);x.fastest_approach_verified=true;
    x.switch_and_escape_seconds=3.25;check(!grenade_zoning(x).allowed);
    x.switch_and_escape_seconds=1;x.observation_age=.501;check(!grenade_zoning(x).allowed);
    x.observation_age=.1;x.enemy_position_confirmed=false;check(!grenade_zoning(x).allowed);
    x.enemy_position_confirmed=true;x.trajectory_verified=false;check(!grenade_zoning(x).allowed);
    x.trajectory_verified=true;x.ammo=0;check(!grenade_zoning(x).allowed);
    x.ammo=2;x.map="bloodrunintel";check(!grenade_zoning(x).allowed);
    x.map="bloodrun";x.enemy_fastest_approach_seconds=std::numeric_limits<double>::quiet_NaN();
    check(!grenade_zoning(x).allowed);
}
