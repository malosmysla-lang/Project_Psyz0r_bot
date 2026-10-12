/* Bounded opening overlay. No aim or enemy-position access. */
#include "psyz_opening_bank.h"
static int psyz_opening_seen,psyz_opening_playing,psyz_opening_since;
static int psyz_opening_plan=-1,psyz_opening_step,psyz_opening_active;
static float psyz_opening_start[3];
static void Psyz_OpeningReset(void) {
    psyz_opening_seen=psyz_opening_playing=psyz_opening_since=0;
    psyz_opening_plan=-1;psyz_opening_step=psyz_opening_active=0;
    memset(psyz_opening_start,0,sizeof(psyz_opening_start));
}
static void Psyz_OpeningEnd(int now,const char *reason) {
    if(psyz_opening_active)fprintf(stderr,"PSYZ_OPENING_END t=%d plan=%d step=%d reason=%s\n",now,psyz_opening_plan,psyz_opening_step,reason);
    psyz_opening_active=0;
}
static void Psyz_OpeningTick(gentity_t *own) {
    int now=own->client->pers.cmd.serverTime;
    cvar_t *phase=Cvar_FindVar("g_gameState"),*enabled=Cvar_FindVar("qlx_psyzOpening");
    if(!phase || !enabled || !enabled->integer){Psyz_OpeningEnd(now,"disabled_or_no_phase");return;}
    int playing=!strcmp(phase->string,"IN_PROGRESS");
    if(psyz_opening_seen && playing && !psyz_opening_playing){
        psyz_opening_since=now;psyz_opening_active=1;psyz_opening_plan=-1;psyz_opening_step=0;
        memcpy(psyz_opening_start,own->client->ps.origin,sizeof(psyz_opening_start));
        fprintf(stderr,"PSYZ_OPENING_BEGIN t=%d\n",now);
        /* Warmup targets must not survive the duel restart. */
        psyz_goal_target=psyz_active_route=psyz_rj_plan=-1;
    }
    psyz_opening_seen=1;psyz_opening_playing=playing;
    if(!playing)Psyz_OpeningEnd(now,"not_in_progress");
    else if(own->health<=0)Psyz_OpeningEnd(now,"death");
    else if(now-psyz_opening_since>=30000)Psyz_OpeningEnd(now,"time_limit");
}
static int Psyz_OpeningTarget(gentity_t *own,int recovering) {
    int now=own->client->pers.cmd.serverTime;
    if(!psyz_opening_active)return -1;
    if(recovering && (own->health<70 || (own->health<100 && own->client->ps.stats[STAT_ARMOR]<30))){Psyz_OpeningEnd(now,"emergency_recovery");return -1;}
    if(psyz_opening_plan<0){
        float best=1e9f;int nearby=0;
        for(size_t i=0;i<PSYZ_OPENING_COUNT;i++){
            const PsyzOpeningPlan *p=&psyz_openings[i];
            float d=Psyz_Distance(psyz_opening_start,p->start);if(d>=193)continue;nearby++;
            int main_weapon=0;
            for(int s=0;s<p->count;s++)if(!strcmp(p->steps[s].classname,"weapon_lightning") ||
                !strcmp(p->steps[s].classname,"weapon_rocketlauncher") || !strcmp(p->steps[s].classname,"weapon_railgun"))main_weapon=1;
            if(!main_weapon)continue;
            int valid=1;
            for(int s=0;s<p->count;s++){
                int found=0;
                for(int n=0;n<1024;n++){
                    gentity_t *e=&g_entities[n];
                    if(psyz_goal_known[n] && e->inuse && e->item && e->item->classname &&
                       !strcmp(e->item->classname,p->steps[s].classname) && Psyz_Distance(e->r.currentOrigin,p->steps[s].position)<16){found=1;break;}
                }
                if(!found){valid=0;break;}
            }
            if(!valid)continue;
            const char *first=p->steps[0].classname;
            float cost=d+Psyz_Distance(psyz_opening_start,p->steps[0].position)*.05f;
            if(strcmp(first,"weapon_lightning") && strcmp(first,"weapon_rocketlauncher") && strcmp(first,"weapon_railgun"))cost+=80;
            if(cost<best){best=cost;psyz_opening_plan=(int)i;}
        }
        if(psyz_opening_plan<0){
            if(nearby && now-psyz_opening_since<2000)return -1;
            Psyz_OpeningEnd(now,nearby?"registry_not_ready":"no_nearby_demo");return -1;
        }
        fprintf(stderr,"PSYZ_OPENING_PLAN t=%d plan=%d selection_cost=%.2f latched_start=1\n",now,psyz_opening_plan,best);
    }
    const PsyzOpeningPlan *p=&psyz_openings[psyz_opening_plan];
    if(psyz_opening_step>=p->count){Psyz_OpeningEnd(now,"completed_pickups");return -1;}
    const PsyzOpeningStep *step=&p->steps[psyz_opening_step];
    for(int i=0;i<1024;i++){
        gentity_t *e=&g_entities[i];
        if(!psyz_goal_known[i] || !e->inuse || !e->item || !e->item->classname)continue;
        if(strcmp(e->item->classname,step->classname) || Psyz_Distance(e->r.currentOrigin,step->position)>16)continue;
        if(!e->r.contents || psyz_banned[i]>now || Psyz_Distance(own->client->ps.origin,e->r.currentOrigin)>1100){
            Psyz_OpeningEnd(now,"unavailable_or_distant");return -1;
        }
        return i;
    }
    if(now-psyz_opening_since>=2000)Psyz_OpeningEnd(now,"no_valid_goal");return -1;
}
static void Psyz_OpeningPickup(gentity_t *item,int now) {
    if(!psyz_opening_active || psyz_opening_plan<0)return;
    const PsyzOpeningPlan *p=&psyz_openings[psyz_opening_plan];
    if(psyz_opening_step>=p->count)return;
    const PsyzOpeningStep *step=&p->steps[psyz_opening_step];
    if(!strcmp(item->item->classname,step->classname) && Psyz_Distance(item->r.currentOrigin,step->position)<16){
        fprintf(stderr,"PSYZ_OPENING_PICKUP t=%d plan=%d step=%d entity=%d\n",now,psyz_opening_plan,psyz_opening_step,item->s.number);
        psyz_opening_step++;
        if(psyz_opening_step>=p->count)Psyz_OpeningEnd(now,"completed_pickups");
    }
}
