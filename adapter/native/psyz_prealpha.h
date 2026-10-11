/* Experimental Blood Run prealpha. Uses valid goals produced by stock QL. */
#include <math.h>
#include "psyz_bloodrun_bank.h"
static unsigned char psyz_goal_cache[1024][64];
static unsigned char psyz_goal_known[1024];
static int psyz_route_banned[PSYZ_ROUTE_COUNT];
static int psyz_goal_target=-1,psyz_goal_since,psyz_registry_logged;
static int psyz_rj_plan=-1,psyz_active_route=-1,psyz_route_point,psyz_last_move_time;
static float psyz_progress_distance;
static int psyz_strafe_log;
static int psyz_progress_time,psyz_banned[1024];
static int psyz_rj=-1,psyz_rj_phase,psyz_rj_time,psyz_rj_ground,psyz_rj_last,psyz_rj_fired,psyz_rj_landed_at;
static float psyz_rj_start_z;
static int psyz_debug_logged;
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
static void Psyz_PreAlphaReset(void) {
    psyz_debug_logged=0;
    memset(psyz_goal_known,0,sizeof(psyz_goal_known));memset(psyz_route_banned,0,sizeof(psyz_route_banned));memset(psyz_banned,0,sizeof(psyz_banned));
    psyz_rj_plan=psyz_goal_target=psyz_active_route=psyz_rj=psyz_last_pickup=-1;
    
    psyz_registry_logged=psyz_rj_phase=psyz_rj_last=psyz_last_move_time=0;
    psyz_last_pickup_time=psyz_rj_landed_at=psyz_strafe_log=0;
}
static float Psyz_ItemWeight(gentity_t *item,gentity_t *own,int recovering) {
    const char *c=item->item->classname;int h=own->health,a=own->client->ps.stats[STAT_ARMOR];
    int weapons=own->client->ps.stats[STAT_WEAPONS];
    if(!strcmp(c,"weapon_rocketlauncher"))return weapons&(1<<5)?8:180;
    if(!strcmp(c,"weapon_lightning"))return weapons&(1<<6)?8:150;
    if(!strcmp(c,"weapon_railgun"))return weapons&(1<<7)?8:145;
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
    for(size_t i=0;i<PSYZ_ROUTE_COUNT;i++) {
        const PsyzLearnedRoute *r=&psyz_routes[i];if(psyz_route_banned[i]>own->client->pers.cmd.serverTime)continue;
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
    if(!psyz_debug_logged){
        psyz_debug_logged=1;void *im;memcpy(&im,(char*)qagame+0x2d8000,sizeof(im));
        int (*get_item)(int,const char*,void*);memcpy(&get_item,(char*)im+0x4d0,sizeof(get_item));
        int count=0;
        for(int n=0;n<1024;n++){
            gentity_t *e=&g_entities[n];if(!e->inuse || !e->item || !e->item->pickup_name)continue;
            unsigned char candidate[256];int cursor=-1;
            for(int j=0;j<64;j++){
                memset(candidate,0,sizeof(candidate));int next=get_item(cursor,e->item->pickup_name,candidate);
                if(next<0 || next==cursor)break;
                cursor=next;
                int id,area,flags;float p[3];memcpy(p,candidate,12);memcpy(&area,candidate+12,4);memcpy(&id,candidate+40,4);memcpy(&flags,candidate+48,4);
                if(id==n && area>0 && area<2393 && flags==1 && Psyz_Distance(p,e->r.currentOrigin)<64){memcpy(psyz_goal_cache[n],candidate,64);psyz_goal_known[n]=1;count++;break;}
            }
        }
        fprintf(stderr,"PSYZ_GOAL_REGISTRY valid_item_goals=%d weapons=%d ammo_rl=%d\n",count,own->client->ps.stats[STAT_WEAPONS],own->client->ps.ammo[5]);
    }
    int recovering=own->health<70 || (own->health<100 && own->client->ps.stats[STAT_ARMOR]<30);
    // Only exact enemy HP/armor are read, never hidden enemy coordinates.
    for(int i=1;i<64;i++) {
        gentity_t *e=&g_entities[i];if(!e->inuse||!e->client||(e->r.svFlags&8)||e->health<=0)continue;
        float ours=own->health+fminf(own->client->ps.stats[STAT_ARMOR],2*own->health);
        float theirs=e->health+fminf(e->client->ps.stats[STAT_ARMOR],2*e->health);
        if(theirs>ours*1.15f)recovering=1;
    }
    int keep=psyz_goal_target>=0 && psyz_goal_known[psyz_goal_target] &&
        g_entities[psyz_goal_target].r.contents && now-psyz_goal_since<3000;
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
    if(psyz_goal_target<0)return;
    float distance=Psyz_Distance(own->client->ps.origin,g_entities[psyz_goal_target].r.currentOrigin);
    if(distance<psyz_progress_distance-32){psyz_progress_distance=distance;psyz_progress_time=now;}
    if(now-psyz_progress_time>6000) {
        fprintf(stderr,"PSYZ_REPATH t=%d target=%d route=%d reason=no_progress\n",now,psyz_goal_target,psyz_active_route);
        if(psyz_active_route>=0)psyz_route_banned[psyz_active_route]=now+60000;
        psyz_banned[psyz_goal_target]=now+8000;psyz_goal_target=-1;psyz_active_route=-1;
        int gs;memcpy(&gs,(char*)state+0x1968,4);void *imports;memcpy(&imports,(char*)qagame+0x2d8000,sizeof(imports));
        void (*pop)(int);memcpy(&pop,(char*)imports+0x468,sizeof(pop));pop(gs);
        float expired=0;memcpy((char*)state+0x179c,&expired,4);return;
    }
    memcpy(output,psyz_goal_cache[psyz_goal_target],64);
    if(psyz_active_route<0)Psyz_SelectDemoRoute(own,psyz_goal_target);
    if(psyz_active_route>=0) {
        const PsyzLearnedRoute *r=&psyz_routes[psyz_active_route];
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
    int dt=now-psyz_last_move_time;psyz_last_move_time=now;
    if(dt<=0 || dt>100 || own->health<=0){psyz_rj=-1;return;}
    // Never inherit habitual crouching. Agreed exceptions are not enabled yet.
    if(cmd->upmove<0)cmd->upmove=0;
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
    const PsyzLearnedRoute *r=&psyz_routes[psyz_active_route];int k=psyz_route_point;
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
    fprintf(stderr,"PSYZ_PICKUP install=%d\n",result);
}
