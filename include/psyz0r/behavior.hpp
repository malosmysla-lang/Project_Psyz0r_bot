#pragma once
#include <cstdint>
#include <deque>
#include <random>
#include <string>
#include <unordered_set>
#include <vector>

namespace psyz0r {
struct BehaviorSettings {
    int aggressive_push_damage=85, thoughtful_retreat_damage=80, own_health_recover=30;
    double style_window=30, style_hold=20, style_margin=0.25;
    int style_min_samples=8;
    double engagement_timeout=5, gauntlet_duration=30, corpse_duration=30;
    int gauntlet_damage=75, relax_lead=20, relax_allow_frags=7, strong_opponent_frags=5, pressure_equal_score=10;
    double lead_tilt_probability=0.015, lead_tilt_duration=0, relax_probability=1;
    bool surrender_enabled=true;
    int surrender_deficit=5, surrender_own_max_score=0, surrender_min_streak=3;
    double surrender_probability=0.10, surrender_duration=0, opening_seconds=15;
    double close_distance=180, rail_distance=800, push_confidence_min=0.65;
    double relaxed_jump_scale=0.5, passive_jump_scale=0.25;
    double strong_min_observed_accuracy=0.5;
    int strong_min_samples=10;
    double item_mega_weight=100, item_red_weight=90, item_yellow_weight=60, item_health_weight=50;
    double item_travel_penalty=1, item_wait_penalty=2;
    static BehaviorSettings load(const std::string& path);
};
enum class Style { Aggressive, Thoughtful, Passive };
enum class Mood { Normal, Relaxed, LeadLossTilt, SurrenderTilt };
enum class Intent { Recover, Hold, Push, RecklessPush, ShootCorpse };
enum class ItemPriority { None, Mega, MegaRed, YellowHealth, FullControl };
enum class Weapon { None, Gauntlet, Machinegun, Shotgun, Grenade, Rocket, Lightning, Rail, Plasma };
enum class ItemKind { Mega, Red, Yellow, Health };
struct ItemCandidate {
    std::string id;
    ItemKind kind;
    double expected_respawn=0, travel_seconds=0;
};
enum class EventKind { OpponentPush, OpponentRetreat, OpponentTrade, GauntletDamage,
                       OpponentCorpseShot, OpponentKilledBot, BotKilledOpponent, OpponentHit, OpponentMiss,
                       EstimatedDamageDealt, OwnDamageReceived, OwnRailHit };
struct Event { std::uint64_t id; double time; EventKind kind; int amount=0; };
// Observations are sanitized by the future adapter: enemy_visible requires LOS and FOV.
// Enemy HP/armor and hidden positions are deliberately absent.
struct Observation {
    int health=100, armor=0;
    bool alive=true, enemy_visible=false;
    int damage_dealt=0, damage_received=0;
    bool hit_by_rail=false, favorable_fight_estimate=false;
    double time=0, enemy_distance=0, estimate_confidence=1;
    int bot_score=0, opponent_score=0;
    bool corpse_visible=false;
    std::vector<Weapon> available_weapons;
    // Static map locations and observed timer predictions only, not hidden pickup state.
    std::vector<ItemCandidate> item_candidates;
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
};
class Behavior {
public:
    explicit Behavior(Style style=Style::Thoughtful, BehaviorSettings settings={}, unsigned seed=1);
    void set_style(Style style) { style_=style; }
    void trigger_surrender_tilt();
    void reset_match();
    void observe(const Event& event);
    Decision decide(const Observation& observation);
private:
    Style initial_style_, style_;
    BehaviorSettings settings_;
    std::mt19937 rng_;
    Mood mood_=Mood::Normal;
    bool surrender_checked_=false, lead_checked_=false;
    double mood_until_=0, last_style_change_=0, last_time_=0;
    double revenge_until_=0, corpse_until_=0, last_gauntlet_time_=-1;
    int gauntlet_damage_=0, enemy_streak_=0, hits_=0, shots_=0, relax_start_enemy_=0;
    int episode_dealt_=0, episode_received_=0;
    bool episode_rail_=false;
    double last_combat_time_=-1;
    std::deque<Event> style_events_;
    std::unordered_set<std::uint64_t> event_ids_;
    bool roll(double probability);
    void enter(Mood mood,double now,double duration);
    Weapon choose_weapon(const Observation&,bool revenge) const;
    void choose_item(const Observation&,Decision&) const;
};
}
