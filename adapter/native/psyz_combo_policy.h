/* Offline-tested finishing policy. Not connected to retail usercmd yet. */
#ifndef PSYZ_COMBO_POLICY_H
#define PSYZ_COMBO_POLICY_H
#include <math.h>
enum {PSYZ_COMBO_KEEP,PSYZ_COMBO_NO_OBSERVATION,PSYZ_COMBO_STALE_HIT,
      PSYZ_COMBO_RAIL_FINISH,PSYZ_COMBO_LG_FINISH,PSYZ_COMBO_ROCKET_CLOSE,
      PSYZ_COMBO_GAUNTLET_REVENGE,PSYZ_COMBO_SHOTGUN_CLOSE};
typedef struct {
    int current_weapon,weapons;
    const int *ammo;
    float distance;
    int own_health,own_armor,enemy_health,enemy_armor;
    int enemy_visible,stack_known,last_hit_weapon,last_hit_age_ms;
    int closing,revenge_active,melee_path_clear;
} PsyzComboContext;
typedef struct {int weapon,reason;} PsyzComboChoice;
static int Psyz_ComboStack(int health,int armor){
    if(health<=0)return 0;
    return health+(armor<2*health?armor:2*health);
}
static int Psyz_ComboHas(const PsyzComboContext *c,int weapon,int rounds){
    return c->ammo && (c->weapons&(1<<weapon)) && (weapon==1 || c->ammo[weapon]>=rounds);
}
static PsyzComboChoice Psyz_ComboChoose(const PsyzComboContext *c){
    PsyzComboChoice out={c->current_weapon,PSYZ_COMBO_KEEP};
    // Никаких скрытых координат: расстояние должно поступать от видимого контакта.
    // Неизвестный стек, смерть цели или невалидный вход оставляют штатный выбор.
    if(!c->enemy_visible || !c->stack_known || !isfinite(c->distance) || c->distance<0 ||
       c->own_health<=0 || c->enemy_health<=0 || c->own_armor<0 || c->enemy_armor<0 ||
       c->own_health>1000 || c->enemy_health>1000 || c->own_armor>1000 || c->enemy_armor>1000){
        out.reason=PSYZ_COMBO_NO_OBSERVATION;return out;
    }
    // Сменить оружие после выстрела недостаточно: нужен подтверждённый недавний hit.
    // Источник этого события обязан быть проверен до подключения к live-движку.
    if(c->last_hit_age_ms<0 || c->last_hit_age_ms>900 ||
       (c->last_hit_weapon!=5 && c->last_hit_weapon!=6 && c->last_hit_weapon!=7)){
        out.reason=PSYZ_COMBO_STALE_HIT;return out;
    }
    int target=Psyz_ComboStack(c->enemy_health,c->enemy_armor);
    int own=Psyz_ComboStack(c->own_health,c->own_armor);
    // Месть перчаткой не означает погоню через всю карту или прыжок под ракету.
    if(c->revenge_active && c->melee_path_clear && c->distance<=64 && target<=50 &&
       c->own_health>=45 && own>target*2 && Psyz_ComboHas(c,1,0)){
        out.weapon=1;out.reason=PSYZ_COMBO_GAUNTLET_REVENGE;return out;
    }
    // Дальний отход и цель на один rail: не бежим ради искусственной квоты комбо.
    if((!c->closing || c->distance>=600) && c->distance>=350 && target<=80 && Psyz_ComboHas(c,7,1)){
        out.weapon=7;out.reason=PSYZ_COMBO_RAIL_FINISH;return out;
    }
    // LG -> RL только при настоящем сближении и запасе HP для собственного splash.
    if(c->last_hit_weapon==6 && c->closing && c->distance>=96 && c->distance<=192 &&
       c->own_health>=80 && target<=160 && Psyz_ComboHas(c,5,1)){
        out.weapon=5;out.reason=PSYZ_COMBO_ROCKET_CLOSE;return out;
    }
    // Средняя дистанция: LG с реальным боезапасом, а не обязательный shotgun.
    int cells=(target+5)/6+2;
    if(c->distance>96 && c->distance<=768 && target<=160 && Psyz_ComboHas(c,6,cells)){
        out.weapon=6;out.reason=PSYZ_COMBO_LG_FINISH;return out;
    }
    // У самого соперника избегаем self-rocket. SG остаётся редким добиванием.
    if(c->distance<96 && target<=55 && Psyz_ComboHas(c,3,1)){
        out.weapon=3;out.reason=PSYZ_COMBO_SHOTGUN_CLOSE;return out;
    }
    return out;
}
#endif
