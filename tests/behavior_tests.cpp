#include "psyz0r/behavior.hpp"
#include <iostream>
using namespace psyz0r;
int main() {
    int failures = 0;
    auto check = [&](bool ok, const char* label) {
        if (!ok) { std::cerr << label << '\n'; ++failures; }
    };
    Behavior bot(Style::Aggressive);
    Observation o;
    o.time=30;
    o.damage_dealt = 90; o.favorable_fight_estimate = true;
    check(bot.decide(o).intent != Intent::Push, "no unseen-target push");
    o.enemy_visible = true;
    check(bot.decide(o).intent == Intent::Push, "aggressive push");
    o.favorable_fight_estimate = false;
    check(bot.decide(o).intent != Intent::Push, "damage alone is insufficient");
    bot.set_style(Style::Thoughtful); o.damage_received = 80;
    check(bot.decide(o).intent == Intent::Recover, "thoughtful retreat");
    bot.set_style(Style::Passive); o.hit_by_rail = true;
    check(bot.decide(o).intent == Intent::Recover, "passive rail retreat");
    bot.trigger_surrender_tilt(); o.health = 100;
    check(bot.decide(o).intent == Intent::RecklessPush, "tilt persists at respawn");
    o.alive = false;
    check(bot.decide(o).intent == Intent::Hold, "dead bot cannot rush");
    bot.reset_match(); o.alive = true; o.health = 20;
    check(bot.decide(o).intent == Intent::Recover, "match reset removes tilt");
    Behavior tuned(Style::Aggressive, BehaviorSettings{95, 100, 10});
    o.health = 100; o.damage_dealt = 90; o.favorable_fight_estimate = true;
    check(tuned.decide(o).intent == Intent::Hold, "configured push threshold");
    o.damage_dealt = 95;
    check(tuned.decide(o).intent == Intent::Push, "configured threshold boundary");
    return failures == 0 ? 0 : 1;
}
