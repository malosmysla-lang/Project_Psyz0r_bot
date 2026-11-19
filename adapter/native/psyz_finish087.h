/* Retail bridge: independently enabled, test ports only, no global/shared target. */
#include "psyz_finish087_policy.h"
typedef struct {int target,time,health,armor,weapon,angles[2],revenge_until,logged;float distance;
    int pending_weapon,pending_until,pending_ack,pending_target,last_contact_time;} PsyzFinish087State;
static PsyzFinish087State psyz_finish087[64];
static int Psyz_Finish087Enabled(void){
    cvar_t *p=Cvar_FindVar("net_port"),*t=Cvar_FindVar("qlx_psyzTestInstance"),*e=Cvar_FindVar("qlx_psyzFinish087");
    return p && (p->integer==27961 || p->integer==27962) && t && t->integer==1 && e && e->integer==1;
}
static void Psyz_Finish087Reset(void){memset(psyz_finish087,0,sizeof(psyz_finish087));}
static int Psyz_FinishV2Enabled(void){cvar_t *v=Cvar_FindVar("qlx_psyzV2");return Psyz_Finish087Enabled() && v && v->integer==1;}
static void Psyz_Finish087Hit(gentity_t *victim,gentity_t *attacker,int before,int mod){
    if(!Psyz_Finish087Enabled() || !victim || !attacker || !victim->client || !attacker->client || before<=victim->health)return;
    int a=attacker->s.number,v=victim->s.number;if(a<0 || a>=64 || v<0 || v>=64 || a==v)return;
    int now=attacker->client->pers.cmd.serverTime;
    if(Psyz_IsOurBot(victim) && mod==MOD_GAUNTLET)psyz_finish087[v].revenge_until=now+15000;
    if(victim->health<=0){psyz_finish087[v].time=0;psyz_finish087[a].time=0;psyz_finish087[v].pending_weapon=psyz_finish087[a].pending_weapon=0;return;}
    if(!Psyz_IsOurBot(attacker) || (mod!=MOD_LIGHTNING && mod!=MOD_RAILGUN && mod!=MOD_GAUNTLET))return;
    PsyzFinish087State *s=&psyz_finish087[a];
    if(s->pending_weapon && s->pending_target!=v)s->pending_weapon=0;
    s->target=v;s->time=now;s->health=victim->health;s->armor=victim->client->ps.stats[STAT_ARMOR];
    s->last_contact_time=now;
    s->weapon=mod==MOD_LIGHTNING?6:mod==MOD_RAILGUN?7:1;
    s->distance=Psyz_Distance(attacker->client->ps.origin,victim->client->ps.origin);
    for(int k=0;k<2;k++)s->angles[k]=attacker->client->pers.cmd.angles[k];
}
static void Psyz_Finish087Command(gentity_t *own){
    if(!Psyz_Finish087Enabled() || !Psyz_IsOurBot(own) || own->s.number<0 || own->s.number>=64)return;
    PsyzFinish087State *s=&psyz_finish087[own->s.number];
    if(!own->client || own->health<=0){memset(s,0,sizeof(*s));return;}
    usercmd_t *cmd=&own->client->pers.cmd;playerState_t *ps=&own->client->ps;int now=cmd->serverTime;
    int v2=Psyz_FinishV2Enabled();
    if(v2 && s->last_contact_time>0 && now>=s->last_contact_time && now-s->last_contact_time<=700 && (cmd->buttons&1)){
        float turn=0;for(int k=0;k<2;k++){int d=(cmd->angles[k]-s->angles[k])&65535;if(d>32767)d-=65536;float f=fabsf(d*360.f/65536.f);if(f>turn)turn=f;}
        int guns=0;for(int w=5;w<=7;w++)if((ps->stats[STAT_WEAPONS]&(1<<w)) && ps->ammo[w]>=(w==6?40:3))guns++;
        int own_stack=own->health+ps->stats[STAT_ARMOR],enemy_stack=s->health+s->armor;
        if(turn<=12 && (own->health<100 || ps->stats[STAT_ARMOR]<100 || guns<2 || own_stack<enemy_stack) && cmd->forwardmove>32)
            cmd->forwardmove=32;
    }
    if(v2 && s->pending_weapon){
        int w=s->pending_weapon;
        if(now>s->pending_until || now<s->pending_until-2500 || !(ps->stats[STAT_WEAPONS]&(1<<w)) || (w!=1 && ps->ammo[w]<=0))s->pending_weapon=0;
        else{
            if(ps->weapon==w && !s->pending_ack){s->pending_ack=now;fprintf(stderr,"PSYZ_V2_WEAPON_ACK slot=%d t=%d weapon=%d\n",own->s.number,now,w);}
            if(s->pending_ack && now-s->pending_ack>500)s->pending_weapon=0;
            else{cmd->weapon=(unsigned char)w;return;}
        }
    }
    if(!v2)s->pending_weapon=0;
    if(!s->time)return;
    float turn=0;
    for(int k=0;k<2;k++){int d=(cmd->angles[k]-s->angles[k])&65535;if(d>32767)d-=65536;float f=fabsf(d*360.f/65536.f);if(f>turn)turn=f;}
    PsyzFinish087Input c={ps->weapon,ps->stats[STAT_WEAPONS],ps->ammo,own->health,ps->stats[STAT_ARMOR],s->health,s->armor,now-s->time,cmd->buttons&1,s->weapon,now<s->revenge_until,s->distance,turn};
    PsyzFinish087Choice choice=v2?Psyz_FinishV2Choose(&c):Psyz_Finish087Choose(&c);
    if(choice.weapon!=ps->weapon && choice.reason){
        cmd->weapon=(unsigned char)choice.weapon;
        if(v2){int budget=ps->weaponTime+600;if(budget<800)budget=800;if(budget>2200)budget=2200;
            s->pending_weapon=choice.weapon;s->pending_until=now+budget;s->pending_ack=0;s->pending_target=s->target;
            fprintf(stderr,"PSYZ_V2_WEAPON_REQUEST slot=%d t=%d from=%d to=%d cooldown=%d hold_until=%d\n",own->s.number,now,ps->weapon,choice.weapon,ps->weaponTime,s->pending_until);}
        if(now-s->logged>250){s->logged=now;fprintf(stderr,"PSYZ_FINISH087 slot=%d target=%d t=%d from=%d to=%d reason=%d range=%.1f age=%d\n",own->s.number,s->target,now,ps->weapon,choice.weapon,choice.reason,s->distance,c.age_ms);}
        /* One request per contact: no long weapon hold or override of stock movement. */
        s->time=0;
    }
}
