/* Retail bridge: independently enabled, test ports only, no global/shared target. */
#include "psyz_finish087_policy.h"
typedef struct {int target,time,health,armor,weapon,angles[2],revenge_until,logged;float distance;} PsyzFinish087State;
static PsyzFinish087State psyz_finish087[64];
static int Psyz_Finish087Enabled(void){
    cvar_t *p=Cvar_FindVar("net_port"),*t=Cvar_FindVar("qlx_psyzTestInstance"),*e=Cvar_FindVar("qlx_psyzFinish087");
    return p && (p->integer==27961 || p->integer==27962) && t && t->integer==1 && e && e->integer==1;
}
static void Psyz_Finish087Reset(void){memset(psyz_finish087,0,sizeof(psyz_finish087));}
static void Psyz_Finish087Hit(gentity_t *victim,gentity_t *attacker,int before,int mod){
    if(!Psyz_Finish087Enabled() || !victim || !attacker || !victim->client || !attacker->client || before<=victim->health)return;
    int a=attacker->s.number,v=victim->s.number;if(a<0 || a>=64 || v<0 || v>=64 || a==v)return;
    int now=attacker->client->pers.cmd.serverTime;
    if(Psyz_IsOurBot(victim) && mod==MOD_GAUNTLET)psyz_finish087[v].revenge_until=now+15000;
    if(victim->health<=0){psyz_finish087[v].time=0;psyz_finish087[a].time=0;return;}
    if(!Psyz_IsOurBot(attacker) || (mod!=MOD_LIGHTNING && mod!=MOD_RAILGUN && mod!=MOD_GAUNTLET))return;
    PsyzFinish087State *s=&psyz_finish087[a];
    s->target=v;s->time=now;s->health=victim->health;s->armor=victim->client->ps.stats[STAT_ARMOR];
    s->weapon=mod==MOD_LIGHTNING?6:mod==MOD_RAILGUN?7:1;
    s->distance=Psyz_Distance(attacker->client->ps.origin,victim->client->ps.origin);
    for(int k=0;k<2;k++)s->angles[k]=attacker->client->pers.cmd.angles[k];
}
static void Psyz_Finish087Command(gentity_t *own){
    if(!Psyz_Finish087Enabled() || !Psyz_IsOurBot(own) || own->s.number<0 || own->s.number>=64)return;
    PsyzFinish087State *s=&psyz_finish087[own->s.number];
    if(!own->client || own->health<=0){memset(s,0,sizeof(*s));return;}
    usercmd_t *cmd=&own->client->pers.cmd;playerState_t *ps=&own->client->ps;int now=cmd->serverTime;
    if(!s->time)return;
    float turn=0;
    for(int k=0;k<2;k++){int d=(cmd->angles[k]-s->angles[k])&65535;if(d>32767)d-=65536;float f=fabsf(d*360.f/65536.f);if(f>turn)turn=f;}
    PsyzFinish087Input c={ps->weapon,ps->stats[STAT_WEAPONS],ps->ammo,own->health,ps->stats[STAT_ARMOR],s->health,s->armor,now-s->time,cmd->buttons&1,s->weapon,now<s->revenge_until,s->distance,turn};
    PsyzFinish087Choice choice=Psyz_Finish087Choose(&c);
    if(choice.weapon!=ps->weapon && choice.reason){
        cmd->weapon=(unsigned char)choice.weapon;
        if(now-s->logged>250){s->logged=now;fprintf(stderr,"PSYZ_FINISH087 slot=%d target=%d t=%d from=%d to=%d reason=%d range=%.1f age=%d\n",own->s.number,s->target,now,ps->weapon,choice.weapon,choice.reason,s->distance,c.age_ms);}
        /* One request per contact: no long weapon hold or override of stock movement. */
        s->time=0;
    }
}
