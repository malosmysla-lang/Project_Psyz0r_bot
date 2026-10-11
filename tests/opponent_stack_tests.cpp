#include "psyz0r/behavior.hpp"
#include <iostream>
using namespace psyz0r;
int main(){
 int failures=0;auto check=[&](bool b,const char* s){if(!b){++failures;std::cerr<<s<<'\n';}};
 Observation o;o.time=30;o.opponent_id="human";o.stack_context={"human","match","bloodrun",1};
 o.exact_opponent_stack=ExactOpponentStack{"human","match","bloodrun","server",1,30,200,200,true,true};
 o.health=100;o.armor=0;o.enemy_visible=true;o.damage_dealt=90;o.favorable_fight_estimate=true;
 o.armor_rules_verified=true;o.available_weapons={Weapon::Rocket};
 o.item_candidates={{"yellow",ItemKind::Yellow,0,1},{"mega",ItemKind::Mega,0,1}};
 Behavior weak(Style::Aggressive);auto d=weak.decide(o);
 check(d.exact_stack_used && d.intent==Intent::Recover,"exact disadvantage overrides stale favorable flag");
 check(d.target_item=="yellow","disadvantage selects recovery route goal");
 o.health=200;o.armor=200;o.exact_opponent_stack->health=50;o.exact_opponent_stack->armor=0;
 o.favorable_fight_estimate=false;Behavior strong(Style::Aggressive);d=strong.decide(o);
 check(d.intent==Intent::Push,"exact advantage supports visible damage push");
 o.enemy_visible=false;Behavior blind(Style::Aggressive);
 check(blind.decide(o).intent!=Intent::Push,"exact stack grants no hidden target pursuit");
 o.time=31;Behavior stale(Style::Aggressive);check(!stale.decide(o).exact_stack_used,"expired stack rejected");
 o.time=30;o.stack_context.respawn_generation=2;Behavior respawn;
 check(!respawn.decide(o).exact_stack_used,"previous life rejected");
 o.stack_context.respawn_generation=1;o.stack_context.match_id="next";Behavior match;
 check(!match.decide(o).exact_stack_used,"previous match rejected");
 o.stack_context.match_id="match";o.exact_opponent_stack->verified=false;Behavior unverified;
 check(!unverified.decide(o).exact_stack_used,"unverified server sample rejected");
 o.exact_opponent_stack->verified=true;o.exact_opponent_stack->observed_at=31;Behavior future;
 check(!future.decide(o).exact_stack_used,"future sample rejected");
 o.exact_opponent_stack->observed_at=30;o.armor_rules_verified=false;Behavior unknown_rules;
 check(!unknown_rules.decide(o).exact_stack_used,"unknown armor rules do not imply stack advantage");
 bool rejected=false;try { damage_budget(100,100,1); } catch(const std::invalid_argument&) {rejected=true;}
 check(rejected,"invalid absorption rejected");
 check(damage_budget(100,200,2.0/3.0)>299.99,"armor absorption budget");
 check(damage_budget(10,200,2.0/3.0)<30.01,"excess armor is not simply added to low health");
 return failures?1:0;
}
