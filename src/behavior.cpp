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
        INT_SETTING(pressure_deficit) INT_SETTING(pressure_own_max_score) INT_SETTING(pressure_min_deaths)
        INT_SETTING(pressure_min_pushes) INT_SETTING(pressure_min_interruptions) INT_SETTING(pressure_exit_health)
        INT_SETTING(pressure_exit_armor) INT_SETTING(pressure_allow_aggressive)
        FLOAT_SETTING(pressure_window) FLOAT_SETTING(pressure_probability) FLOAT_SETTING(pressure_min_duration)
        FLOAT_SETTING(pressure_calm_window) FLOAT_SETTING(pressure_reentry_cooldown) FLOAT_SETTING(pressure_withdraw_seconds)
        FLOAT_SETTING(pressure_max_route_risk) FLOAT_SETTING(pressure_jump_scale)
        FLOAT_SETTING(pressure_cover_hold) FLOAT_SETTING(pressure_health_weight) FLOAT_SETTING(pressure_armor_weight)
        FLOAT_SETTING(pressure_rail_ammo_weight) FLOAT_SETTING(pressure_major_item_weight) FLOAT_SETTING(pressure_risk_penalty)
        INT_SETTING(aggressive_push_damage) INT_SETTING(thoughtful_retreat_damage) INT_SETTING(own_health_recover)
        INT_SETTING(style_min_samples) INT_SETTING(gauntlet_damage) INT_SETTING(relax_lead)
        INT_SETTING(relax_allow_frags) INT_SETTING(strong_opponent_frags) INT_SETTING(surrender_deficit)
        INT_SETTING(pressure_equal_score) INT_SETTING(corpse_episode_threshold)
        INT_SETTING(surrender_own_max_score) INT_SETTING(surrender_min_streak) INT_SETTING(strong_min_samples)
        FLOAT_SETTING(style_window) FLOAT_SETTING(style_hold) FLOAT_SETTING(style_margin)
        FLOAT_SETTING(engagement_timeout) FLOAT_SETTING(gauntlet_duration) FLOAT_SETTING(corpse_duration)
        FLOAT_SETTING(lead_tilt_probability) FLOAT_SETTING(lead_tilt_duration)
        FLOAT_SETTING(relax_probability)
        FLOAT_SETTING(total_control_probability)
        FLOAT_SETTING(surrender_probability) FLOAT_SETTING(surrender_duration) FLOAT_SETTING(opening_seconds)
        FLOAT_SETTING(revenge_target_estimated_hp) FLOAT_SETTING(revenge_contact_distance)
        FLOAT_SETTING(close_distance) FLOAT_SETTING(rail_distance) FLOAT_SETTING(push_confidence_min)
        FLOAT_SETTING(relaxed_jump_scale) FLOAT_SETTING(passive_jump_scale) FLOAT_SETTING(strong_min_observed_accuracy)
        FLOAT_SETTING(item_mega_weight) FLOAT_SETTING(item_red_weight) FLOAT_SETTING(item_yellow_weight)
        FLOAT_SETTING(item_health_weight) FLOAT_SETTING(item_travel_penalty) FLOAT_SETTING(item_wait_penalty)
        if(key=="surrender_enabled" && (value==0||value==1)) s.surrender_enabled=value==1;
        else throw std::runtime_error("Unknown setting: "+key);
#undef INT_SETTING
#undef FLOAT_SETTING
    }
    if(s.surrender_probability>1||s.lead_tilt_probability>1||s.total_control_probability>1||s.relax_probability>1||s.style_margin>1||s.push_confidence_min>1||
       s.strong_min_observed_accuracy>1||s.relaxed_jump_scale>1||s.passive_jump_scale>1||
       s.style_min_samples<2||s.style_window<=0||s.close_distance>=s.rail_distance||s.surrender_deficit<1||s.gauntlet_damage<1||s.gauntlet_duration<=0||s.corpse_episode_threshold<1||s.corpse_duration>1||s.corpse_duration<=0||s.revenge_contact_distance<=0)
        throw std::runtime_error("Settings outside supported ranges");
    if(s.pressure_deficit<1||s.pressure_window<=0||s.pressure_probability>1||s.pressure_max_route_risk>1||
       s.pressure_jump_scale>1||s.pressure_allow_aggressive>1||s.pressure_min_deaths<1||s.pressure_min_pushes<1||
       s.pressure_min_interruptions<1||s.pressure_calm_window<=0||s.pressure_withdraw_seconds<=0||s.pressure_cover_hold<=0)
        throw std::runtime_error("Invalid pressure_escape settings");
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
    total_control_checked_=total_control_selected_=false;
    mood_until_=last_style_change_=last_time_=0;
    pressure_events_.clear(); pressure_opponent_.clear(); last_fired_cover_.clear();
    waiting_cover_.clear();cover_wait_started_=0;
    pressure_started_=rail_withdraw_until_=0; pressure_last_exit_=pressure_last_trial_=-1000000; pressure_needs_reposition_=pressure_rail_pending_=false;
    reactions_.clear(); reaction_trace_.clear(); enemy_streak_=hits_=shots_=relax_start_enemy_=0;
    style_events_.clear(); event_ids_.clear();
    episode_dealt_=episode_received_=0; episode_rail_=false; last_combat_time_=-1;
}
void Behavior::forget_opponent(const std::string& id) {
    reactions_.erase(id);
    pressure_events_.erase(std::remove_if(pressure_events_.begin(),pressure_events_.end(),[&](const Event& e){return e.opponent_id==id;}),pressure_events_.end());
    if(pressure_opponent_==id) { if(mood_==Mood::PressureEscape) mood_=Mood::Normal; pressure_opponent_.clear(); }
}
const OpponentReaction* Behavior::reaction(const std::string& id) const {
    auto it=reactions_.find(id); return it==reactions_.end()?nullptr:&it->second;
}
std::vector<ReactionTrace> Behavior::drain_reaction_trace() {
    auto result=std::move(reaction_trace_); reaction_trace_.clear(); return result;
}
void Behavior::observe(const Event& e) {
    if(event_ids_.count(e.id)) return;
    if(!std::isfinite(e.time)||e.time<last_time_||e.amount<0) throw std::invalid_argument("Invalid observation event");
    if(!event_ids_.insert(e.id).second) return;
    last_time_=e.time;
    if(last_combat_time_>=0 && e.time-last_combat_time_>settings_.engagement_timeout) {
        episode_dealt_=episode_received_=0; episode_rail_=false;
    }
    if(e.verified && !e.source.empty() && !e.opponent_id.empty() &&
       (e.kind==EventKind::OpponentPush||e.kind==EventKind::OpponentKilledBot||e.kind==EventKind::RecoveryInterrupted))
        pressure_events_.push_back(e);
    switch(e.kind) {
    case EventKind::OpponentPush: case EventKind::OpponentRetreat: case EventKind::OpponentTrade:
        style_events_.push_back(e); break;
    case EventKind::GauntletDamage: case EventKind::OpponentCorpseShot: {
        if(!e.verified||e.opponent_id.empty()||e.source.empty()||
           (e.kind==EventKind::GauntletDamage && e.amount==0)||
           (e.kind==EventKind::OpponentCorpseShot && e.corpse_id.empty())) {
            reaction_trace_.push_back({e.id,e.opponent_id,e.source,"rejected_unverified_event"}); break;
        }
        auto& r=reactions_[e.opponent_id];
        std::string reason;
        if(e.kind==EventKind::GauntletDamage) {
            r.gauntlet_damage=std::min(1000000,r.gauntlet_damage+std::min(e.amount,1000000));
            reason="gauntlet_damage_below_threshold";
            if(r.gauntlet_damage>=settings_.gauntlet_damage && e.time>=r.revenge_until) {
                r.revenge_until=e.time+settings_.gauntlet_duration;
                r.gauntlet_damage=0; reason="revenge_started";
            }
        } else if(r.own_corpses_seen.insert(e.corpse_id).second) {
            ++r.corpse_episodes; reason="corpse_episode_ignored";
            if(!r.corpse_retaliation && r.corpse_episodes>=settings_.corpse_episode_threshold) {
                r.corpse_retaliation=true; r.eligible_enemy_corpses.clear(); reason="corpse_retaliation_enabled";
            }
        } else reason="same_corpse_episode_ignored";
        reaction_trace_.push_back({e.id,e.opponent_id,e.source,reason,r.gauntlet_damage,r.corpse_episodes});
        break;
    }
    case EventKind::OpponentKilledBot: ++enemy_streak_; episode_dealt_=episode_received_=0; episode_rail_=false; break;
    case EventKind::BotKilledOpponent:
        enemy_streak_=0; episode_dealt_=episode_received_=0; episode_rail_=false;
        if(e.verified && !e.opponent_id.empty() && !e.source.empty() && !e.corpse_id.empty())
            if(reactions_[e.opponent_id].corpse_retaliation) reactions_[e.opponent_id].eligible_enemy_corpses.insert(e.corpse_id);
        if(e.verified && e.weapon==Weapon::Gauntlet && !e.opponent_id.empty() && !e.source.empty()) {
            auto it=reactions_.find(e.opponent_id);
            if(it!=reactions_.end() && e.time<it->second.revenge_until) {
                it->second.revenge_until=0; it->second.gauntlet_damage=0;
                reaction_trace_.push_back({e.id,e.opponent_id,e.source,"revenge_completed_gauntlet_kill"});
            }
        }
        break;
    case EventKind::RecoveryInterrupted: break;
    case EventKind::OwnRailShot:
        if(e.verified && !e.source.empty() && e.weapon==Weapon::Rail && mood_==Mood::PressureEscape && e.opponent_id==pressure_opponent_) {
            rail_withdraw_until_=e.time+settings_.pressure_withdraw_seconds;
            pressure_rail_pending_=false; pressure_needs_reposition_=true; last_fired_cover_=e.location_id;
            reaction_trace_.push_back({e.id,e.opponent_id,e.source,"pressure_escape_rail_fired_withdraw"});
        }
        break;
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
        if(d.items==ItemPriority::SafeRecovery && (!item.exit_open||!std::isfinite(item.observed_route_risk)||
           item.observed_route_risk<0||item.observed_route_risk>settings_.pressure_max_route_risk)) continue;
        double weight=item.kind==ItemKind::Mega?settings_.item_mega_weight:item.kind==ItemKind::Red?settings_.item_red_weight:
            item.kind==ItemKind::Yellow?settings_.item_yellow_weight:settings_.item_health_weight;
        if(d.items==ItemPriority::SafeRecovery) {
            weight=item.kind==ItemKind::Health?settings_.pressure_health_weight:
                (item.kind==ItemKind::Yellow||item.kind==ItemKind::Green)?settings_.pressure_armor_weight:
                item.kind==ItemKind::RailAmmo?settings_.pressure_rail_ammo_weight:settings_.pressure_major_item_weight;
        }
        double score=weight-settings_.item_travel_penalty*item.travel_seconds-
            (d.items==ItemPriority::SafeRecovery?settings_.pressure_risk_penalty*item.observed_route_risk:0)-
            settings_.item_wait_penalty*std::max(0.0,item.expected_respawn-o.time-item.travel_seconds);
        if(score>best) {best=score;d.target_item=item.id;}
    }
}
Decision Behavior::decide(const Observation& o) {
    if(!std::isfinite(o.time)||o.time<last_time_||(o.alive&&o.health<0)||o.armor<0||o.damage_dealt<0||o.damage_received<0||
       !std::isfinite(o.enemy_distance)||o.enemy_distance<0||
       (o.enemy_hp_estimate_valid&&(!std::isfinite(o.enemy_hp_estimate)||o.enemy_hp_estimate<0))||
       !std::isfinite(o.estimate_confidence)||o.estimate_confidence<0||o.estimate_confidence>1)
        throw std::invalid_argument("Invalid player observation");
    const auto exact = o.stack_context.opponent_id==o.opponent_id
        ? current_stack(o.exact_opponent_stack,o.stack_context,o.time) : std::nullopt;
    const bool stack_known=exact && o.alive && o.health>0 && o.armor_rules_verified && std::isfinite(o.armor_absorption) &&
        o.armor_absorption>0 && o.armor_absorption<1;
    const double own_budget=stack_known?damage_budget(o.health,o.armor,o.armor_absorption):0;
    const double enemy_budget=stack_known?damage_budget(exact->health,exact->armor,o.armor_absorption):0;
    // Stack advantage is necessary evidence, not permission for blind pursuit.
    const bool favorable=stack_known?own_budget>=enemy_budget*1.15:o.favorable_fight_estimate;
    const bool outstacked=stack_known && enemy_budget>=own_budget*1.15;
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
    while(!pressure_events_.empty()&&o.time-pressure_events_.front().time>settings_.pressure_window) pressure_events_.pop_front();
    int pressure_deaths=0,pressure_pushes=0,pressure_interruptions=0;
    double last_pressure=-1000000;
    for(const auto& e:pressure_events_) if(e.opponent_id==o.opponent_id) {
        last_pressure=std::max(last_pressure,e.time);
        if(e.kind==EventKind::OpponentKilledBot) ++pressure_deaths;
        if(e.kind==EventKind::OpponentPush) ++pressure_pushes;
        if(e.kind==EventKind::RecoveryInterrupted) ++pressure_interruptions;
    }
    if(mood_==Mood::PressureEscape && (o.opponent_id!=pressure_opponent_ ||
       (o.time-pressure_started_>=settings_.pressure_min_duration && o.time-last_pressure>=settings_.pressure_calm_window &&
        o.alive && o.health>=settings_.pressure_exit_health && o.armor>=settings_.pressure_exit_armor))) {
        mood_=Mood::Normal; pressure_last_exit_=o.time;
        reaction_trace_.push_back({0,o.opponent_id,"behavior_policy","pressure_escape_recovered_exit"});
    }
    if(mood_==Mood::Normal && o.alive && !o.opponent_id.empty() &&
       (style_!=Style::Aggressive||settings_.pressure_allow_aggressive) && -lead>=settings_.pressure_deficit &&
       o.bot_score<=settings_.pressure_own_max_score && o.time-std::max(pressure_last_exit_,pressure_last_trial_)>=settings_.pressure_reentry_cooldown &&
       pressure_deaths>=settings_.pressure_min_deaths && pressure_pushes>=settings_.pressure_min_pushes &&
       pressure_interruptions>=settings_.pressure_min_interruptions) {
        pressure_last_trial_=o.time; // one probability trial per configured cooldown, never per frame
        if(roll(settings_.pressure_probability)) {
            mood_=Mood::PressureEscape;pressure_started_=o.time;pressure_opponent_=o.opponent_id;
            waiting_cover_.clear();cover_wait_started_=0;
            pressure_needs_reposition_=pressure_rail_pending_=false;last_fired_cover_.clear();rail_withdraw_until_=0;
            reaction_trace_.push_back({0,o.opponent_id,"behavior_policy","pressure_escape_repeated_pressure_enter"});
        } else reaction_trace_.push_back({0,o.opponent_id,"behavior_policy","pressure_escape_probability_declined"});
    }
    if(mood_==Mood::Normal && !surrender_checked_ && settings_.surrender_enabled && o.time-pressure_last_exit_>=settings_.pressure_reentry_cooldown && -lead>=settings_.surrender_deficit &&
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
    d.exact_stack_used=stack_known; d.own_damage_budget=own_budget; d.opponent_damage_budget=enemy_budget;
    auto it=reactions_.find(o.opponent_id);
    OpponentReaction* r=it==reactions_.end()?nullptr:&it->second;
    d.revenge_gauntlet=r && o.time<r->revenge_until;
    const bool target_hp_known=exact.has_value() || o.enemy_hp_estimate_valid;
    const double target_hp=exact?exact->health:o.enemy_hp_estimate;
    bool attempt=d.revenge_gauntlet && o.alive && o.enemy_visible && o.safe_close_contact &&
        o.enemy_distance<=settings_.revenge_contact_distance && target_hp_known &&
        target_hp<=settings_.revenge_target_estimated_hp && o.health>settings_.own_health_recover &&
        std::find(o.available_weapons.begin(),o.available_weapons.end(),Weapon::Gauntlet)!=o.available_weapons.end();
    d.reaction_reason=!d.revenge_gauntlet?"no_active_revenge":!o.enemy_visible?"revenge_no_visible_contact":
        !o.safe_close_contact?"revenge_unsafe_approach":o.enemy_distance>settings_.revenge_contact_distance?"revenge_out_of_contact":
        !target_hp_known?"revenge_unknown_hp_estimate":target_hp>settings_.revenge_target_estimated_hp?"revenge_target_not_low":
        o.health<=settings_.own_health_recover?"revenge_own_health_low":attempt?"gauntlet_finish_attempt":"revenge_no_usable_gauntlet";
    d.weapon=choose_weapon(o,attempt);
    d.attack_visible_target=o.enemy_visible && d.weapon!=Weapon::None;
    d.strict_yellow_timing=strong;
    if(style_==Style::Passive) d.jump_scale=settings_.passive_jump_scale;
    if(!o.alive) {
        d.attack_visible_target=false; d.collect_resources=false; d.items=ItemPriority::None;
        d.reaction_reason="revenge_wait_respawn"; d.reason="dead_wait_respawn"; return d;
    }
    if(mood_==Mood::SurrenderTilt||mood_==Mood::LeadLossTilt) {
        d.intent=Intent::RecklessPush; d.items=ItemPriority::None; d.collect_resources=false;
        d.revenge_gauntlet=false; d.reaction_reason="revenge_suspended_by_tilt";
        if(mood_==Mood::SurrenderTilt) d.weapon=o.available_weapons.empty()?Weapon::None:o.available_weapons.front();
        d.attack_visible_target=o.enemy_visible && d.weapon!=Weapon::None;
        d.reason=mood_==Mood::SurrenderTilt?"behavioral_forfeit":"throwing_own_lead"; return d;
    }
    if(mood_==Mood::PressureEscape) {
        d.intent=Intent::Escape; d.items=ItemPriority::SafeRecovery;d.collect_resources=true;
        d.revenge_gauntlet=false;
        auto defence=o; defence.available_weapons.erase(std::remove(defence.available_weapons.begin(),defence.available_weapons.end(),Weapon::Rail),defence.available_weapons.end());
        d.weapon=choose_weapon(defence,false);d.attack_visible_target=o.enemy_visible&&d.weapon!=Weapon::None;
        d.reaction_reason="revenge_suspended_by_pressure_escape";
        d.jump_scale=settings_.pressure_jump_scale;
        d.fast_escape_requested=o.immediate_danger||o.enemy_visible||o.time<rail_withdraw_until_;
        d.quiet_walk_requested=!d.fast_escape_requested;
        d.reason=d.fast_escape_requested?"pressure_escape_fast_withdraw":"pressure_escape_safe_recovery";
        double best_risk=2;
        for(const auto& cover:o.cover_candidates) {
            if(cover.id.empty()||!cover.exit_open||!std::isfinite(cover.observed_route_risk)||cover.observed_route_risk<0||
               cover.observed_route_risk>settings_.pressure_max_route_risk||
               (cover.watched_item!=ItemKind::Mega&&cover.watched_item!=ItemKind::Red)||
               (pressure_needs_reposition_&&cover.id==last_fired_cover_)) continue;
            if(cover.observed_route_risk<best_risk) {best_risk=cover.observed_route_risk;d.target_cover=cover.id;}
        }
        bool rail_available=std::find(o.available_weapons.begin(),o.available_weapons.end(),Weapon::Rail)!=o.available_weapons.end();
        if(!rail_available) {d.target_cover.clear();d.reason="pressure_escape_seek_rail_ammo";}
        else if(!pressure_rail_pending_ && !o.immediate_danger && o.time>=rail_withdraw_until_ && !d.target_cover.empty() &&
                o.reached_cover_id==d.target_cover && o.health>settings_.own_health_recover) {
            d.intent=Intent::CoverRail;d.weapon=Weapon::Rail;
            d.attack_visible_target=o.enemy_visible;
            if(o.enemy_visible) pressure_rail_pending_=true;
            d.quiet_walk_requested=!o.enemy_visible;d.fast_escape_requested=false;
            d.reason=o.enemy_visible?"pressure_escape_one_rail_attempt":"pressure_escape_wait_visible_target";
            if(!o.enemy_visible) {
                if(waiting_cover_!=d.target_cover) {waiting_cover_=d.target_cover;cover_wait_started_=o.time;}
                if(o.time-cover_wait_started_>=settings_.pressure_cover_hold) {
                    last_fired_cover_=d.target_cover;pressure_needs_reposition_=true;
                    d.target_cover.clear();d.intent=Intent::Escape;d.reason="pressure_escape_cover_wait_expired_relocate";
                }
            }
        }
        if(pressure_rail_pending_ && d.intent!=Intent::CoverRail) {
            d.reason="pressure_escape_wait_fire_confirmation";
        }
        // Once a rail command is requested, caller must confirm actual fire; no hit-dependent push.
        choose_item(o,d);return d;
    }
    if(mood_==Mood::Relaxed) {
        d.jump_scale=settings_.relaxed_jump_scale; d.strict_yellow_timing=false;
        d.collect_resources=false; d.items=ItemPriority::None;
    }
    if((outstacked && mood_==Mood::Normal) || o.health<=settings_.own_health_recover || (style_==Style::Passive&&(o.hit_by_rail||episode_rail_)) ||
       (style_==Style::Thoughtful&&std::max(o.damage_received,episode_received_)>=settings_.thoughtful_retreat_damage)) {
        d.intent=Intent::Recover; d.items=ItemPriority::YellowHealth; d.collect_resources=true;
        d.weapon=choose_weapon(o,false); d.reaction_reason="revenge_recovery_has_priority";
        d.reason=outstacked?"recover_against_exact_stack":"recover_after_damage"; choose_item(o,d); return d;
    }
    if(style_==Style::Passive && mood_!=Mood::Relaxed) { d.items=ItemPriority::YellowHealth; d.jump_scale=settings_.passive_jump_scale; }
    else if(o.time<settings_.opening_seconds) d.items=ItemPriority::Mega;
    else if(mood_==Mood::Normal && strong && o.time>=settings_.opening_seconds) {
        if(!total_control_checked_) {
            total_control_checked_=true;
            total_control_selected_=roll(settings_.total_control_probability);
            reaction_trace_.push_back({0,o.opponent_id,"behavior_policy",
                total_control_selected_?"total_control_match_trial_selected":"total_control_match_trial_declined"});
        }
        if(total_control_selected_) d.items=ItemPriority::FullControl;
    }
    if(o.time>=settings_.opening_seconds && style_==Style::Aggressive && mood_!=Mood::Relaxed && o.enemy_visible && favorable &&
       o.estimate_confidence>=settings_.push_confidence_min && std::max(o.damage_dealt,episode_dealt_)>=settings_.aggressive_push_damage)
        { d.intent=Intent::Push; d.reason="damage_estimate_push"; }
    else if(o.time>=settings_.opening_seconds && mood_!=Mood::Relaxed && o.enemy_visible &&
        (lead<0||(lead==0&&o.bot_score>=settings_.pressure_equal_score)) && favorable && style_!=Style::Passive)
        { d.intent=Intent::Push; d.reason="score_pressure"; }
    else { d.reason=mood_==Mood::Relaxed?"relaxed_hold":"controlled_hold"; }
    if(attempt) { d.intent=Intent::Push; d.reason="gauntlet_revenge"; }
    if(r && r->corpse_retaliation && o.safe_corpse_action && o.corpse_visible && !o.enemy_visible &&
       o.corpse_owner_id==o.opponent_id && r->eligible_enemy_corpses.count(o.corpse_id) && d.weapon!=Weapon::None) {
        if(!r->enemy_corpses_used.count(o.corpse_id)) {
            r->enemy_corpses_used.insert(o.corpse_id); r->corpse_action_started=o.time; r->active_corpse=o.corpse_id;
        }
        if(r->active_corpse==o.corpse_id && r->corpse_action_started>=0 && o.time-r->corpse_action_started<settings_.corpse_duration) {
            d.intent=Intent::ShootCorpse; d.attack_visible_target=false; d.attack_visible_corpse=true;
            d.reason="observed_corpse_retaliation";
        }
    } else if(r) r->corpse_action_started=-1;
    choose_item(o,d);
    return d;
}
}
