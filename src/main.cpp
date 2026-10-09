#include "psyz0r/behavior.hpp"
#include <fstream>
#include <iostream>
#include <stdexcept>
using namespace psyz0r;
const char* mood_name(Mood mood) {
    switch(mood) {case Mood::Normal:return "normal";case Mood::Relaxed:return "relaxed";
    case Mood::LeadLossTilt:return "lead_loss_tilt";case Mood::SurrenderTilt:return "surrender_tilt";case Mood::PressureEscape:return "pressure_escape";}
    return "unknown";
}
int main(int argc,char** argv) {
    try {
        auto settings=argc>2?BehaviorSettings::load(argv[2]):BehaviorSettings{};
        Behavior bot(Style::Aggressive,settings);
        Observation seen; seen.time=30; seen.enemy_visible=true; seen.damage_dealt=85;
        seen.favorable_fight_estimate=true; seen.available_weapons={Weapon::Machinegun,Weapon::Rocket};
        auto decision=bot.decide(seen);
        std::ofstream log;
        if(argc>1) { log.open(argv[1],std::ios::app); if(!log) throw std::runtime_error("Cannot open journal"); }
        auto record=[&](int id,const Observation& o,const Decision& d,bool forced) {
            if(log.is_open()) {
                log<<"{\"mode\":\"offline_scenario\",\"bot\":\"Psyz0r_bot\",\"scenario_id\":"<<id
                   <<",\"time\":"<<o.time<<",\"mood\":\""<<mood_name(d.mood)<<"\",\"reason\":\""<<d.reason
                   <<"\",\"intent\":"<<static_cast<int>(d.intent)<<",\"weapon\":"<<static_cast<int>(d.weapon)
                   <<",\"collect_resources\":"<<(d.collect_resources?"true":"false")
                   <<",\"forced_for_test\":"<<(forced?"true":"false")<<",\"game_command_sent\":false}\n";
                if(!log) throw std::runtime_error("Cannot write journal");
            }
            std::cout<<id<<": "<<d.reason<<" (offline)\n";
        };
        record(1,seen,decision,false);
        bot.reset_match(); bot.trigger_surrender_tilt();
        seen.time=1; seen.health=100; seen.damage_dealt=0; seen.bot_score=0; seen.opponent_score=6;
        record(2,seen,bot.decide(seen),true);
        seen.time=2; seen.bot_score=2; // accidental frags do not cancel psychological surrender
        record(3,seen,bot.decide(seen),true);
    } catch(const std::exception& error) { std::cerr<<error.what()<<'\n'; return 1; }
}
