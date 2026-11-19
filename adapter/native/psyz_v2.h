/* Blood Run V2 execution. Independent of the legacy PreAlpha switch.
 * Only own inventory, public item clocks, stock goals and recorded map routes.
 * No writes to player physics except explicitly marked, empty-LAB probe setup.
 */
#include "psyz_v2_red_presets.h"
#include "psyz_v2_spin_reference.h"
#include "psyz_v2_tp_path.h"
typedef struct {
    void *bot_state;
    int target,since,progress_at,last_time,combat_until,health,armor,log_at;
    float best_distance,look_yaw,last_pos[3];
    int banned[1024],teleport_until;
    int jump,jump_phase,jump_since,launch_at,shot_ammo,shot_at,picked_at,cooldown,probe;
    int jump_probe_active;
    int strafe_since,strafe_until,strafe_last_ground,strafe_jumps,strafe_log,strafe_phase;
    float strafe_heading,strafe_peak;
    int spin_start,spin_cooldown,spin_probe;float spin_yaw;
    int movement_probe,movement_probe_at,fire_count[16],fire_log_at[16];
    int tp_active,tp_point,tp_since,tp_picked;
} PsyzV2State;
static PsyzV2State psyz_v2[64];
static int psyz_v2_reject_goal;
static int Psyz_V2LabEmpty(void);
static int Psyz_V2Enabled(void){
    cvar_t *v=Cvar_FindVar("qlx_psyzV2"),*m=Cvar_FindVar("mapname"),*t=Cvar_FindVar("qlx_psyzTestInstance"),*p=Cvar_FindVar("net_port");
    cvar_t *lab=Cvar_FindVar("qlx_psyzV2Lab");
    return v && v->integer==1 && t && t->integer==1 && m && !strcmp(m->string,"bloodrun") && p &&
        (p->integer==27961 || (p->integer==27962 && lab && lab->integer==1));
}
static void Psyz_V2Reset(void){
    memset(psyz_v2,0,sizeof(psyz_v2));psyz_v2_reject_goal=0;
    for(int i=0;i<64;i++){psyz_v2[i].target=-1;psyz_v2[i].jump=-1;}
}
static int Psyz_V2Ready(const gentity_t *own){
    return own->health>=100 && own->client->ps.stats[STAT_ARMOR]>=100 &&
        Psyz_TrinityReady(own->client->ps.stats[STAT_WEAPONS],own->client->ps.ammo)>=2;
}
static int Psyz_V2Minor(const char *c){
    return !strcmp(c,"item_armor_shard") || !strcmp(c,"item_health_small");
}
static float Psyz_V2Weight(gentity_t *e,gentity_t *own,int combat){
    const char *c=e->item->classname;playerState_t *ps=&own->client->ps;
    int h=own->health,a=ps->stats[STAT_ARMOR],guns=Psyz_TrinityReady(ps->stats[STAT_WEAPONS],ps->ammo);
    if(Psyz_V2Minor(c))return combat || !(Psyz_V2Ready(own) || h<70)?0:!strcmp(c,"item_armor_shard")?(a<190?18:0):(h<100?24:0);
    if(!strcmp(c,"item_health_mega"))return h>=190?0:h<80?350:h<150?285:170;
    if(!strcmp(c,"item_armor_body"))return a>=190?0:a<100?310:220;
    if(!strcmp(c,"item_armor_combat"))return a>=150?0:a<100?260:135;
    if(!strncmp(c,"item_health",11))return h>=100?0:h<60?330:210;
    int w=!strcmp(c,"weapon_rocketlauncher")?5:!strcmp(c,"weapon_lightning")?6:!strcmp(c,"weapon_railgun")?7:
          !strcmp(c,"weapon_shotgun")?3:!strcmp(c,"weapon_plasmagun")?8:!strcmp(c,"weapon_grenadelauncher")?4:0;
    if(w){
        if(!(ps->stats[STAT_WEAPONS]&(1<<w)) || ps->ammo[w]<=0)return w>=5 && w<=7?(h<50?230:guns<2?335:235):w==3?155:w==8?120:55;
        return ps->ammo[w]<Psyz_Reserve(w)?150:0;
    }
    if(!strncmp(c,"ammo_",5))return Psyz_AmmoNeed(ps->stats[STAT_WEAPONS],ps->ammo,e->item->giTag);
    return 0;
}
static int Psyz_V2Red(void){
    for(int i=64;i<1024;i++)if(psyz_goal_known[i] && g_entities[i].inuse && g_entities[i].item &&
        g_entities[i].item->classname && !strcmp(g_entities[i].item->classname,"item_armor_body"))return i;
    return -1;
}
static void Psyz_V2GoalStack(void *state,void *output,int reject){
    int gs;void *imports;void (*pop)(int);void (*push)(int,void*);
    memcpy(&gs,(char*)state+0x1968,4);memcpy(&imports,(char*)qagame+0x2d8000,sizeof(imports));
    if(!imports)return;
    memcpy(&pop,(char*)imports+0x468,sizeof(pop));memcpy(&push,(char*)imports+0x460,sizeof(push));
    if(!pop || (!reject && !push))return;
    pop(gs);if(!reject)push(gs,output);
    if(reject){float zero=0;memcpy((char*)state+0x179c,&zero,4);psyz_v2_reject_goal=1;}
}
static void Psyz_V2PointGoal(void *output,const float *p,int area){
    /* Preserve real goal bounds; alter only position, valid AAS area and item flag. */
    int flags=0;memcpy(output,p,12);memcpy((char*)output+12,&area,4);memcpy((char*)output+48,&flags,4);
}
static int Psyz_V2JumpMask(void){cvar_t *m=Cvar_FindVar("qlx_psyzV2JumpMask");return m?m->integer&31:0;}
static void Psyz_V2Goal(void *state,void *output,gentity_t *own){
    if(!Psyz_V2Enabled() || own->s.number<0 || own->s.number>=64)return;
    PsyzV2State *s=&psyz_v2[own->s.number];playerState_t *ps=&own->client->ps;int now=own->client->pers.cmd.serverTime;
    s->bot_state=state;
    int combat=(own->client->pers.cmd.buttons&1) || now<s->combat_until;
    if(s->movement_probe>0 && s->movement_probe<3 && s->movement_probe_at && now-s->movement_probe_at<1800 && Psyz_V2LabEmpty()){
        for(int i=64;i<1024;i++)if(psyz_goal_known[i] && g_entities[i].item && !strcmp(g_entities[i].item->classname,"item_health_mega")){
            s->target=i;memcpy(output,psyz_goal_cache[i],64);Psyz_V2GoalStack(state,output,0);return;
        }
    }
    int red=Psyz_V2Red();
    if(s->tp_active){
        int available=red>=0 && (g_entities[red].r.contents || (g_entities[red].nextthink>now && g_entities[red].nextthink<s->tp_since+16000));
        if(now-s->tp_since>16000 || !available || s->tp_picked || (combat && own->health<80)){
            fprintf(stderr,"PSYZ_V2_TP_END slot=%d t=%d outcome=%s point=%d\n",own->s.number,now,s->tp_picked?"target_pickup":"timeout_unavailable_or_combat",s->tp_point);
            s->tp_active=0;
        }else{
            s->target=red;
            memcpy(output,psyz_goal_cache[red],64);
            if(s->tp_point<PSYZ_V2_TP_COUNT)Psyz_V2PointGoal(output,psyz_v2_tp_points[s->tp_point].p,psyz_v2_tp_points[s->tp_point].area);
            Psyz_V2GoalStack(state,output,0);return;
        }
    }
    if(s->jump>=0 && s->target==red && red>=0){
        memcpy(output,psyz_goal_cache[red],64);
        if(s->jump_phase<3)Psyz_V2PointGoal(output,psyz_v2_red_presets[s->jump].runup,psyz_v2_red_presets[s->jump].area);
        Psyz_V2GoalStack(state,output,0);return;
    }
    int selected=-1;float best=-1e9f;
    for(int i=64;i<1024;i++){
        gentity_t *e=&g_entities[i];
        if(!psyz_goal_known[i] || s->banned[i]>now || !e->inuse || !e->item || !e->item->classname)continue;
        float weight=Psyz_V2Weight(e,own,combat);if(weight<=0)continue;
        float distance=Psyz_Distance(ps->origin,e->r.currentOrigin);
        float travel=distance/300.f+fabsf(ps->origin[2]-e->r.currentOrigin[2])/250.f;
        float until=e->r.contents?0:(e->nextthink>now?(e->nextthink-now)/1000.f:10000);
        int major=i==red || !strcmp(e->item->classname,"item_health_mega") || !strcmp(e->item->classname,"item_armor_combat");
        if(until>0 && (!major || until>travel+2.5f || (own->health<60 && until>travel+.5f)))continue;
        float score=weight-travel*26-fmaxf(0,until-travel)*35;
        if(i==red && now<s->teleport_until)score+=200;
        if(distance<112 && fabsf(ps->origin[2]-e->r.currentOrigin[2])<40 && e->r.contents)score+=80;
        if(i==s->target && now-s->since<750)score+=30;
        if(score>best){best=score;selected=i;}
    }
    /* Resource recovery replaces only item navigation. Combat aim/fire stay stock. */
    if(selected<0){
        int old;memcpy(&old,(char*)output+40,4);
        if(old>=0 && old<1024 && g_entities[old].item && g_entities[old].item->classname &&
            Psyz_V2Minor(g_entities[old].item->classname) && Psyz_V2Weight(&g_entities[old],own,combat)<=0)
            Psyz_V2GoalStack(state,output,1);
        s->target=-1;return;
    }
    float distance=Psyz_Distance(ps->origin,g_entities[selected].r.currentOrigin);
    if(selected!=s->target){
        s->target=selected;s->since=s->progress_at=now;s->best_distance=distance;s->look_yaw=ps->viewangles[1];
        fprintf(stderr,"PSYZ_V2_TARGET slot=%d t=%d entity=%d class=%s hp=%d armor=%d guns=%d combat=%d ready=%d due=%d\n",
            own->s.number,now,selected,g_entities[selected].item->classname,own->health,ps->stats[STAT_ARMOR],
            Psyz_TrinityReady(ps->stats[STAT_WEAPONS],ps->ammo),combat,Psyz_V2Ready(own),g_entities[selected].r.contents?now:g_entities[selected].nextthink);
    }else if(distance<s->best_distance-20){s->best_distance=distance;s->progress_at=now;}
    else if(now-s->progress_at>4500 && (distance>80 || !g_entities[selected].r.contents)){
        s->banned[selected]=now+8000;s->target=-1;
        fprintf(stderr,"PSYZ_V2_RECOVERY slot=%d t=%d entity=%d reason=no_progress bounded_ms=4500\n",own->s.number,now,selected);
        return;
    }
    memcpy(output,psyz_goal_cache[selected],64);
    if(selected==red && !combat && own->health>=95 && (ps->stats[STAT_WEAPONS]&(1<<5)) && ps->ammo[5]>0 && now>=s->cooldown){
        int plan=-1;float nearest=650;int mask=Psyz_V2JumpMask();
        for(int j=0;j<PSYZ_V2_RED_COUNT;j++)if(mask&(1<<j)){
            const PsyzV2RedPreset *r=&psyz_v2_red_presets[j];float d=Psyz_Distance(ps->origin,r->runup);
            if(d<nearest && fabsf(ps->origin[2]-r->start[2])<48){nearest=d;plan=j;}
        }
        if(plan>=0){s->jump=plan;s->jump_phase=0;s->jump_since=now;s->picked_at=0;s->shot_at=0;
            Psyz_V2PointGoal(output,psyz_v2_red_presets[plan].runup,psyz_v2_red_presets[plan].area);
            fprintf(stderr,"PSYZ_V2_RJ_BEGIN slot=%d t=%d preset=%d target=%d source=observed_trajectory\n",own->s.number,now,plan,selected);
        }
    }
    Psyz_V2GoalStack(state,output,0);
}
static void Psyz_V2View(usercmd_t *cmd,const playerState_t *ps,float pitch,float yaw){
    cmd->angles[0]=(int)(pitch*65536.f/360.f)-ps->delta_angles[0];
    cmd->angles[1]=(int)(yaw*65536.f/360.f)-ps->delta_angles[1];
}
static void Psyz_V2Wish(usercmd_t *cmd,float yaw,float x,float y,float magnitude){
    float length=hypotf(x,y);if(length<.01f){cmd->forwardmove=cmd->rightmove=0;return;}
    x/=length;y/=length;float a=yaw*.01745329252f;
    float f=x*cosf(a)+y*sinf(a),r=x*sinf(a)-y*cosf(a);
    float scale=magnitude/fmaxf(fabsf(f),fabsf(r));
    cmd->forwardmove=(signed char)fmaxf(-127,fminf(127,f*scale));
    cmd->rightmove=(signed char)fmaxf(-127,fminf(127,r*scale));
}
static float Psyz_V2CircleYaw(float heading,int beat,float speed,int dt){
    /* Ground friction/acceleration differ from the air-strafe projection. */
    float seconds=dt/1000.f,after=fmaxf(0,speed-fmaxf(speed,100)*6*seconds);
    float projection=fmaxf(0,320-320*10*seconds);
    float angle=after>projection?acosf(fminf(1,projection/after))*57.2957795f:0;
    return heading+beat*(45-angle);
}
static void Psyz_V2JumpEnd(gentity_t *own,PsyzV2State *s,int now,const char *reason){
    fprintf(stderr,"PSYZ_V2_RJ_END slot=%d t=%d preset=%d target=%d outcome=%s pickup_confirmed=%d pos=%.2f,%.2f,%.2f\n",
        own->s.number,now,s->jump,s->target,reason,s->picked_at>0,own->client->ps.origin[0],own->client->ps.origin[1],own->client->ps.origin[2]);
    s->jump=-1;s->cooldown=now+7000;s->target=-1;
    s->jump_probe_active=0;
}
static int Psyz_V2LabEmpty(void){
    cvar_t *p=Cvar_FindVar("net_port"),*l=Cvar_FindVar("qlx_psyzV2Lab");
    if(!p || p->integer!=27962 || !l || l->integer!=1)return 0;
    for(int i=0;i<64;i++)if(g_entities[i].inuse && g_entities[i].client && !(g_entities[i].r.svFlags&8))return 0;
    return 1;
}
static void Psyz_V2LabParkOthers(gentity_t *own){
    if(!Psyz_V2LabEmpty())return;
    const float p[3]={960,-1104,88.125f};
    for(int i=0;i<64;i++)if(g_entities[i].inuse && g_entities[i].client && &g_entities[i]!=own && (g_entities[i].r.svFlags&8)){
        memcpy(g_entities[i].client->ps.origin,p,12);memcpy(g_entities[i].r.currentOrigin,p,12);
        memset(g_entities[i].client->ps.velocity,0,12);
    }
}
static void Psyz_V2Probe(gentity_t *own,PsyzV2State *s,int now){
    cvar_t *p=Cvar_FindVar("qlx_psyzV2JumpProbe");int request=p?p->integer:0;
    if(!request){s->probe=0;return;}
    if(request<1 || request>5 || s->probe==request || !Psyz_V2LabEmpty())return;
    int red=Psyz_V2Red();if(red<0 || !g_entities[red].r.contents)return;
    s->probe=request;const PsyzV2RedPreset *r=&psyz_v2_red_presets[request-1];playerState_t *ps=&own->client->ps;
    /* Controlled initial state ONLY. After this all movement is normal usercmd physics. */
    memcpy(ps->origin,r->runup,12);memcpy(own->r.currentOrigin,r->runup,12);memset(ps->velocity,0,12);
    own->health=ps->stats[STAT_HEALTH]=125;ps->stats[STAT_ARMOR]=100;ps->stats[STAT_WEAPONS]|=1<<5;ps->ammo[5]=20;
    s->target=red;s->jump=request-1;s->jump_phase=1;s->jump_since=now;s->picked_at=s->shot_at=0;
    s->jump_probe_active=1;Psyz_V2LabParkOthers(own);
    fprintf(stderr,"PSYZ_V2_PROBE_SETUP slot=%d t=%d preset=%d empty_lab=1 position_write=initial_state_only\n",own->s.number,now,request-1);
}
static int Psyz_V2JumpMove(gentity_t *own,PsyzV2State *s,int now){
    if(s->jump<0)return 0;
    playerState_t *ps=&own->client->ps;usercmd_t *cmd=&own->client->pers.cmd;
    const PsyzV2RedPreset *r=&psyz_v2_red_presets[s->jump];
    if(s->picked_at){Psyz_V2JumpEnd(own,s,now,"target_pickup");return 0;}
    if(now-s->jump_since>6500 || now<s->jump_since || own->health<45 || ps->ammo[5]<=0){Psyz_V2JumpEnd(own,s,now,"timeout_or_resources");return 0;}
    if((cmd->buttons&1) && s->jump_phase<3 && !Psyz_V2LabEmpty()){Psyz_V2JumpEnd(own,s,now,"combat_interrupt");return 0;}
    if(s->jump_phase==0){
        if(Psyz_Distance(ps->origin,r->runup)>28)return 0;
        s->jump_phase=1;s->jump_since=now;
    }
    float heading=atan2f(r->velocity[1],r->velocity[0])*57.2957795f;
    cmd->weapon=5;cmd->buttons&=~1;cmd->upmove=0;
    if(s->jump_phase==1){
        Psyz_V2View(cmd,ps,0,heading);cmd->forwardmove=cmd->rightmove=0;
        if(ps->weapon!=5 || ps->weaponTime>0 || ps->groundEntityNum==1023 || hypotf(ps->velocity[0],ps->velocity[1])>35)return 1;
        s->jump_phase=2;s->jump_since=now;
        fprintf(stderr,"PSYZ_V2_RJ_RUNUP slot=%d t=%d preset=%d\n",own->s.number,now,s->jump);
    }
    if(s->jump_phase==2){
        float dx=r->start[0]-ps->origin[0],dy=r->start[1]-ps->origin[1];float speed=hypotf(r->velocity[0],r->velocity[1]);
        float ux=r->velocity[0]/speed,uy=r->velocity[1]/speed,remaining=dx*ux+dy*uy,lateral=dx*uy-dy*ux;
        Psyz_V2View(cmd,ps,0,heading);
        Psyz_V2Wish(cmd,heading,ux+dx*.006f,uy+dy*.006f,fminf(127,speed/320.f*127.f));
        if(remaining<10 && remaining> -28 && fabsf(lateral)<24 && hypotf(ps->velocity[0],ps->velocity[1])>speed*.85f){
            cmd->upmove=127;s->jump_phase=3;s->launch_at=now;s->shot_ammo=ps->ammo[5];
            fprintf(stderr,"PSYZ_V2_RJ_LAUNCH slot=%d t=%d preset=%d pos=%.2f,%.2f,%.2f speed=%.2f\n",own->s.number,now,s->jump,ps->origin[0],ps->origin[1],ps->origin[2],hypotf(ps->velocity[0],ps->velocity[1]));
        }else if(remaining< -28 || fabsf(lateral)>60 || now-s->jump_since>2000){Psyz_V2JumpEnd(own,s,now,"runup_diverged");return 0;}
        return 1;
    }
    int elapsed=now-s->launch_at;const PsyzV2FlightPoint *point=&r->flight[r->count-1];
    for(int i=1;i<r->count;i++)if(r->flight[i].ms>=elapsed+75){point=&r->flight[i];break;}
    float yaw=point->view[1],pitch=0;
    /* Demo EV_FIRE_WEAPON is observed after PM_Weapon. The first floor-RJ
       needs one command frame of lead to reproduce its recorded blast timing. */
    int fire_delay=r->shot_ms-(s->jump==0?25:0);
    if(elapsed>=fire_delay && !s->shot_at){
        pitch=r->shot_view[0];yaw=r->shot_view[1];
        if(ps->weapon==5 && ps->weaponTime<=0){cmd->buttons|=1;s->shot_at=now;
            fprintf(stderr,"PSYZ_V2_RJ_SHOT slot=%d t=%d preset=%d elapsed=%d pitch=%.2f yaw=%.2f\n",own->s.number,now,s->jump,elapsed,pitch,yaw);}
    }
    Psyz_V2View(cmd,ps,pitch,yaw);
    Psyz_V2Wish(cmd,yaw,point->v[0]+(point->p[0]-ps->origin[0])*4,point->v[1]+(point->p[1]-ps->origin[1])*4,127);
    if(elapsed>r->flight[r->count-1].ms-100 && s->target>=0){
        const float *p=g_entities[s->target].r.currentOrigin;
        Psyz_V2Wish(cmd,yaw,(p[0]-ps->origin[0])*4-ps->velocity[0],(p[1]-ps->origin[1])*4-ps->velocity[1],127);
    }
    if(elapsed>2800){Psyz_V2JumpEnd(own,s,now,"no_target_pickup");return 0;}
    return 1;
}
static int Psyz_V2TPMove(gentity_t *own,PsyzV2State *s,int now){
    if(!s->tp_active)return 0;
    int red=Psyz_V2Red();playerState_t *ps=&own->client->ps;usercmd_t *cmd=&own->client->pers.cmd;
    if(s->tp_picked || red<0 || now-s->tp_since>16000 || own->health<80 || (!g_entities[red].r.contents && g_entities[red].nextthink>s->tp_since+16000)){
        fprintf(stderr,"PSYZ_V2_TP_END slot=%d t=%d outcome=%s point=%d\n",own->s.number,now,s->tp_picked?"target_pickup":"timeout_unavailable_or_combat",s->tp_point);s->tp_active=0;return 0;
    }
    s->target=red;
    while(s->tp_point<PSYZ_V2_TP_COUNT && !psyz_v2_tp_points[s->tp_point].jump &&
          hypotf(ps->origin[0]-psyz_v2_tp_points[s->tp_point].p[0],ps->origin[1]-psyz_v2_tp_points[s->tp_point].p[1])<18 &&
          fabsf(ps->origin[2]-psyz_v2_tp_points[s->tp_point].p[2])<32)s->tp_point++;
    const float *p=s->tp_point<PSYZ_V2_TP_COUNT?psyz_v2_tp_points[s->tp_point].p:g_entities[red].r.currentOrigin;
    float dx=p[0]-ps->origin[0],dy=p[1]-ps->origin[1],distance=hypotf(dx,dy);
    int jump=s->tp_point<PSYZ_V2_TP_COUNT && psyz_v2_tp_points[s->tp_point].jump;
    float heading=atan2f(dy,dx)*57.2957795f,yaw=(cmd->angles[1]+ps->delta_angles[1])*360.f/65536.f;
    if(!(cmd->buttons&1)){yaw=Psyz_TurnToward(ps->viewangles[1],heading,10);Psyz_V2View(cmd,ps,0,yaw);}
    float x=dx*5-ps->velocity[0]*.65f,y=dy*5-ps->velocity[1]*.65f,magnitude=127;
    if(jump){x=dx;y=dy;}
    if(p[2]<ps->origin[2]-48 && distance<70)magnitude=45;
    if(!jump && distance<35)magnitude=fmaxf(40,distance/35*100);
    Psyz_V2Wish(cmd,yaw,x,y,magnitude);cmd->upmove=0;s->strafe_until=0;
    if(jump && distance<12 && ps->groundEntityNum!=1023 && hypotf(ps->velocity[0],ps->velocity[1])>=280){
        cmd->upmove=127;s->tp_point++;
        fprintf(stderr,"PSYZ_V2_TP_JUMP slot=%d t=%d speed=%.2f\n",own->s.number,now,hypotf(ps->velocity[0],ps->velocity[1]));
    }
    return 1;
}
static int Psyz_V2StraightCorridor(const playerState_t *ps,float heading){
    for(size_t r=0;r<PSYZ_ALL_ROUTE_COUNT;r++){
        const PsyzLearnedRoute *route=Psyz_Route(r);
        for(int i=0;i+3<route->count;i++){
            if(Psyz_Distance(ps->origin,route->points[i].p)>60)continue;
            const float *a=route->points[i].p,*b=route->points[i+3].p;
            if(fabsf(a[2]-b[2])>16 || hypotf(b[0]-a[0],b[1]-a[1])<165)continue;
            float axis=atan2f(b[1]-a[1],b[0]-a[0])*57.2957795f;
            if(fabsf(Psyz_Angle(axis-heading))>12)continue;
            int straight=1;
            for(int j=i+1;j<i+3;j++){
                const float *p=route->points[j].p;float yaw=atan2f(p[1]-a[1],p[0]-a[0])*57.2957795f;
                if(fabsf(Psyz_Angle(yaw-axis))>10 || fabsf(p[2]-a[2])>16)straight=0;
            }
            if(straight)return 1;
        }
    }
    return 0;
}
static void Psyz_V2Move(gentity_t *own){
    if(!Psyz_V2Enabled() || !Psyz_IsOurBot(own) || own->s.number<0 || own->s.number>=64 || !own->client)return;
    PsyzV2State *s=&psyz_v2[own->s.number];playerState_t *ps=&own->client->ps;usercmd_t *cmd=&own->client->pers.cmd;int now=cmd->serverTime;
    if(own->health<=0 || ps->pm_type!=0){s->jump=-1;s->target=-1;s->strafe_until=s->spin_start=s->jump_probe_active=s->tp_active=0;return;}
    if(now<s->last_time){memset(s,0,sizeof(*s));s->target=s->jump=-1;}
    int dt=now-s->last_time;if(dt<=0 || dt>100)dt=25;
    if((cmd->buttons&1) || ((s->health-own->health>1 || s->armor-ps->stats[STAT_ARMOR]>1) && s->jump<0))s->combat_until=now+700;
    if(s->last_time && Psyz_Distance(ps->origin,s->last_pos)>256 &&
        ps->origin[0]< -480 && ps->origin[0]> -640 && ps->origin[1]>200 && ps->origin[2]>500){
        s->teleport_until=now+4000;fprintf(stderr,"PSYZ_V2_TELEPORT_EXIT slot=%d t=%d red_priority=1\n",own->s.number,now);
        s->tp_active=1;s->tp_point=0;s->tp_since=now;s->tp_picked=0;
    }
    s->last_time=now;s->health=own->health;s->armor=ps->stats[STAT_ARMOR];memcpy(s->last_pos,ps->origin,12);
    Psyz_V2Probe(own,s,now);
    if(Psyz_V2JumpMove(own,s,now))return;
    cvar_t *move_probe=Cvar_FindVar("qlx_psyzV2MoveProbe");int request=move_probe?move_probe->integer:0;
    if(!request)s->movement_probe=0;
    if(request>=1 && request<=3 && request!=s->movement_probe && Psyz_V2LabEmpty()){
        float p[3]={385.1714f,-231.685f,88.3296f};
        if(request==3){p[0]=672;p[1]=-1296;p[2]=96;s->teleport_until=now+10000;}
        memcpy(ps->origin,p,12);memcpy(own->r.currentOrigin,p,12);memset(ps->velocity,0,12);
        if(request==2)ps->velocity[0]=400;
        own->health=ps->stats[STAT_HEALTH]=125;ps->stats[STAT_ARMOR]=100;
        if(request==3){ps->stats[STAT_WEAPONS]|=(1<<5)|(1<<6)|(1<<7);ps->ammo[5]=20;ps->ammo[6]=100;ps->ammo[7]=10;}
        s->movement_probe=request;s->movement_probe_at=now;s->combat_until=s->strafe_until=0;
        Psyz_V2LabParkOthers(own);
        fprintf(stderr,"PSYZ_V2_MOVE_PROBE slot=%d t=%d type=%d initial_speed=%d empty_lab=1\n",own->s.number,now,request,request==2?400:0);
    }
    if(s->movement_probe>0 && s->movement_probe<3 && s->movement_probe_at && now-s->movement_probe_at<1800 && Psyz_V2LabEmpty()){
        Psyz_V2View(cmd,ps,0,0);cmd->forwardmove=127;cmd->rightmove=0;cmd->buttons=0;
        s->combat_until=0;
    }
    if(Psyz_V2TPMove(own,s,now))return;
    int combat=now<s->combat_until;
    if(s->bot_state){
        /* Nearby goals can bypass the LTG callback. Read the real botlib top
           goal and remove only an explicitly forbidden small-item detour. */
        void *imports;int gs;int (*top)(int,void*);unsigned char goal[64];
        memcpy(&imports,(char*)qagame+0x2d8000,sizeof(imports));
        memcpy(&gs,(char*)s->bot_state+0x1968,4);
        if(imports){
            memcpy(&top,(char*)imports+0x490,sizeof(top));
            if(top && top(gs,goal)){
                int id,flags;float position[3];memcpy(position,goal,12);memcpy(&id,goal+40,4);memcpy(&flags,goal+48,4);
                if(flags==1 && id>=64 && id<1024 && g_entities[id].inuse && g_entities[id].item && g_entities[id].item->classname &&
                    Psyz_Distance(position,g_entities[id].r.currentOrigin)<64 && Psyz_V2Minor(g_entities[id].item->classname) &&
                    Psyz_V2Weight(&g_entities[id],own,combat)<=0){
                    int reject=s->target<0 || !psyz_goal_known[s->target];
                    if(!reject){memcpy(goal,psyz_goal_cache[s->target],64);
                        if(s->tp_active && s->tp_point<PSYZ_V2_TP_COUNT)Psyz_V2PointGoal(goal,psyz_v2_tp_points[s->tp_point].p,psyz_v2_tp_points[s->tp_point].area);}
                    Psyz_V2GoalStack(s->bot_state,goal,reject);
                    fprintf(stderr,"PSYZ_V2_MINOR_REJECT slot=%d t=%d entity=%d combat=%d\n",own->s.number,now,id,combat);
                }
            }
        }
    }
    if(!combat && s->target>=0 && g_entities[s->target].r.contents &&
        Psyz_Distance(ps->origin,g_entities[s->target].r.currentOrigin)<112 &&
        fabsf(ps->origin[2]-g_entities[s->target].r.currentOrigin[2])<40){
        float yaw=s->look_yaw;const float *p=g_entities[s->target].r.currentOrigin;
        Psyz_V2View(cmd,ps,0,yaw);Psyz_V2Wish(cmd,yaw,p[0]-ps->origin[0],p[1]-ps->origin[1],127);
        s->strafe_until=0;return;
    }
    /* A short measured corridor licenses a bounded strafe burst, never a blind
       map-wide straight run or a cosmetic spin during combat/item approach. */
    cvar_t *strafe=Cvar_FindVar("qlx_psyzV2Strafe");
    if(!strafe || !strafe->integer || combat || cmd->forwardmove<90 || abs(cmd->rightmove)>50){s->strafe_until=0;return;}
    float yaw=(cmd->angles[1]+ps->delta_angles[1])*360.f/65536.f,speed=hypotf(ps->velocity[0],ps->velocity[1]);
    if(!s->strafe_until && ps->groundEntityNum!=1023 && Psyz_V2StraightCorridor(ps,yaw)){
        s->strafe_since=now;s->strafe_until=now+1800;s->strafe_heading=yaw;s->strafe_peak=speed;s->strafe_jumps=0;s->strafe_last_ground=0;
        s->strafe_phase=speed<300?1:2;
    }
    if(!s->strafe_until)return;
    if(now>=s->strafe_until || fabsf(Psyz_Angle(yaw-s->strafe_heading))>22 || (s->strafe_phase>1 && speed<160)){s->strafe_until=0;return;}
    int ground=ps->groundEntityNum!=1023;
    if(s->strafe_phase==1 && (now-s->strafe_since>=375 || speed>=340)){s->strafe_phase=2;s->strafe_last_ground=0;}
    if(ground && !s->strafe_last_ground && s->strafe_phase>1)s->strafe_jumps++;
    s->strafe_last_ground=ground;
    float heading=speed>50?atan2f(ps->velocity[1],ps->velocity[0])*57.2957795f:s->strafe_heading;int beat=s->strafe_phase==1?1:((now-s->strafe_since)/300)&1?1:-1;
    float view=s->strafe_phase==1?Psyz_V2CircleYaw(heading,beat,speed,dt):Psyz_StrafeViewYaw(heading,beat,speed,dt);
    if(fabsf(Psyz_Angle(view-s->strafe_heading))>50){s->strafe_until=0;return;}
    Psyz_V2View(cmd,ps,0,view);cmd->forwardmove=127;cmd->rightmove=(signed char)(beat*127);cmd->upmove=ground && s->strafe_phase>1?127:0;
    if(speed>s->strafe_peak)s->strafe_peak=speed;
    if(now-s->strafe_log>250){s->strafe_log=now;fprintf(stderr,"PSYZ_V2_STRAFE slot=%d t=%d speed=%.2f peak=%.2f jumps=%d phase=%d measured_corridor=1\n",own->s.number,now,speed,s->strafe_peak,s->strafe_jumps,s->strafe_phase);}
}
static void Psyz_V2Spin(gentity_t *own){
    if(!Psyz_V2Enabled() || !Psyz_IsOurBot(own) || own->s.number<0 || own->s.number>=64 || !own->client)return;
    PsyzV2State *s=&psyz_v2[own->s.number];playerState_t *ps=&own->client->ps;usercmd_t *cmd=&own->client->pers.cmd;int now=cmd->serverTime;
    cvar_t *on=Cvar_FindVar("qlx_psyzV2Spin"),*probe=Cvar_FindVar("qlx_psyzV2SpinProbe");
    int forced=probe && probe->integer==1 && Psyz_V2LabEmpty();if(!forced)s->spin_probe=0;
    if(!on || !on->integer || own->health<=0 || ps->pm_type!=0 || (cmd->buttons&1) || now<s->combat_until || s->jump>=0){
        if(s->spin_start)fprintf(stderr,"PSYZ_V2_SPIN_END slot=%d t=%d outcome=interrupted\n",own->s.number,now);
        s->spin_start=0;return;
    }
    float speed=hypotf(ps->velocity[0],ps->velocity[1]);
    if(!s->spin_start){
        int far=s->target<0 || Psyz_Distance(ps->origin,g_entities[s->target].r.currentOrigin)>400;
        if(!(forced && !s->spin_probe && speed>250) && !(now>=s->spin_cooldown && speed>360 && far && s->strafe_until-now>950))return;
        s->spin_start=now;s->spin_cooldown=now+20000;s->spin_probe=forced;
        s->spin_yaw=(cmd->angles[1]+ps->delta_angles[1])*360.f/65536.f;
        fprintf(stderr,"PSYZ_V2_SPIN_BEGIN slot=%d t=%d duration=950 source=owner_pov_template lab_probe=%d\n",own->s.number,now,forced);
    }
    int elapsed=now-s->spin_start;if(elapsed<0){s->spin_start=0;return;}
    float sample=fminf(38,elapsed/25.f);int index=(int)sample;
    float offset=psyz_v2_spin_yaw[index];if(index<38)offset+=(psyz_v2_spin_yaw[index+1]-offset)*(sample-index);
    float previous=(cmd->angles[1]+ps->delta_angles[1])*360.f/65536.f;
    float view=s->spin_yaw+offset,rotation=(view-previous)*.01745329252f;
    float f=cmd->forwardmove*cosf(rotation)-cmd->rightmove*sinf(rotation),r=cmd->forwardmove*sinf(rotation)+cmd->rightmove*cosf(rotation);
    /* PM_CmdScale uses max-axis magnitude: retain it as well as world direction. */
    float maximum=fmaxf(abs(cmd->forwardmove),abs(cmd->rightmove)),new_max=fmaxf(fabsf(f),fabsf(r));
    float scale=new_max>.01f?maximum/new_max:0;
    cmd->forwardmove=(signed char)(f*scale);cmd->rightmove=(signed char)(r*scale);
    cmd->angles[1]=(int)(view*65536.f/360.f)-ps->delta_angles[1];
    if(elapsed>=950){fprintf(stderr,"PSYZ_V2_SPIN_END slot=%d t=%d outcome=completed degrees=360\n",own->s.number,now);s->spin_start=0;}
}
static void Psyz_V2Pickup(gentity_t *item,gentity_t *own,int now){
    if(!Psyz_V2Enabled() || !Psyz_IsOurBot(own) || own->s.number<0 || own->s.number>=64)return;
    PsyzV2State *s=&psyz_v2[own->s.number];
    if(s->jump>=0 && s->target==item->s.number)s->picked_at=now;
    if(s->tp_active && s->target==item->s.number && !strcmp(item->item->classname,"item_armor_body")){s->tp_picked=now;
        fprintf(stderr,"PSYZ_V2_TP_PICKUP slot=%d t=%d entity=%d elapsed=%d\n",own->s.number,now,item->s.number,now-s->tp_since);}
    fprintf(stderr,"PSYZ_V2_PICKUP slot=%d t=%d entity=%d class=%s target=%d jump=%d hp=%d armor=%d\n",own->s.number,now,item->s.number,item->item->classname,s->target,s->jump,own->health,own->client->ps.stats[STAT_ARMOR]);
    if(s->jump<0 && s->target==item->s.number)s->target=-1;
}
