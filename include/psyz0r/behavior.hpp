#pragma once
#include <cstdint>
#include "psyz0r/opponent_stack.hpp"
#include <deque>
#include <random>
#include <string>
#include <unordered_set>
#include <unordered_map>
#include <vector>

namespace psyz0r {
struct BehaviorSettings {
    int aggressive_push_damage=85, thoughtful_retreat_damage=80, own_health_recover=30;
    double style_window=30, style_hold=20, style_margin=0.25;
    int style_min_samples=8;
    double engagement_timeout=5, gauntlet_duration=90, corpse_duration=1;
    int gauntlet_damage=50, relax_lead=20, relax_allow_frags=7, strong_opponent_frags=5, pressure_equal_score=10;
    double lead_tilt_probability=0.12, lead_tilt_duration=0, relax_probability=1;
    double total_control_probability=0.15;
    bool surrender_enabled=true;
    int surrender_deficit=5, surrender_own_max_score=0, surrender_min_streak=3;
    double surrender_probability=0.10, surrender_duration=0, opening_seconds=15;
    double close_distance=180, rail_distance=800, push_confidence_min=0.65;
    double relaxed_jump_scale=0.5, passive_jump_scale=0.25;
    double strong_min_observed_accuracy=0.5;
    int strong_min_samples=10;
    double item_mega_weight=100, item_red_weight=90, item_yellow_weight=60, item_health_weight=50;
    double item_travel_penalty=1, item_wait_penalty=2;
    int corpse_episode_threshold=3;
    double revenge_target_estimated_hp=50, revenge_contact_distance=64;
    int pressure_deficit=3, pressure_own_max_score=0, pressure_min_deaths=2, pressure_min_pushes=2, pressure_min_interruptions=1;
    int pressure_exit_health=100, pressure_exit_armor=50, pressure_allow_aggressive=0;
    double pressure_window=30, pressure_probability=0.6, pressure_min_duration=30, pressure_calm_window=15;
    double pressure_reentry_cooldown=60, pressure_withdraw_seconds=2, pressure_max_route_risk=0.25;
    double pressure_jump_scale=0.1;
    double pressure_cover_hold=3, pressure_health_weight=150, pressure_armor_weight=100;
    double pressure_rail_ammo_weight=80, pressure_major_item_weight=20, pressure_risk_penalty=200;
    static BehaviorSettings load(const std::string& path);
};
enum class Style { Aggressive, Thoughtful, Passive };
enum class Mood { Normal, Relaxed, LeadLossTilt, SurrenderTilt, PressureEscape };
enum class Intent { Recover, Hold, Push, RecklessPush, ShootCorpse, Escape, CoverRail };
enum class ItemPriority { None, Mega, MegaRed, YellowHealth, FullControl, SafeRecovery };
enum class Weapon { None, Gauntlet, Machinegun, Shotgun, Grenade, Rocket, Lightning, Rail, Plasma };
enum class ItemKind { Mega, Red, Yellow, Health, Green, RailAmmo };
struct ItemCandidate {
    std::string id;
    ItemKind kind;
    double expected_respawn=0, travel_seconds=0;
    double observed_route_risk=1;
    bool exit_open=false;
};
struct CoverCandidate {
    std::string id;
    ItemKind watched_item=ItemKind::Mega;
    double observed_route_risk=1;
    bool exit_open=false;
};
enum class EventKind { OpponentPush, OpponentRetreat, OpponentTrade, GauntletDamage,
                       OpponentCorpseShot, OpponentKilledBot, BotKilledOpponent, OpponentHit, OpponentMiss,
                       EstimatedDamageDealt, OwnDamageReceived, OwnRailHit, RecoveryInterrupted, OwnRailShot };
struct Event {
    std::uint64_t id; double time; EventKind kind; int amount=0;
    std::string opponent_id, source;
    bool verified=false;
    Weapon weapon=Weapon::None;
    std::string corpse_id;
    std::string location_id;
};
struct OpponentReaction {
    int gauntlet_damage=0, corpse_episodes=0;
    double revenge_until=0, corpse_action_started=-1;
    bool corpse_retaliation=false;
    std::string active_corpse;
    std::unordered_set<std::string> own_corpses_seen, enemy_corpses_used, eligible_enemy_corpses;
};
struct ReactionTrace {
    std::uint64_t event_id; std::string opponent_id, source, reason;
    int gauntlet_damage=0, corpse_episodes=0;
};
// Observations are sanitized by the future adapter: enemy_visible requires LOS and FOV.
// Owner-authorized exact HP/armor is separate from hidden-position knowledge.
struct Observation {
    StackContext stack_context;
    std::optional<ExactOpponentStack> exact_opponent_stack;
    double armor_absorption=2.0/3.0;
    bool armor_rules_verified=false;
    int health=100, armor=0;
    bool alive=true, enemy_visible=false;
    int damage_dealt=0, damage_received=0;
    bool hit_by_rail=false, favorable_fight_estimate=false;
    double time=0, enemy_distance=0, estimate_confidence=1;
    int bot_score=0, opponent_score=0;
    bool corpse_visible=false;
    std::string opponent_id, corpse_owner_id, corpse_id;
    bool safe_close_contact=false, safe_corpse_action=false;
    // Conservative HP estimate from legitimate observations, never server enemy HP.
    bool enemy_hp_estimate_valid=false;
    double enemy_hp_estimate=0;
    std::vector<Weapon> available_weapons;
    // Static map locations with observed predictions or owner-authorized exact timers.
    // Timer privilege never grants hidden live opponent positions.
    std::vector<ItemCandidate> item_candidates;
    // Static map cover candidates filtered by observed danger; no hidden enemy coordinates.
    std::vector<CoverCandidate> cover_candidates;
    std::string reached_cover_id;
    bool immediate_danger=false;
};
struct Decision {
    Intent intent=Intent::Hold;
    ItemPriority items=ItemPriority::MegaRed;
    Style style=Style::Thoughtful;
    Mood mood=Mood::Normal;
    Weapon weapon=Weapon::None;
    bool collect_resources=true, revenge_gauntlet=false, strict_yellow_timing=false;
    bool attack_visible_target=false;
    bool attack_visible_corpse=false;
    double jump_scale=1;
    std::string reason;
    std::string target_item;
    bool exact_stack_used=false;
    double own_damage_budget=0, opponent_damage_budget=0;
    std::string reaction_reason;
    std::string target_cover;
    bool quiet_walk_requested=false, fast_escape_requested=false;
};
class Behavior {
public:
    explicit Behavior(Style style=Style::Thoughtful, BehaviorSettings settings={}, unsigned seed=1);
    void set_style(Style style) { style_=style; }
    void trigger_surrender_tilt();
    void reset_match();
    void observe(const Event& event);
    void forget_opponent(const std::string& id);
    const OpponentReaction* reaction(const std::string& id) const;
    std::vector<ReactionTrace> drain_reaction_trace();
    Decision decide(const Observation& observation);
private:
    Style initial_style_, style_;
    BehaviorSettings settings_;
    std::mt19937 rng_;
    Mood mood_=Mood::Normal;
    bool surrender_checked_=false, lead_checked_=false;
    bool total_control_checked_=false, total_control_selected_=false;
    double mood_until_=0, last_style_change_=0, last_time_=0;
    std::unordered_map<std::string,OpponentReaction> reactions_;
    std::vector<ReactionTrace> reaction_trace_;
    int enemy_streak_=0, hits_=0, shots_=0, relax_start_enemy_=0;
    int episode_dealt_=0, episode_received_=0;
    bool episode_rail_=false;
    double last_combat_time_=-1;
    std::deque<Event> style_events_;
    std::unordered_set<std::uint64_t> event_ids_;
    std::deque<Event> pressure_events_;
    std::string pressure_opponent_, last_fired_cover_;
    double pressure_started_=0, pressure_last_exit_=-1000000, pressure_last_trial_=-1000000, rail_withdraw_until_=0;
    bool pressure_needs_reposition_=false, pressure_rail_pending_=false;
    std::string waiting_cover_;
    double cover_wait_started_=0;
    bool roll(double probability);
    void enter(Mood mood,double now,double duration);
    Weapon choose_weapon(const Observation&,bool revenge) const;
    void choose_item(const Observation&,Decision&) const;
};
}
