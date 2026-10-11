#pragma once
#include <cmath>
#include <string>

namespace psyz0r {
enum class GrenadeZone { None, MegaFromGrenadePlatform, UpperTeleportToRed };
struct GrenadeZoningInput {
    std::string map;
    GrenadeZone zone = GrenadeZone::None;
    bool enemy_position_confirmed = false;
    double observation_age = -1;
    // True only after considering every feasible shortcut, including TP/RJ.
    bool fastest_approach_verified = false;
    double enemy_fastest_approach_seconds = -1;
    double switch_and_escape_seconds = -1;
    bool demonstrated_launch_position = false;
    bool trajectory_verified = false;
    bool safe_from_own_grenade = false;
    bool useful_to_delay_item_or_block_exit = false;
    bool grenade_launcher_owned = false;
    int ammo = 0;
};
struct GrenadeZoningDecision { bool allowed; const char* reason; };
inline GrenadeZoningDecision grenade_zoning(const GrenadeZoningInput& x) {
    if (x.map != "bloodrun" || x.zone == GrenadeZone::None)
        return {false,"unsupported_map_or_zone"};
    if (!x.enemy_position_confirmed || !std::isfinite(x.observation_age) ||
        x.observation_age < 0 || x.observation_age > .5)
        return {false,"enemy_position_unconfirmed_or_stale"};
    if (!x.fastest_approach_verified || !std::isfinite(x.enemy_fastest_approach_seconds) ||
        !std::isfinite(x.switch_and_escape_seconds) || x.enemy_fastest_approach_seconds < 0 ||
        x.switch_and_escape_seconds < 0)
        return {false,"fast_closure_not_excluded"};
    // Conservative initial margins; tune only from verified route/weapon timing.
    if (x.enemy_fastest_approach_seconds <= 2.0 ||
        x.enemy_fastest_approach_seconds <= x.switch_and_escape_seconds + .75)
        return {false,"opponent_can_close_quickly"};
    if (!x.grenade_launcher_owned || x.ammo <= 0)
        return {false,"weapon_or_ammo_missing"};
    if (!x.demonstrated_launch_position || !x.trajectory_verified || !x.safe_from_own_grenade)
        return {false,"launch_not_verified_safe"};
    if (!x.useful_to_delay_item_or_block_exit)
        return {false,"no_zoning_purpose"};
    return {true,"zone_one_grenade_then_recheck"};
}
} // namespace psyz0r
