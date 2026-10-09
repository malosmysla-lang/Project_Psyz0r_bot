#include "psyz0r/behavior.hpp"
#include <fstream>
#include <iostream>
using namespace psyz0r;
int main(int argc,char** argv) {
    if(argc!=2){std::cerr<<"Usage: reaction_sandbox output.jsonl\n";return 1;}
    std::ofstream out(argv[1]);if(!out)return 1;
    Behavior bot;
    Observation o;o.opponent_id="123";o.available_weapons={Weapon::Rocket,Weapon::Gauntlet};
    o.enemy_visible=true;o.enemy_distance=48;o.safe_close_contact=true;
    o.enemy_hp_estimate_valid=true;o.enemy_hp_estimate=40;
    auto emit=[&](Event e){
        e.opponent_id="123";e.source="synthetic_test";e.verified=true;bot.observe(e);o.time=e.time;
        auto d=bot.decide(o);auto traces=bot.drain_reaction_trace();
        out<<"{\"time\":"<<o.time<<",\"mood\":\"normal\",\"reason\":\""<<d.reason
           <<"\",\"reaction_reason\":\""<<d.reaction_reason<<"\",\"weapon\":"<<static_cast<int>(d.weapon)
           <<",\"game_command_sent\":false,\"interaction_events\":[";
        for(std::size_t i=0;i<traces.size();++i){auto& t=traces[i];if(i)out<<',';
            out<<"{\"event_id\":"<<t.event_id<<",\"opponent_id\":\"123\",\"source\":\"synthetic_test\",\"reason\":\""
               <<t.reason<<"\",\"gauntlet_damage\":"<<t.gauntlet_damage<<",\"corpse_episodes\":"<<t.corpse_episodes<<'}';}
        out<<"]}\n";
    };
    emit({1,1,EventKind::GauntletDamage,25});
    emit({2,32,EventKind::GauntletDamage,25});
    Event e{3,33,EventKind::OpponentCorpseShot};e.corpse_id="own1";emit(e);
    e.id=4;e.time=34;e.corpse_id="own2";emit(e);
    e.id=5;e.time=35;e.corpse_id="own3";emit(e);
    return out?0:1;
}
