/* Experimental Blood Run prealpha. Uses valid goals produced by stock QL. */
#include <math.h>
#include "psyz_bloodrun_bank.h"
#include "psyz_red_routes.h"
#define PSYZ_ALL_ROUTE_COUNT (PSYZ_ROUTE_COUNT+PSYZ_RED_ROUTE_COUNT)
static const PsyzLearnedRoute *Psyz_Route(size_t i) { return i<PSYZ_ROUTE_COUNT?&psyz_routes[i]:&psyz_red_routes[i-PSYZ_ROUTE_COUNT]; }
#include "psyz_nav_recovery.h"
static PsyzNavRecovery psyz_nav;
static int psyz_nav_health,psyz_nav_damage_time;
static int psyz_combat_until,psyz_diagnostic_time;
static int psyz_combat_log;
static int psyz_aim_log;
/* Smooth angular error, never modify damage, projectiles or registered hits.
   Match accuracy still needs empirical calibration at each distance. */
static float Psyz_AimNoise(unsigned int bucket,unsigned int salt){
    unsigned int x=bucket*747796405u+salt*2891336453u+277803737u;
    x=(x^(x>>16))*2246822519u;x^=x>>13;
    return (float)(x&65535u)/32767.5f-1.f;
}
static void Psyz_HumanizeAim(usercmd_t *cmd,int weapon,int now){
    cvar_t *on=Cvar_FindVar("qlx_psyzAimHumanize");
    cvar_t *all=Cvar_FindVar("qlx_psyzAllWeaponAim");int all_weapons=all && all->integer;
    if(!on || !on->integer || !(cmd->buttons&1) || cmd->weapon!=weapon || weapon<2 || weapon>8 ||
       (!all_weapons && weapon!=6 && weapon!=8))return;
    const float initial[9]={0,0,1.1f,1.5f,3.f,2.5f,1.25f,.45f,3.f};
    cvar_t *amplitude=Cvar_FindVar(weapon==6?"qlx_psyzLGAimError":weapon==8?"qlx_psyzPlasmaAimError":"qlx_psyzOtherAimError");
    float degrees=amplitude?(float)atof(amplitude->string):initial[weapon];
    if(!isfinite(degrees))degrees=initial[weapon];
    if(degrees<0)degrees=0;if(degrees>10)degrees=10;
    if(all_weapons){
        char name[64];snprintf(name,sizeof(name),"qlx_psyzAcc%dBase",weapon);cvar_t *base=Cvar_FindVar(name);
        snprintf(name,sizeof(name),"qlx_psyzAcc%dMin",weapon);cvar_t *low=Cvar_FindVar(name);
        snprintf(name,sizeof(name),"qlx_psyzAcc%dMax",weapon);cvar_t *high=Cvar_FindVar(name);
        float center=base?(float)atof(base->string):0,lo=low?(float)atof(low->string):0,hi=high?(float)atof(high->string):0;
        if(isfinite(center)&&isfinite(lo)&&isfinite(hi)&&lo>0&&center>=lo&&hi>=center&&hi<=100){
            float f=(Psyz_AimNoise((unsigned int)(now/15000),(unsigned int)weapon)+1)*.5f;
            float target=lo+(hi-lo)*f;
            if(psyz_nav_damage_time>0 && now-psyz_nav_damage_time<2000)target=lo;
            degrees*=center/target;
            if(now-psyz_aim_log>=3000){psyz_aim_log=now;fprintf(stderr,"PSYZ_AIM_PROFILE t=%d weapon=%d target=%.2f error_degrees=%.3f calibrated=0\n",now,weapon,target,degrees);}
        }
    }
    unsigned int bucket=(unsigned int)(now/240);float t=(now%240)/240.f;t=t*t*(3-2*t);
    for(int axis=0;axis<2;axis++){
        unsigned int salt=(unsigned int)(weapon*11+axis);
        float error=Psyz_AimNoise(bucket,salt)*(1-t)+Psyz_AimNoise(bucket+1,salt)*t;
        cmd->angles[axis]+=(int)(error*degrees*65536.f/360.f);
    }
}
static unsigned char psyz_goal_cache[1024][64];
static unsigned char psyz_goal_known[1024];
static int psyz_route_banned[PSYZ_ALL_ROUTE_COUNT];
static int psyz_goal_target=-1,psyz_goal_since,psyz_registry_logged;
static int psyz_rj_plan=-1,psyz_active_route=-1,psyz_route_point,psyz_last_move_time;
static float psyz_progress_distance;
static int psyz_strafe_log;
static int psyz_progress_time,psyz_banned[1024];
static int psyz_demo_retry_after[1024];
static int psyz_rj=-1,psyz_rj_phase,psyz_rj_time,psyz_rj_ground,psyz_rj_last,psyz_rj_fired,psyz_rj_landed_at;
static float psyz_rj_start_z;
static int psyz_debug_logged;
static int psyz_registry_retry;
/* Successful VM hooks occupy a contiguous tail of the NOPY trampoline pool. */
static int psyz_vm_hook_count;
static int psyz_last_pickup=-1,psyz_last_pickup_time;

static float Psyz_Distance(const float *a,const float *b) {
    float x=a[0]-b[0],y=a[1]-b[1],z=a[2]-b[2];return sqrtf(x*x+y*y+z*z);
}
static float Psyz_Angle(float a) { while(a>180)a-=360;while(a< -180)a+=360;return a; }
static int Psyz_PreAlphaEnabled(void) {
    cvar_t *v=Cvar_FindVar("qlx_psyzPreAlpha");cvar_t *m=Cvar_FindVar("mapname");
    cvar_t *test=Cvar_FindVar("qlx_psyzTestInstance"),*port=Cvar_FindVar("net_port");
    return test && test->integer==1 && port && port->integer==27961 && v && v->integer==1 && m && !strcmp(m->string,"bloodrun");
}
#include "psyz_opening.h"
static void Psyz_PreAlphaReset(void) {
    Psyz_NavReset(&psyz_nav);psyz_nav_health=psyz_nav_damage_time=0;
    psyz_combat_until=psyz_diagnostic_time=0;
    psyz_combat_log=psyz_aim_log=0;
    Psyz_OpeningReset();
    psyz_debug_logged=0;
    psyz_registry_retry=0;
    memset(psyz_goal_known,0,sizeof(psyz_goal_known));memset(psyz_route_banned,0,sizeof(psyz_route_banned));memset(psyz_banned,0,sizeof(psyz_banned));
    memset(psyz_demo_retry_after,0,sizeof(psyz_demo_retry_after));
    psyz_rj_plan=psyz_goal_target=psyz_active_route=psyz_rj=psyz_last_pickup=-1;

    psyz_registry_logged=psyz_rj_phase=psyz_rj_last=psyz_last_move_time=0;
    psyz_last_pickup_time=psyz_rj_landed_at=psyz_strafe_log=0;
}
static void Psyz_PreAlphaVmReset(void) {
    int seen=psyz_opening_seen,playing=psyz_opening_playing;
    Psyz_PreAlphaReset();
    psyz_opening_seen=seen;psyz_opening_playing=playing;
}
static float Psyz_ItemWeight(gentity_t *item,gentity_t *own,int recovering) {
    const char *c=item->item->classname;int h=own->health,a=own->client->ps.stats[STAT_ARMOR];
    int weapons=own->client->ps.stats[STAT_WEAPONS];
    if(!strcmp(c,"weapon_rocketlauncher"))return (weapons&(1<<5)) && own->client->ps.ammo[5]>0?8:180;
    if(!strcmp(c,"weapon_lightning"))return (weapons&(1<<6)) && own->client->ps.ammo[6]>0?8:150;
    if(!strcmp(c,"weapon_railgun"))return (weapons&(1<<7)) && own->client->ps.ammo[7]>0?8:145;
    if(!strcmp(c,"weapon_shotgun"))return weapons&(1<<3)?6:90;
    if(!strcmp(c,"weapon_plasmagun"))return weapons&(1<<8)?6:75;
    if(!strcmp(c,"weapon_grenadelauncher"))return weapons&(1<<4)?5:50;
    if(!strcmp(c,"item_health_mega"))return h>=190?5:recovering?65:135;
    if(!strcmp(c,"item_armor_body"))return a>=190?4:recovering?55:110;
    if(!strcmp(c,"item_armor_combat"))return a>=150?4:recovering?160:80;
    if(!strncmp(c,"item_health",11))return h>=100?2:recovering?180:120;
    if(!strcmp(c,"item_armor_shard"))return a>=190?1:recovering?35:12;
    if(!strncmp(c,"ammo_",5)){int tag=item->item->giTag;return tag>=0 && tag<16 && own->client->ps.ammo[tag]<20?40:0;}
    return 1;
}
static void Psyz_SelectDemoRoute(gentity_t *own,int target) {
    float best=97;psyz_active_route=-1;psyz_route_point=0;
    if(target>=0 && target<1024 && psyz_demo_retry_after[target]>own->client->pers.cmd.serverTime)return;
    for(size_t i=0;i<PSYZ_ALL_ROUTE_COUNT;i++) {
        const PsyzLearnedRoute *r=Psyz_Route(i);
        cvar_t *red=Cvar_FindVar("qlx_psyzRedRoutes");if(i>=PSYZ_ROUTE_COUNT && (!red || !red->integer))continue;if(psyz_route_banned[i]>own->client->pers.cmd.serverTime)continue;
        if(target<0 || r->count<2 || !g_entities[target].item || strcmp(r->classname,g_entities[target].item->classname) || Psyz_Distance(r->target,g_entities[target].r.currentOrigin)>16)continue;
        float d=Psyz_Distance(own->client->ps.origin,r->points[0].p);
        if(d<best){best=d;psyz_active_route=(int)i;}
    }
    if(psyz_active_route>=0)fprintf(stderr,"PSYZ_DEMO_ROUTE t=%d target=%d route=%d source=demo_bank\n",own->client->pers.cmd.serverTime,target,psyz_active_route);
}
static void Psyz_PreAlphaGoal(void *state,int travel_flags,void *output) {
    (void)travel_flags;if(!g_entities)return;
    int client;memcpy(&client,(char*)state+8,4);
    if(client!=0 || !g_entities[0].client || !(g_entities[0].r.svFlags&8))return;
    gentity_t *own=&g_entities[0];int now=own->client->pers.cmd.serverTime;
    unsigned char raw[64];memcpy(raw,output,64);
    int entity,area,raw_flags;memcpy(&raw_flags,raw+48,4);float pos[3];memcpy(pos,raw,12);memcpy(&area,raw+12,4);memcpy(&entity,raw+40,4);
    if(raw_flags==1 && entity>=0 && entity<1024 && area>0 && area<2393 && g_entities[entity].inuse && g_entities[entity].item &&
       Psyz_Distance(pos,g_entities[entity].r.currentOrigin)<64) {
        memcpy(psyz_goal_cache[entity],raw,64);psyz_goal_known[entity]=1;
    }
    if(!psyz_registry_logged) {
        psyz_registry_logged=1;
        for(int i=0;i<1024;i++) {
            gentity_t *e=&g_entities[i];if(!e->inuse||!e->item||!e->item->classname)continue;
            fprintf(stderr,"PSYZ_ITEM entity=%d class=%s pos=%.3f,%.3f,%.3f contents=%d next=%d model=%d\n",i,e->item->classname,e->r.currentOrigin[0],e->r.currentOrigin[1],e->r.currentOrigin[2],e->r.contents,e->nextthink,e->s.modelindex);
        }
    }
    if(!Psyz_PreAlphaEnabled())return;
    Psyz_OpeningTick(own);
    if(!psyz_debug_logged || now-psyz_registry_retry>=1000){
        psyz_registry_retry=now;
        psyz_debug_logged=1;void *im;memcpy(&im,(char*)qagame+0x2d8000,sizeof(im));
        int (*get_item)(int,const char*,void*);memcpy(&get_item,(char*)im+0x4d0,sizeof(get_item));
        int count=0;
        for(int n=0;n<1024;n++){
            gentity_t *e=&g_entities[n];if(psyz_goal_known[n] || !e->inuse || !e->item || !e->item->pickup_name)continue;
            unsigned char candidate[256];int cursor=-1;
            for(int j=0;j<64;j++){
                memset(candidate,0,sizeof(candidate));int next=get_item(cursor,e->item->pickup_name,candidate);
                if(next<0 || next==cursor)break;
                cursor=next;
                int id,area,flags;float p[3];memcpy(p,candidate,12);memcpy(&area,candidate+12,4);memcpy(&id,candidate+40,4);memcpy(&flags,candidate+48,4);
                if(id==n && area>0 && area<2393 && flags==1 && Psyz_Distance(p,e->r.currentOrigin)<64){memcpy(psyz_goal_cache[n],candidate,64);psyz_goal_known[n]=1;count++;break;}
            }
        }
        if(count)fprintf(stderr,"PSYZ_GOAL_REGISTRY newly_valid_item_goals=%d weapons=%d ammo_rl=%d\n",count,own->client->ps.stats[STAT_WEAPONS],own->client->ps.ammo[5]);
    }
    int recovering=own->health<70 || (own->health<100 && own->client->ps.stats[STAT_ARMOR]<30);
    // Only exact enemy HP/armor are read, never hidden enemy coordinates.
    for(int i=1;i<64;i++) {
        gentity_t *e=&g_entities[i];if(!e->inuse||!e->client||(e->r.svFlags&8)||e->health<=0)continue;
        float ours=own->health+fminf(own->client->ps.stats[STAT_ARMOR],2*own->health);
        float theirs=e->health+fminf(e->client->ps.stats[STAT_ARMOR],2*e->health);
        if(theirs>ours*1.15f)recovering=1;
    }
    int was_opening=psyz_opening_active;
    int opening_target=Psyz_OpeningTarget(own,recovering);
    if(was_opening && !psyz_opening_active){psyz_goal_target=-1;psyz_active_route=-1;}
    cvar_t *nav=Cvar_FindVar("qlx_psyzNavRecovery");
    int nav_hold=nav && nav->integer && !recovering && psyz_nav.target==psyz_goal_target &&
        now-psyz_nav.start<30000;
    int keep=opening_target<0 && psyz_goal_target>=0 && psyz_goal_known[psyz_goal_target] &&
        g_entities[psyz_goal_target].r.contents &&
        Psyz_ItemWeight(&g_entities[psyz_goal_target],own,recovering)>15 &&
        (now-psyz_goal_since<3000 || nav_hold);
    /* A nearby needed main weapon may interrupt a long resource route.
       Use only registered available goals; do not fabricate a path. */
    int nearby_main=-1;float nearby_best=192;
    for(int i=0;i<1024;i++){
        gentity_t *e=&g_entities[i];if(!psyz_goal_known[i] || psyz_banned[i]>now || !e->inuse || !e->item || !e->r.contents)continue;
        const char *c=e->item->classname;
        if(strcmp(c,"weapon_rocketlauncher") && strcmp(c,"weapon_lightning") && strcmp(c,"weapon_railgun"))continue;
        if(Psyz_ItemWeight(e,own,recovering)<140)continue;
        float d=Psyz_Distance(own->client->ps.origin,e->r.currentOrigin);
        if(d<nearby_best){nearby_best=d;nearby_main=i;}
    }
    if(nearby_main>=0 && !recovering && opening_target<0 && nearby_main!=psyz_goal_target)keep=0;
    if(!keep) {
        float best=-1;int selected=-1;
        for(int i=0;i<1024;i++) {
            if(!psyz_goal_known[i] || psyz_banned[i]>now)continue;
            gentity_t *e=&g_entities[i];if(!e->inuse||!e->item||!e->item->classname)continue;
            float weight=Psyz_ItemWeight(e,own,recovering);if(weight<=0)continue;
            float wait=e->r.contents?0:fmaxf(0,(e->nextthink-now)/1000.f);
            if(!e->r.contents && (e->nextthink<=now || wait>3))continue;
            float distance=Psyz_Distance(own->client->ps.origin,e->r.currentOrigin);
            float score=weight-distance*.035f-wait*15;
            if(score>best){best=score;selected=i;}
        }
        if(nearby_main>=0 && !recovering && opening_target<0)selected=nearby_main;
        if(opening_target>=0)selected=opening_target;
        if(selected!=psyz_goal_target) {
            psyz_goal_target=selected;psyz_goal_since=now;psyz_progress_time=now;
            psyz_progress_distance=selected>=0?Psyz_Distance(own->client->ps.origin,g_entities[selected].r.currentOrigin):0;
            Psyz_SelectDemoRoute(own,selected);
            fprintf(stderr,"PSYZ_TARGET t=%d entity=%d recover=%d stock_original=%d known_only=1\n",now,selected,recovering,entity);
        }
    }
    cvar_t *probe=Cvar_FindVar("qlx_psyzRJProbe");
    int probe_jump=probe && probe->integer>0 && probe->integer<=(int)PSYZ_JUMP_COUNT?probe->integer-1:-1;
    if(probe_jump>=0){
        float best=160;int target=-1;
        for(int i=0;i<1024;i++)if(psyz_goal_known[i] && g_entities[i].inuse && g_entities[i].item){
            float d=Psyz_Distance(g_entities[i].r.currentOrigin,psyz_jumps[probe_jump].landing);if(d<best){best=d;target=i;}
        }
        if(target>=0){psyz_goal_target=target;psyz_progress_time=now;}
    }
    cvar_t *diagnostics=Cvar_FindVar("qlx_psyzItemDiagnostics");
    if(diagnostics && diagnostics->integer && now-psyz_diagnostic_time>=2000){
        psyz_diagnostic_time=now;
        int ready=0;for(int w=5;w<=7;w++)if((own->client->ps.stats[STAT_WEAPONS]&(1<<w)) && own->client->ps.ammo[w]>0)ready++;
        fprintf(stderr,"PSYZ_LOADOUT t=%d trinity_ready=%d rl_ammo=%d lg_ammo=%d rg_ammo=%d target=%d\n",now,ready,own->client->ps.ammo[5],own->client->ps.ammo[6],own->client->ps.ammo[7],psyz_goal_target);
        for(int i=0;i<1024;i++){
            gentity_t *e=&g_entities[i];if(!e->inuse || !e->item)continue;
            float d=Psyz_Distance(own->client->ps.origin,e->r.currentOrigin);if(d>192)continue;
            float w=Psyz_ItemWeight(e,own,recovering);
            const char *reason=i==psyz_goal_target?"selected":!e->r.contents?"unavailable":!psyz_goal_known[i]?"no_aas_goal":psyz_banned[i]>now?"temporarily_banned":w<=15?"low_need":"other_goal_retained_or_ranked_higher";
            fprintf(stderr,"PSYZ_NEAR_ITEM t=%d entity=%d class=%s distance=%.1f available=%d known=%d weight=%.1f target=%d reason=%s\n",now,i,e->item->classname,d,e->r.contents!=0,psyz_goal_known[i]!=0,w,psyz_goal_target,reason);
        }
    }
    if(psyz_goal_target<0)return;
    float distance=Psyz_Distance(own->client->ps.origin,g_entities[psyz_goal_target].r.currentOrigin);
    if(distance<psyz_progress_distance-32){psyz_progress_distance=distance;psyz_progress_time=now;}
    int nav_action=0;
    if(nav && nav->integer){
        gentity_t *target=&g_entities[psyz_goal_target];
        int waiting=!target->r.contents && target->nextthink>now && target->nextthink-now<=3000;
        int combat=(own->client->pers.cmd.buttons&1) || (psyz_nav_damage_time>0 && now-psyz_nav_damage_time<1000);
        nav_action=Psyz_NavUpdate(&psyz_nav,psyz_goal_target,now,own->client->ps.origin,distance,
                    psyz_active_route>=0?psyz_route_point:-1,psyz_active_route>=0,combat,waiting);
    }
    if((nav && nav->integer)?nav_action!=0:now-psyz_progress_time>6000) {
        if(nav && nav->integer)fprintf(stderr,"PSYZ_NAV_RECOVERY t=%d target=%d action=%d elapsed=%d paused=%d visited=%d waypoint=%d\n",now,psyz_goal_target,nav_action,now-psyz_nav.start,psyz_nav.paused,psyz_nav.cell_count,psyz_nav.waypoint);
        if(psyz_active_route>=0 && (!nav || !nav->integer || nav_action==1)){
            fprintf(stderr,"PSYZ_REPATH t=%d target=%d route=%d reason=demo_failed_fallback_aas\n",now,psyz_goal_target,psyz_active_route);
            psyz_route_banned[psyz_active_route]=now+60000;
            psyz_demo_retry_after[psyz_goal_target]=now+15000;
            psyz_active_route=-1;psyz_progress_time=now;psyz_progress_distance=distance;
        } else {
        Psyz_OpeningEnd(now,"no_progress");
        fprintf(stderr,"PSYZ_REPATH t=%d target=%d route=%d reason=no_progress\n",now,psyz_goal_target,psyz_active_route);
        if(psyz_active_route>=0)psyz_route_banned[psyz_active_route]=now+60000;
        psyz_banned[psyz_goal_target]=now+8000;psyz_goal_target=-1;psyz_active_route=-1;
        int gs;memcpy(&gs,(char*)state+0x1968,4);void *imports;memcpy(&imports,(char*)qagame+0x2d8000,sizeof(imports));
        void (*pop)(int);memcpy(&pop,(char*)imports+0x468,sizeof(pop));pop(gs);
        float expired=0;memcpy((char*)state+0x179c,&expired,4);return;
        }
    }
    memcpy(output,psyz_goal_cache[psyz_goal_target],64);
    if(psyz_active_route<0)Psyz_SelectDemoRoute(own,psyz_goal_target);
    if(psyz_active_route>=0) {
        const PsyzLearnedRoute *r=Psyz_Route((size_t)psyz_active_route);
        while(psyz_route_point<r->count && Psyz_Distance(own->client->ps.origin,r->points[psyz_route_point].p)<48)psyz_route_point++;
        if(psyz_route_point<r->count-1) {
            const PsyzRoutePoint *p=&r->points[psyz_route_point];int flags=0;
            memcpy(output,p->p,12);memcpy((char*)output+12,&p->area,4);memcpy((char*)output+48,&flags,4);
        } else psyz_active_route=-1;
    }
    psyz_rj_plan=-1;
    if(psyz_rj<0 && now-psyz_rj_last>15000 && (own->client->ps.stats[STAT_WEAPONS]&(1<<5)) && own->client->ps.ammo[5]>0){
        float best=probe_jump>=0?100000:256;
        for(size_t j=0;j<PSYZ_JUMP_COUNT;j++){
            if(probe_jump>=0 && j!=(size_t)probe_jump)continue;
            if(probe_jump<0 && j!=0)continue; /* Sample 0 passed three live repetitions. */
            const PsyzLearnedJump *r=&psyz_jumps[j];float d=Psyz_Distance(own->client->ps.origin,r->start);
            if(r->start_area>0 && d<best && own->health>r->health_cost+50 && Psyz_Distance(g_entities[psyz_goal_target].r.currentOrigin,r->landing)<160){best=d;psyz_rj_plan=(int)j;}
        }
        if(psyz_rj_plan>=0){const PsyzLearnedJump *r=&psyz_jumps[psyz_rj_plan];int flags=0;memcpy(output,r->start,12);memcpy((char*)output+12,&r->start_area,4);memcpy((char*)output+48,&flags,4);psyz_active_route=-1;}
    }
    /* Keep botlib's top goal consistent with the goal passed to its mover.
       Slots verified from this SHA-pinned qagame call sites. */
    int goal_state;memcpy(&goal_state,(char*)state+0x1968,4);
    void *imports;memcpy(&imports,(char*)qagame+0x2d8000,sizeof(imports));
    void (*pop_goal)(int);void (*push_goal)(int,void*);
    memcpy(&pop_goal,(char*)imports+0x468,sizeof(pop_goal));
    memcpy(&push_goal,(char*)imports+0x460,sizeof(push_goal));
    pop_goal(goal_state);push_goal(goal_state,output);
}
static void Psyz_PreAlphaMove(gentity_t *own) {
    if(!Psyz_PreAlphaEnabled())return;
    usercmd_t *cmd=&own->client->pers.cmd;playerState_t *ps=&own->client->ps;int now=cmd->serverTime;
    if(now<psyz_last_move_time)Psyz_PreAlphaReset();
    if(psyz_nav_health-own->health>1)psyz_nav_damage_time=now;
    psyz_nav_health=own->health;
    Psyz_OpeningTick(own);
    int dt=now-psyz_last_move_time;psyz_last_move_time=now;
    if(dt<=0 || dt>100 || own->health<=0){psyz_rj=-1;return;}
    // Never inherit habitual crouching. Agreed exceptions are not enabled yet.
    if(cmd->upmove<0)cmd->upmove=0;
    Psyz_HumanizeAim(cmd,ps->weapon,now);
    cvar_t *ground_combat=Cvar_FindVar("qlx_psyzGroundCombat");
    if(ground_combat && ground_combat->integer){
        int triggered=(cmd->buttons&1) || (psyz_nav_damage_time>0 && now-psyz_nav_damage_time<1000);
        if(triggered && psyz_rj<0)psyz_combat_until=now+1200;
        if(now<psyz_combat_until && psyz_rj<0){
            /* Preserve stock ground strafes and existing flight; block new jumps
               and route/RJ steering for the whole observed combat episode. */
            if(ps->groundEntityNum!=1023 && cmd->upmove>0){
                cmd->upmove=0;
                if(now-psyz_combat_log>=500){psyz_combat_log=now;fprintf(stderr,"PSYZ_COMBAT_GROUND t=%d weapon=%d until=%d jump_suppressed=1\n",now,ps->weapon,psyz_combat_until);}
            }
            return;
        }
    }
    if(psyz_rj_plan>=0)cmd->weapon=5;
    if(psyz_goal_target>=0 && psyz_rj<0 && now-psyz_rj_last>15000 && !(cmd->buttons&1) &&
       (ps->stats[STAT_WEAPONS]&(1<<5)) && ps->ammo[5]>0) {
        for(size_t j=0;j<PSYZ_JUMP_COUNT;j++) {
            if(psyz_rj_plan>=0 && j!=(size_t)psyz_rj_plan)continue;
            if(psyz_rj_plan<0 && j!=0)continue;
            const PsyzLearnedJump *r=&psyz_jumps[j];
            if(Psyz_Distance(ps->origin,r->start)<40 && Psyz_Distance(g_entities[psyz_goal_target].r.currentOrigin,r->landing)<160 &&
               own->health>r->health_cost+50 && ps->groundEntityNum!=1023) {
                psyz_rj=(int)j;psyz_rj_phase=0;psyz_rj_time=now;psyz_rj_start_z=ps->origin[2];psyz_rj_ground=0;psyz_rj_fired=0;
                fprintf(stderr,"PSYZ_RJ_BEGIN t=%d sample=%d target=%d health=%d\n",now,psyz_rj,psyz_goal_target,own->health);break;
            }
        }
    }
    if(psyz_rj>=0) {
        const PsyzLearnedJump *r=&psyz_jumps[psyz_rj];int elapsed=now-psyz_rj_time;
        if(elapsed>3000 && psyz_rj_phase!=2){fprintf(stderr,"PSYZ_RJ_END t=%d outcome=timeout\n",now);psyz_rj=-1;psyz_rj_last=now;return;}
        if(psyz_rj_phase==2){
            int pickup=psyz_last_pickup_time>=psyz_rj_time && psyz_last_pickup_time<=psyz_rj_landed_at+1500;
            if(pickup || now-psyz_rj_landed_at>=1500){fprintf(stderr,"PSYZ_RJ_END t=%d sample=%d higher=0 pickup=%d reconstructed_input=1\n",now,psyz_rj,pickup);psyz_rj=-1;psyz_rj_last=now;}
            return;
        }
        cmd->weapon=5;
        if(psyz_rj_phase==0) {
            cmd->forwardmove=cmd->rightmove=cmd->upmove=0;cmd->buttons&=~1;
            if(Psyz_Distance(ps->origin,r->start)>90){psyz_rj=-1;psyz_rj_last=now;return;}
            if(ps->weapon!=5 || ps->weaponTime>0 || hypotf(ps->velocity[0],ps->velocity[1])>30)return;
            psyz_rj_phase=3;
        }
        if(psyz_rj_phase==3){
            float heading=atan2f(r->landing[1]-ps->origin[1],r->landing[0]-ps->origin[0])*57.2957795f;
            cmd->angles[0]=-ps->delta_angles[0];cmd->angles[1]=(int)(heading*65536.f/360.f)-ps->delta_angles[1];
            cmd->forwardmove=127;cmd->rightmove=cmd->upmove=0;cmd->buttons&=~1;
            if(ps->groundEntityNum==1023 || Psyz_Distance(ps->origin,r->start)>100){psyz_rj=-1;psyz_rj_last=now;return;}
            if(hypotf(ps->velocity[0],ps->velocity[1])<300)return;
            psyz_rj_time=now;psyz_rj_start_z=ps->origin[2];psyz_rj_phase=1;elapsed=0;
        }
        float yaw=r->yaw,pitch=r->pitch;
        if(elapsed<r->shot_delay+75) {
            cmd->angles[0]=(int)(pitch*65536.f/360.f)-ps->delta_angles[0];
            cmd->angles[1]=(int)(yaw*65536.f/360.f)-ps->delta_angles[1];
            float dx=r->landing[0]-ps->origin[0],dy=r->landing[1]-ps->origin[1],len=hypotf(dx,dy);
            if(len>1){float rad=yaw*.01745329252f;cmd->forwardmove=(signed char)(100*(dx*cosf(rad)+dy*sinf(rad))/len);cmd->rightmove=(signed char)(100*(dx*sinf(rad)-dy*cosf(rad))/len);}
            cmd->upmove=elapsed<75?127:0;
            if(elapsed>=r->shot_delay && !psyz_rj_fired){cmd->buttons|=1;psyz_rj_fired=1;}else cmd->buttons&=~1;
        }
        if(elapsed>=r->shot_delay+75){
            float heading=atan2f(r->landing[1]-ps->origin[1],r->landing[0]-ps->origin[0])*57.2957795f;
            cmd->angles[0]=-ps->delta_angles[0];cmd->angles[1]=(int)(heading*65536.f/360.f)-ps->delta_angles[1];
            cmd->forwardmove=127;cmd->rightmove=0;cmd->upmove=0;cmd->buttons&=~1;
        }
        if(ps->groundEntityNum==1023)psyz_rj_ground=1;
        if(elapsed>250 && psyz_rj_ground && ps->groundEntityNum!=1023) {
            int higher=ps->origin[2]>psyz_rj_start_z+8;
            int pickup=psyz_last_pickup_time>=psyz_rj_time && now-psyz_last_pickup_time<1500;
            if(higher || pickup){fprintf(stderr,"PSYZ_RJ_END t=%d sample=%d higher=%d pickup=%d delta_z=%.2f reconstructed_input=1\n",now,psyz_rj,higher,pickup,ps->origin[2]-psyz_rj_start_z);psyz_rj=-1;psyz_rj_last=now;}
            else{psyz_rj_phase=2;psyz_rj_landed_at=now;}
        }
        return;
    }
    // Strafe-jump only on a straight, observed demo corridor, never during firing.
    if(psyz_active_route<0 || (cmd->buttons&1))return;
    const PsyzLearnedRoute *r=Psyz_Route((size_t)psyz_active_route);int k=psyz_route_point;
    if(k+3>=r->count)return;
    float dx=r->points[k+3].p[0]-ps->origin[0],dy=r->points[k+3].p[1]-ps->origin[1];
    float length=hypotf(dx,dy);if(length<160 || fabsf(r->points[k+3].p[2]-ps->origin[2])>32)return;
    float heading=atan2f(dy,dx)*57.2957795f;
    for(int n=k;n<k+3;n++){
        float ex=r->points[n].p[0]-ps->origin[0],ey=r->points[n].p[1]-ps->origin[1];
        if(hypotf(ex,ey)>48 && fabsf(Psyz_Angle(atan2f(ey,ex)*57.2957795f-heading))>15)return;
    }
    if(fabsf(Psyz_Angle(heading-ps->viewangles[1]))>35 || cmd->forwardmove<70)return;
    float speed=hypotf(ps->velocity[0],ps->velocity[1]);if(speed<150)return;
    float velocity_heading=atan2f(ps->velocity[1],ps->velocity[0])*57.2957795f;
    int beat=Psyz_Angle(heading-velocity_heading)>=0?1:-1;
    float wish_angle=speed>320?acosf(fminf(1,(320.f-320.f*dt/1000.f)/speed))*57.2957795f:0;
    float yaw=velocity_heading+beat*wish_angle-beat*45;
    cmd->angles[1]=(int)(yaw*65536.f/360.f)-ps->delta_angles[1];
    cmd->forwardmove=127;cmd->rightmove=(signed char)(-beat*127);
    if(ps->groundEntityNum!=1023)cmd->upmove=127;
    if(now-psyz_strafe_log>500){psyz_strafe_log=now;fprintf(stderr,"PSYZ_STRAFE t=%d route=%d speed=%.2f desired_speed=%.2f ground=%d\n",now,psyz_active_route,speed,r->speed,ps->groundEntityNum);}
}

static void (*psyz_real_touch)(gentity_t*,gentity_t*,trace_t*);
static void Psyz_PreAlphaTouch(gentity_t *item,gentity_t *other,trace_t *trace) {
    int before=item?item->r.contents:0;
    int weapons_before=other && other->client?other->client->ps.stats[STAT_WEAPONS]:0;
    int ammo_before=item && item->item && other && other->client && item->item->giTag>=0 && item->item->giTag<16?other->client->ps.ammo[item->item->giTag]:0;
    psyz_real_touch(item,other,trace);
    if(!Psyz_PreAlphaEnabled() || !item || !other || other->s.number!=0 || !other->client)return;
    int ammo_after=item->item && item->item->giTag>=0 && item->item->giTag<16?other->client->ps.ammo[item->item->giTag]:0;
    if(item->item && ((before && !item->r.contents) || weapons_before!=other->client->ps.stats[STAT_WEAPONS] || ammo_after>ammo_before)) {
        const char *c=item->item->classname;
        Psyz_OpeningPickup(item,other->client->pers.cmd.serverTime);
        if(!strncmp(c,"weapon_",7) || !strncmp(c,"item_health",11) || !strcmp(c,"item_armor_body") || !strcmp(c,"item_armor_combat")){psyz_last_pickup=item->s.number;psyz_last_pickup_time=other->client->pers.cmd.serverTime;}
        fprintf(stderr,"PSYZ_PICKUP t=%d entity=%d class=%s target=%d route=%d health=%d armor=%d\n",other->client->pers.cmd.serverTime,item->s.number,item->item->classname,psyz_goal_target,psyz_active_route,other->health,other->client->ps.stats[STAT_ARMOR]);
        if(item->s.number==psyz_goal_target){psyz_goal_target=-1;psyz_active_route=-1;}
    }
}
static void Psyz_InstallPickup(void) {
    static const unsigned char expected[]={0x41,0x57,0x41,0x56,0x41,0x55,0x41,0x54,0x55,0x53,0x48,0x89,0xf3};
    void *target=(char*)qagame+0x787c0;
    if(memcmp(target,expected,sizeof(expected))){fprintf(stderr,"PSYZ_PICKUP refused ABI\n");return;}
    int result=Hook(target,Psyz_PreAlphaTouch,(void*)&psyz_real_touch);
    if(!result)psyz_vm_hook_count++;
    fprintf(stderr,"PSYZ_PICKUP install=%d\n",result);
}
