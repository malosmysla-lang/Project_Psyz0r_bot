/* Pure C bounded route watchdog. No engine pointers or enemy information. */
typedef struct {
    int target,start,last,progress,paused,stage,waypoint,cell_count;
    int cells[32][3];
    float best_distance;
    int motion_since;
    float motion_position[3];
} PsyzNavRecovery;
static void Psyz_NavReset(PsyzNavRecovery *s) {
    memset(s,0,sizeof(*s));s->target=-1;s->waypoint=-1;
}
/* 0 continue, 1 retry stock AAS, 2 abandon. Holds have a total 5s budget. */
static int Psyz_NavUpdate(PsyzNavRecovery *s,int target,int now,const float *position,
                          float distance,int waypoint,int has_demo,int combat,int waiting) {
    if(target!=s->target || now<s->last){
        Psyz_NavReset(s);s->target=target;s->start=s->progress=s->last=now;
        s->best_distance=distance;
        s->motion_since=now;memcpy(s->motion_position,position,sizeof(s->motion_position));
    }
    int dt=now-s->last;s->last=now;
    if(target<0)return 0;
    if(now-s->start>=30000)return 2;
    if((combat || waiting) && dt>0 && s->paused<5000){
        int hold=dt;if(hold>5000-s->paused)hold=5000-s->paused;
        s->paused+=hold;s->progress+=hold;
    }
    int cell[3];for(int k=0;k<3;k++)cell[k]=(int)floorf(position[k]/64.f);
    int known=0;
    for(int i=0;i<s->cell_count;i++)if(!memcmp(s->cells[i],cell,sizeof(cell)))known=1;
    /* New territory counts as progress even when a valid detour goes away
       from the item. Revisiting the same cells does not reset the timer. */
    if(!known && s->cell_count<32){memcpy(s->cells[s->cell_count++],cell,sizeof(cell));s->progress=now;}
    if(distance<s->best_distance-32){s->best_distance=distance;s->progress=now;}
    if(waypoint>s->waypoint){s->waypoint=waypoint;s->progress=now;s->motion_since=now;}
    float moved=0;for(int k=0;k<3;k++){float delta=position[k]-s->motion_position[k];moved+=delta*delta;}
    // Близость к предмету сама по себе не доказывает подбор: можно стоять
    // под платформой красного. Только реальное движение или ограниченное
    // ожидание таймера защищают остановку от восстановления маршрута.
    if(moved>64 || combat || waiting){
        s->motion_since=now;memcpy(s->motion_position,position,sizeof(s->motion_position));
    }else if(now-s->motion_since>=1500){
        s->motion_since=now;s->progress=now;
        if(has_demo && !s->stage){s->stage=1;return 1;}
        return 2;
    }
    if(now-s->progress<=6000)return 0;
    if(has_demo && !s->stage){s->stage=1;s->progress=now;return 1;}
    return 2;
}
