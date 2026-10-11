/* Bounded opening overlay. No aim or enemy-position access. */
#include "psyz_opening_bank.h"
static int psyz_opening_seen,psyz_opening_playing,psyz_opening_since;
static int psyz_opening_plan=-1,psyz_opening_step,psyz_opening_active;
static void Psyz_OpeningReset(void) {
    psyz_opening_seen=psyz_opening_playing=psyz_opening_since=0;
    psyz_opening_plan=-1;psyz_opening_step=psyz_opening_active=0;
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
    if(recovering){Psyz_OpeningEnd(now,"recovery");return -1;}
    if(psyz_opening_plan<0){
        float best=193;
        for(size_t i=0;i<PSYZ_OPENING_COUNT;i++){
            const PsyzOpeningPlan *p=&psyz_openings[i];
            float d=Psyz_Distance(own->client->ps.origin,p->start);
            if(d<best){best=d;psyz_opening_plan=(int)i;}
        }
        if(psyz_opening_plan<0){Psyz_OpeningEnd(now,"no_nearby_demo");return -1;}
        fprintf(stderr,"PSYZ_OPENING_PLAN t=%d plan=%d distance=%.2f\n",now,psyz_opening_plan,best);
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
    Psyz_OpeningEnd(now,"no_valid_goal");return -1;
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
