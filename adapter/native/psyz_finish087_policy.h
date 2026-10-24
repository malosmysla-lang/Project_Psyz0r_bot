/* Independent, per-bot finishing policy. No navigation or aim writes. */
#ifndef PSYZ_FINISH087_POLICY_H
#define PSYZ_FINISH087_POLICY_H
#include <math.h>
typedef struct {
    int current, weapons; const int *ammo;
    int own_health, own_armor, target_health, target_armor;
    int age_ms, attack, last_weapon, revenge;
    float distance, turn_degrees;
} PsyzFinish087Input;
enum { PSYZ_F087_KEEP, PSYZ_F087_RAIL, PSYZ_F087_ROCKET, PSYZ_F087_GAUNTLET,
       PSYZ_F090_SHOTGUN, PSYZ_F090_LIGHTNING };
typedef struct { int weapon, reason; } PsyzFinish087Choice;
static PsyzFinish087Choice Psyz_Finish087Choose(const PsyzFinish087Input *c) {
    PsyzFinish087Choice out={c->current,PSYZ_F087_KEEP};
    /* A hit is brief evidence of a shot line, never permission to track through walls. */
    if(!c->ammo || !c->attack || c->age_ms<0 || c->age_ms>100 ||
       !isfinite(c->distance) || !isfinite(c->turn_degrees) || c->distance<0 ||
       c->turn_degrees>8 || c->turn_degrees<0 || c->own_health<=0 ||
       c->target_health<=0 || c->target_health>1000 || c->target_armor<0 || c->target_armor>1000) return out;
    int effective=c->target_health+(c->target_armor<2*c->target_health?c->target_armor:2*c->target_health);
    /* Close revenge only after an actual visible direct hit and one-hit remaining stack. */
    if(c->revenge && c->distance<=56 && effective<=50 && c->own_health>=80 && (c->weapons&(1<<1))) {
        out.weapon=1;out.reason=PSYZ_F087_GAUNTLET;return out;
    }
    if(c->own_health>=45 && c->last_weapon==6 && c->distance>=260 && effective<=80 &&
       (c->weapons&(1<<7)) && c->ammo[7]>0) {
        out.weapon=7;out.reason=PSYZ_F087_RAIL;return out;
    }
    /* Do not launch a self-splash rocket at point-blank range. */
    if(c->last_weapon==6 && c->distance>=150 && c->distance<=280 && effective<=100 &&
       c->own_health>=90 && (c->weapons&(1<<5)) && c->ammo[5]>0) {
        out.weapon=5;out.reason=PSYZ_F087_ROCKET;return out;
    }
    /* Close finish: SG can still be safe with low own HP. Never compensate
       for an empty shotgun by forcing a self-splash rocket in this range.
       These are contact distances, not a request to chase an unseen enemy. */
    if(c->distance<150 && effective<=80 &&
       (c->weapons&(1<<3)) && c->ammo[3]>0){
        out.weapon=3;out.reason=PSYZ_F090_SHOTGUN;return out;
    }
    /* Sustain shaft at a useful range after a recent direct contact. This
       does not acquire the weapon, change aim, move the player or promise
       a kill; stock AAS still handles inventory acquisition and navigation. */
    if(c->own_health>=45 && c->distance>=192 && c->distance<=700 &&
       (c->weapons&(1<<6)) && c->ammo[6]>=12){
        out.weapon=6;out.reason=PSYZ_F090_LIGHTNING;return out;
    }
    return out;
}
#endif
