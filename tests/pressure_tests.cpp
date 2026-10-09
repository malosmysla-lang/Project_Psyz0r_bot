#include "psyz0r/behavior.hpp"
#include <iostream>
using namespace psyz0r;
int main() {
    int failures=0;
    auto check=[&](bool ok,const char* name){if(!ok){std::cerr<<name<<'\n';++failures;}};
    BehaviorSettings s;s.pressure_probability=1;s.surrender_probability=1;
    Behavior b(Style::Thoughtful,s);
    auto event=[&](unsigned id,double time,EventKind kind,Weapon weapon=Weapon::None,const char* cover=""){
        Event e{id,time,kind};e.verified=true;e.source="synthetic_test";e.opponent_id="human";e.weapon=weapon;e.location_id=cover;b.observe(e);
    };
    Observation o;o.opponent_id="human";o.opponent_score=5;o.time=1;
    check(b.decide(o).mood==Mood::Normal,"score alone never triggers escape");
    event(1,2,EventKind::OpponentKilledBot);event(2,3,EventKind::OpponentKilledBot);
    event(3,4,EventKind::OpponentKilledBot);o.time=4;
    // Avoid allowing forfeit before completing pressure evidence in this scenario.
    o.opponent_score=3;
    check(b.decide(o).mood==Mood::Normal,"death streak without repeat attacks/rest interruptions insufficient");
    event(4,5,EventKind::OpponentPush);event(5,6,EventKind::OpponentPush);
    event(6,7,EventKind::RecoveryInterrupted);o.time=7;o.opponent_score=5;
    o.available_weapons={Weapon::Rocket};
    o.item_candidates={{"dangerous-mega",ItemKind::Mega,0,1,.9,false},
                       {"health",ItemKind::Health,0,4,.1,true},
                       {"yellow",ItemKind::Yellow,0,1,.1,true}};
    auto d=b.decide(o);
    check(d.mood==Mood::PressureEscape&&d.collect_resources,"escape takes precedence over forfeit");
    check(d.target_item=="health"&&d.target_cover.empty(),"safe recovery not fake rail ambush");
    check(d.quiet_walk_requested&&!d.fast_escape_requested,"quiet only without immediate danger");
    o.immediate_danger=true;d=b.decide(o);
    check(d.fast_escape_requested&&!d.quiet_walk_requested&&d.intent==Intent::Escape,"fast escape under fire");
    o.immediate_danger=false;o.available_weapons={Weapon::Rail,Weapon::Rocket};
    o.cover_candidates={{"deadend",ItemKind::Mega,.1,false},{"mega-cover",ItemKind::Mega,.1,true},
                        {"red-cover",ItemKind::Red,.2,true}};
    o.reached_cover_id="mega-cover";o.enemy_visible=false;d=b.decide(o);
    check(d.intent==Intent::CoverRail&&!d.attack_visible_target,"wait with rail but never aim through wall");
    o.enemy_visible=true;d=b.decide(o);
    check(d.attack_visible_target&&d.weapon==Weapon::Rail&&d.intent!=Intent::Push,"single observed rail attempt not push");
    auto pending=b.decide(o);
    check(pending.weapon!=Weapon::Rail,"do not issue repeated rail while awaiting actual shot, other weapons defend");
    event(7,8,EventKind::OwnRailShot,Weapon::Rail,"mega-cover");o.time=8;d=b.decide(o);
    check(d.intent==Intent::Escape&&d.fast_escape_requested&&d.target_cover=="red-cover","confirmed fire triggers withdrawal regardless of hit");
    o.time=11;o.enemy_visible=false;d=b.decide(o);
    check(d.intent==Intent::Escape,"cannot repeat ambush from old cover");
    o.reached_cover_id="red-cover";d=b.decide(o);
    check(d.intent==Intent::CoverRail,"next cover prepared after reposition");
    o.time=20;o.health=100;o.armor=100;
    check(b.decide(o).mood==Mood::PressureEscape,"minimum duration prevents flapping");
    o.time=37;
    check(b.decide(o).mood==Mood::Normal,"calm and own recovery exits mode");
    b.reset_match();check(b.decide(Observation{}).mood==Mood::Normal,"new match clears pressure");
    auto feed=[](Behavior& bot){
        EventKind kinds[]={EventKind::OpponentKilledBot,EventKind::OpponentKilledBot,
                           EventKind::OpponentPush,EventKind::OpponentPush,EventKind::RecoveryInterrupted};
        for(unsigned i=0;i<5;++i){Event e{i+1,1, kinds[i]};e.verified=true;e.source="synthetic_test";e.opponent_id="human";bot.observe(e);}
    };
    Observation base;base.opponent_id="human";base.opponent_score=3;base.time=1;
    Behavior aggressive(Style::Aggressive,s);feed(aggressive);
    check(aggressive.decide(base).mood!=Mood::PressureEscape,"aggressive style gate");
    Behavior old(Style::Thoughtful,s);feed(old);base.time=32;
    check(old.decide(base).mood!=Mood::PressureEscape,"old pressure events expire");
    Behavior waiting(Style::Thoughtful,s);feed(waiting);base.time=1;
    base.available_weapons={Weapon::Rail};base.cover_candidates={{"cover",ItemKind::Mega,.1,true}};
    base.reached_cover_id="cover";
    check(waiting.decide(base).intent==Intent::CoverRail,"safe quiet cover selected");
    base.time=4;
    check(waiting.decide(base).reason=="pressure_escape_cover_wait_expired_relocate","cannot stay indefinitely in same cover");
    waiting.forget_opponent("human");
    check(waiting.decide(base).mood==Mood::Normal,"disconnect cancels escape state");
    return failures?1:0;
}
