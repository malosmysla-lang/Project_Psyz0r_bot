#include "psyz0r/behavior.hpp"
#include <algorithm>
#include <cmath>
#include <fstream>
#include <limits>
#include <stdexcept>

namespace psyz0r {
BehaviorSettings BehaviorSettings::load(const std::string& path) {
    std::ifstream in(path);
    if (!in) throw std::runtime_error("Cannot open behavior settings");
    BehaviorSettings s;
    std::string key; double value;
    std::unordered_set<std::string> seen;
    while(in >> key) {
        if (!(in >> value) || !std::isfinite(value) || value<0 || !seen.insert(key).second)
            throw std::runtime_error("Invalid or duplicate setting: "+key);
#define INT_SETTING(name) if(key==#name) { if(value!=std::floor(value)||value>1000000) throw std::runtime_error("Invalid integer: "+key); s.name=static_cast<int>(value); } else
#define FLOAT_SETTING(name) if(key==#name) s.name=value; else
        INT_SETTING(aggressive_push_damage) INT_SETTING(thoughtful_retreat_damage) INT_SETTING(own_health_recover)
        INT_SETTING(style_min_samples) INT_SETTING(gauntlet_damage) INT_SETTING(relax_lead)
        INT_SETTING(relax_allow_frags) INT_SETTING(strong_opponent_frags) INT_SETTING(surrender_deficit)
        INT_SETTING(pressure_equal_score)
        INT_SETTING(surrender_own_max_score) INT_SETTING(surrender_min_streak) INT_SETTING(strong_min_samples)
        FLOAT_SETTING(style_window) FLOAT_SETTING(style_hold) FLOAT_SETTING(style_margin)
        FLOAT_SETTING(engagement_timeout) FLOAT_SETTING(gauntlet_duration) FLOAT_SETTING(corpse_duration)
        FLOAT_SETTING(lead_tilt_probability) FLOAT_SETTING(lead_tilt_duration)
        FLOAT_SETTING(relax_probability)
        FLOAT_SETTING(surrender_probability) FLOAT_SETTING(surrender_duration) FLOAT_SETTING(opening_seconds)
        FLOAT_SETTING(close_distance) FLOAT_SETTING(rail_distance) FLOAT_SETTING(push_confidence_min)
        FLOAT_SETTING(relaxed_jump_scale) FLOAT_SETTING(passive_jump_scale) FLOAT_SETTING(strong_min_observed_accuracy)
        FLOAT_SETTING(item_mega_weight) FLOAT_SETTING(item_red_weight) FLOAT_SETTING(item_yellow_weight)
        FLOAT_SETTING(item_health_weight) FLOAT_SETTING(item_travel_penalty) FLOAT_SETTING(item_wait_penalty)
        if(key=="surrender_enabled" && (value==0||value==1)) s.surrender_enabled=value==1;
        else throw std::runtime_error("Unknown setting: "+key);
#undef INT_SETTING
#undef FLOAT_SETTING
    }
    if(s.surrender_probability>1||s.lead_tilt_probability>1||s.relax_probability>1||s.style_margin>1||s.push_confidence_min>1||
       s.strong_min_observed_accuracy>1||s.relaxed_jump_scale>1||s.passive_jump_scale>1||
       s.style_min_samples<2||s.style_window<=0||s.close_distance>=s.rail_distance||s.surrender_deficit<1)
        throw std::runtime_error("Settings outside supported ranges");
    return s;
}
Behavior::Behavior(Style style,BehaviorSettings settings,unsigned seed)
    : initial_style_(style),style_(style),settings_(settings),rng_(seed) {}
bool Behavior::roll(double p) { return std::generate_canonical<double,53>(rng_)<p; }
void Behavior::enter(Mood mood,double now,double duration) {
    mood_=mood; mood_until_=duration==0?std::numeric_limits<double>::infinity():now+duration;
}
void Behavior::trigger_surrender_tilt() { surrender_checked_=true; enter(Mood::SurrenderTilt,last_time_,settings_.surrender_duration); }
void Behavior::reset_match() {
    style_=initial_style_; mood_=Mood::Normal; surrender_checked_=lead_checked_=false;
    mood_until_=last_style_change_=last_time_=revenge_until_=corpse_until_=0;
    last_gauntlet_time_=-1; gauntlet_damage_=enemy_streak_=hits_=shots_=relax_start_enemy_=0;
    style_events_.clear(); event_ids_.clear();
    episode_dealt_=episode_received_=0; episode_rail_=false; last_combat_time_=-1;
}
void Behavior::observe(const Event& e) {
    if(event_ids_.count(e.id)) return;
    if(!std::isfinite(e.time)||e.time<last_time_||e.amount<0) throw std::invalid_argument("Invalid observation event");
    if(!event_ids_.insert(e.id).second) return;
    last_time_=e.time;
    if(last_combat_time_>=0 && e.time-last_combat_time_>settings_.engagement_timeout) {
        episode_dealt_=episode_received_=0; episode_rail_=false;
    }
    switch(e.kind) {
    case EventKind::OpponentPush: case EventKind::OpponentRetreat: case EventKind::OpponentTrade:
        style_events_.push_back(e); break;
    case EventKind::GauntletDamage:
        if(last_gauntlet_time_<0||e.time-last_gauntlet_time_>settings_.engagement_timeout) gauntlet_damage_=0;
        last_gauntlet_time_=e.time; gauntlet_damage_+=e.amount;
        if(gauntlet_damage_>=settings_.gauntlet_damage) { revenge_until_=e.time+settings_.gauntlet_duration; gauntlet_damage_=0; }
        break;
    case EventKind::OpponentCorpseShot: corpse_until_=e.time+settings_.corpse_duration; break;
    case EventKind::OpponentKilledBot: ++enemy_streak_; episode_dealt_=episode_received_=0; episode_rail_=false; break;
    case EventKind::BotKilledOpponent: enemy_streak_=0; revenge_until_=0; episode_dealt_=episode_received_=0; episode_rail_=false; break;
    case EventKind::OpponentHit: ++hits_; ++shots_; break;
    case EventKind::OpponentMiss: ++shots_; break;
    case EventKind::EstimatedDamageDealt: episode_dealt_+=e.amount; last_combat_time_=e.time; break;
    case EventKind::OwnDamageReceived: episode_received_+=e.amount; last_combat_time_=e.time; break;
    case EventKind::OwnRailHit: episode_rail_=true; last_combat_time_=e.time; break;
    }
}
Weapon Behavior::choose_weapon(const Observation& o,bool revenge) const {
    auto has=[&](Weapon w){return std::find(o.available_weapons.begin(),o.available_weapons.end(),w)!=o.available_weapons.end();};
    if(revenge && has(Weapon::Gauntlet)) return Weapon::Gauntlet;
    if(o.enemy_visible && o.enemy_distance>=settings_.rail_distance && has(Weapon::Rail)) return Weapon::Rail;
    if(o.enemy_visible && o.enemy_distance<settings_.close_distance && has(Weapon::Shotgun)) return Weapon::Shotgun;
    for(auto w:{Weapon::Lightning,Weapon::Rocket,Weapon::Rail,Weapon::Plasma,Weapon::Shotgun,Weapon::Machinegun,Weapon::Grenade,Weapon::Gauntlet})
        if(has(w)) return w;
    return Weapon::None;
}
void Behavior::choose_item(const Observation& o,Decision& d) const {
    if(!d.collect_resources||d.items==ItemPriority::None) return;
    double best=-std::numeric_limits<double>::infinity();
    for(const auto& item:o.item_candidates) {
        if(item.id.empty()||!std::isfinite(item.expected_respawn)||!std::isfinite(item.travel_seconds)||item.travel_seconds<0) continue;
        if(d.items==ItemPriority::Mega && item.kind!=ItemKind::Mega) continue;
        if(d.items==ItemPriority::YellowHealth && item.kind!=ItemKind::Yellow&&item.kind!=ItemKind::Health) continue;
        double weight=item.kind==ItemKind::Mega?settings_.item_mega_weight:item.kind==ItemKind::Red?settings_.item_red_weight:
            item.kind==ItemKind::Yellow?settings_.item_yellow_weight:settings_.item_health_weight;
        double score=weight-settings_.item_travel_penalty*item.travel_seconds-
            settings_.item_wait_penalty*std::max(0.0,item.expected_respawn-o.time-item.travel_seconds);
        if(score>best) {best=score;d.target_item=item.id;}
    }
}
Decision Behavior::decide(const Observation& o) {
    if(!std::isfinite(o.time)||o.time<last_time_||(o.alive&&o.health<0)||o.armor<0||o.damage_dealt<0||o.damage_received<0||
       !std::isfinite(o.estimate_confidence)||o.estimate_confidence<0||o.estimate_confidence>1)
        throw std::invalid_argument("Invalid player observation");
    last_time_=o.time;
    if(last_combat_time_>=0 && o.time-last_combat_time_>settings_.engagement_timeout) {
        episode_dealt_=episode_received_=0; episode_rail_=false;
    }
    while(!style_events_.empty() && o.time-style_events_.front().time>settings_.style_window) style_events_.pop_front();
    if(style_events_.size()>=static_cast<std::size_t>(settings_.style_min_samples) && o.time-last_style_change_>=settings_.style_hold) {
        int counts[3]={0,0,0};
        for(const auto& e:style_events_) ++counts[e.kind==EventKind::OpponentPush?0:e.kind==EventKind::OpponentTrade?1:2];
        int current=style_==Style::Aggressive?0:style_==Style::Thoughtful?1:2;
        int candidate=static_cast<int>(std::max_element(counts,counts+3)-counts);
        if(candidate!=current && static_cast<double>(counts[candidate]-counts[current])/style_events_.size()>=settings_.style_margin) {
            style_=candidate==0?Style::Aggressive:candidate==1?Style::Thoughtful:Style::Passive;
            last_style_change_=o.time;
        }
    }
    if((mood_==Mood::LeadLossTilt||mood_==Mood::SurrenderTilt)&&o.time>=mood_until_) mood_=Mood::Normal;
    int lead=o.bot_score-o.opponent_score;
    bool strong=o.opponent_score>=settings_.strong_opponent_frags ||
        (shots_>=settings_.strong_min_samples && static_cast<double>(hits_)/shots_>=settings_.strong_min_observed_accuracy);
    if(mood_==Mood::Normal && !surrender_checked_ && settings_.surrender_enabled && -lead>=settings_.surrender_deficit &&
       o.bot_score<=settings_.surrender_own_max_score && enemy_streak_>=settings_.surrender_min_streak) {
        surrender_checked_=true;
        if(roll(settings_.surrender_probability)) enter(Mood::SurrenderTilt,o.time,settings_.surrender_duration);
    }
    if(mood_==Mood::Normal && !lead_checked_ && lead>=settings_.relax_lead) {
        lead_checked_=true;
        if(roll(settings_.lead_tilt_probability)) enter(Mood::LeadLossTilt,o.time,settings_.lead_tilt_duration);
        else if(!strong && roll(settings_.relax_probability)) { mood_=Mood::Relaxed; relax_start_enemy_=o.opponent_score; }
    }
    if(mood_==Mood::Relaxed && (lead<=0||o.opponent_score-relax_start_enemy_>=settings_.relax_allow_frags)) mood_=Mood::Normal;
    Decision d; d.style=style_; d.mood=mood_;
    d.revenge_gauntlet=o.time<revenge_until_ && std::find(o.available_weapons.begin(),o.available_weapons.end(),Weapon::Gauntlet)!=o.available_weapons.end();
    d.weapon=choose_weapon(o,d.revenge_gauntlet);
    d.attack_visible_target=o.enemy_visible && d.weapon!=Weapon::None;
    d.strict_yellow_timing=strong;
    if(style_==Style::Passive) d.jump_scale=settings_.passive_jump_scale;
    if(!o.alive) {
        d.attack_visible_target=false; d.collect_resources=false; d.items=ItemPriority::None;
        d.reason="dead_wait_respawn"; return d;
    }
    if(mood_==Mood::SurrenderTilt||mood_==Mood::LeadLossTilt) {
        d.intent=Intent::RecklessPush; d.items=ItemPriority::None; d.collect_resources=false;
        d.revenge_gauntlet=false;
        if(mood_==Mood::SurrenderTilt) d.weapon=o.available_weapons.empty()?Weapon::None:o.available_weapons.front();
        d.attack_visible_target=o.enemy_visible && d.weapon!=Weapon::None;
        d.reason=mood_==Mood::SurrenderTilt?"behavioral_forfeit":"throwing_own_lead"; return d;
    }
    if(mood_==Mood::Relaxed) {
        d.jump_scale=settings_.relaxed_jump_scale; d.strict_yellow_timing=false;
        d.collect_resources=false; d.items=ItemPriority::None;
    }
    if(o.health<=settings_.own_health_recover || (style_==Style::Passive&&(o.hit_by_rail||episode_rail_)) ||
       (style_==Style::Thoughtful&&std::max(o.damage_received,episode_received_)>=settings_.thoughtful_retreat_damage)) {
        d.intent=Intent::Recover; d.items=ItemPriority::YellowHealth; d.collect_resources=true;
        d.reason="recover_after_damage"; choose_item(o,d); return d;
    }
    if(style_==Style::Passive && mood_!=Mood::Relaxed) { d.items=ItemPriority::YellowHealth; d.jump_scale=settings_.passive_jump_scale; }
    else if(o.time<settings_.opening_seconds) d.items=ItemPriority::Mega;
    else if(mood_!=Mood::Relaxed&&lead<=0) d.items=ItemPriority::FullControl;
    if(o.time>=settings_.opening_seconds && style_==Style::Aggressive && mood_!=Mood::Relaxed && o.enemy_visible && o.favorable_fight_estimate &&
       o.estimate_confidence>=settings_.push_confidence_min && std::max(o.damage_dealt,episode_dealt_)>=settings_.aggressive_push_damage)
        { d.intent=Intent::Push; d.reason="damage_estimate_push"; }
    else if(o.time>=settings_.opening_seconds && mood_!=Mood::Relaxed && o.enemy_visible &&
        (lead<0||(lead==0&&o.bot_score>=settings_.pressure_equal_score)) && o.favorable_fight_estimate && style_!=Style::Passive)
        { d.intent=Intent::Push; d.reason="score_pressure"; }
    else { d.reason=mood_==Mood::Relaxed?"relaxed_hold":"controlled_hold"; }
    if(d.revenge_gauntlet && o.enemy_visible && mood_!=Mood::Relaxed) { d.intent=Intent::Push; d.reason="gauntlet_revenge"; }
    if(o.corpse_visible && !o.enemy_visible && o.time<corpse_until_ && d.weapon!=Weapon::None) {
        d.intent=Intent::ShootCorpse; d.attack_visible_target=false; d.attack_visible_corpse=true;
        d.reason="observed_corpse_retaliation";
    }
    choose_item(o,d);
    return d;
}
}
