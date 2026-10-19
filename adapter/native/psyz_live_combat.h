/* Retail bridge: observe real damage; never replace damage or steer aim at hidden players. */
#include "psyz_combo_policy.h"
typedef struct {int victim,time,weapon,health,armor;float range;int angles[2];} PsyzHitContact;
static PsyzHitContact psyz_hit_contact;
static int psyz_combo_hold_until,psyz_combo_hold_weapon,psyz_live_combat_log;
static void (*psyz_damage_original)(gentity_t*,gentity_t*,gentity_t*,vec3_t,vec3_t,int,int,int);
static void Psyz_LiveCombatReset(void){memset(&psyz_hit_contact,0,sizeof(psyz_hit_contact));psyz_hit_contact.victim=-1;psyz_combo_hold_until=0;}
static void Psyz_ObserveDamage(gentity_t *target,gentity_t *inflictor,gentity_t *attacker,vec3_t dir,vec3_t point,int damage,int flags,int mod){
    int before=target?target->health:0;
    int armor_before=target && target->client?target->client->ps.stats[STAT_ARMOR]:0;
    psyz_damage_original(target,inflictor,attacker,dir,point,damage,flags,mod);
    if(!Psyz_PreAlphaEnabled() || !Psyz_IsOurBot(attacker) || !target || !target->client || target==attacker)return;
    if(target->health<=0){if(psyz_hit_contact.victim==target->s.number)Psyz_LiveCombatReset();return;}
    // Только прямой LG/RG hit подтверждает контакт на этой линии выстрела.
    // Splash из-за угла никогда не раскрывает координаты цели этому модулю.
    if(before<=target->health || (mod!=MOD_LIGHTNING && mod!=MOD_RAILGUN))return;
    int now=attacker->client->pers.cmd.serverTime;
    int same=psyz_hit_contact.victim==target->s.number && now>=psyz_hit_contact.time && now-psyz_hit_contact.time<=1500;
    int dealt=(before-target->health)+(armor_before-target->client->ps.stats[STAT_ARMOR]);
    // Оставшийся стек — оценка от условного 200, а не чтение скрытого HP/armor.
    // Только реально нанесённый нами урон уменьшает эту оценку; длинный разрыв сбрасывает её.
    int estimate=(same?psyz_hit_contact.health:200)-dealt;
    if(estimate<40)estimate=40;
    psyz_hit_contact.victim=target->s.number;psyz_hit_contact.time=now;
    psyz_hit_contact.weapon=mod==MOD_LIGHTNING?6:7;
    psyz_hit_contact.health=estimate;psyz_hit_contact.armor=0;
    psyz_hit_contact.range=Psyz_Distance(attacker->client->ps.origin,target->client->ps.origin);
    for(int a=0;a<2;a++)psyz_hit_contact.angles[a]=attacker->client->pers.cmd.angles[a];
}
static void Psyz_LiveCombatCommand(gentity_t *own){
    if(!Psyz_PreAlphaEnabled() || own->health<=0){Psyz_LiveCombatReset();return;}
    usercmd_t *cmd=&own->client->pers.cmd;playerState_t *ps=&own->client->ps;int now=cmd->serverTime;
    cvar_t *on=Cvar_FindVar("qlx_psyzComboLive");if(!on || !on->integer)return;
    int age=now-psyz_hit_contact.time;
    if(psyz_hit_contact.victim<0 || age<0 || age>500 || !(cmd->buttons&1))return;
    for(int a=0;a<2;a++){int delta=(cmd->angles[a]-psyz_hit_contact.angles[a])&65535;if(delta>32767)delta-=65536;if(abs(delta)>2185)return;}
    // Недавний hit хранит только дистанцию/стек в момент попадания, не обновляет скрытую позицию.
    int ready=Psyz_TrinityReady(ps->stats[STAT_WEAPONS],ps->ammo);
    int own_stack=Psyz_ComboStack(own->health,ps->stats[STAT_ARMOR]);
    int target_stack=Psyz_ComboStack(psyz_hit_contact.health,psyz_hit_contact.armor);
    if((own->health<65 || (ready<2 && ps->stats[STAT_ARMOR]<40)) && own_stack<target_stack && cmd->forwardmove>32){
        // Не добавляем слепой отход сквозь стену: сохраняем stock-стрейф и огонь, ограничиваем лобовой rush.
        cmd->forwardmove=32;
        if(now-psyz_live_combat_log>1000){psyz_live_combat_log=now;fprintf(stderr,"PSYZ_COMBAT_BRAKE t=%d own=%d target=%d ready=%d source=recent_direct_hit\n",now,own_stack,target_stack,ready);}
    }
    if(now<psyz_combo_hold_until && (ps->stats[STAT_WEAPONS]&(1<<psyz_combo_hold_weapon)) && ps->ammo[psyz_combo_hold_weapon]>0){cmd->weapon=(unsigned char)psyz_combo_hold_weapon;return;}
    if(age>180 || own->health<45)return;
    PsyzComboContext c={ps->weapon,ps->stats[STAT_WEAPONS],ps->ammo,psyz_hit_contact.range,own->health,ps->stats[STAT_ARMOR],psyz_hit_contact.health,psyz_hit_contact.armor,1,1,psyz_hit_contact.weapon,age,cmd->forwardmove>32,0,0};
    PsyzComboChoice choice=Psyz_ComboChoose(&c);
    if(choice.weapon!=ps->weapon && choice.reason>=PSYZ_COMBO_RAIL_FINISH){
        cmd->weapon=(unsigned char)choice.weapon;psyz_combo_hold_weapon=choice.weapon;psyz_combo_hold_until=now+450;
        fprintf(stderr,"PSYZ_COMBO_SWITCH t=%d from=%d to=%d reason=%d range=%.1f estimated_remaining=%d hold=450 source=confirmed_direct_hit\n",now,ps->weapon,choice.weapon,choice.reason,c.distance,target_stack);
    }
}
static void Psyz_InstallDamageObserver(void){
    static const unsigned char expected[]={0x41,0x57,0x41,0x56,0x41,0x55,0x41,0x54,0x55,0x53,0x48,0x89,0xfb};
    if(!G_Damage || memcmp((void*)G_Damage,expected,sizeof(expected))){fprintf(stderr,"PSYZ_DAMAGE_OBSERVER refused ABI\n");return;}
    int result=Hook((void*)G_Damage,Psyz_ObserveDamage,(void*)&psyz_damage_original);
    if(!result)psyz_vm_hook_count++;
    fprintf(stderr,"PSYZ_DAMAGE_OBSERVER install=%d\n",result);
}
