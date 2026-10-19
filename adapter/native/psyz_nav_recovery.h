/* Pure C bounded route watchdog. No engine pointers or enemy information. */
typedef struct {
    int target,start,last,progress,paused,stage,waypoint,cell_count;
    int cells[32][3];
    float best_distance;
    int motion_since;
    float motion_position[3];
} PsyzNavRecovery;
// Отдельный сторож движения не сбрасывается при смене item-цели.
// Иначе чередование целей каждые 1-2с скрывает реальную остановку у стены.
typedef struct {int since,last,hold;float origin[3];} PsyzMotionWatch;
// Штатный AAS тоже может упереться в стену без нашей item-цели.
// При этом неподвижный прицельный бой без команды движения — не маршрутный тупик.
static int Psyz_MotionExpected(int alive,int learned_jump,int target,int forward,int right){
    return alive && !learned_jump && (target>=0 || forward!=0 || right!=0);
}
static void Psyz_MotionReset(PsyzMotionWatch *s){memset(s,0,sizeof(*s));s->last=-1;}
static int Psyz_MotionStalled(PsyzMotionWatch *s,int now,const float *position,int active,int hold){
    float distance=0;for(int k=0;k<3;k++){float d=position[k]-s->origin[k];distance+=d*d;}
    if(s->last<0 || now<s->last || now-s->last>500 || !active || distance>32*32){
        s->since=now;s->hold=0;memcpy(s->origin,position,sizeof(s->origin));s->last=now;return 0;
    }
    int dt=now-s->last;s->last=now;
    // Даже непрерывная стрельба не прячет неподвижность бесконечно.
    if(hold && s->hold<4000){int pause=dt;if(pause>4000-s->hold)pause=4000-s->hold;s->since+=pause;s->hold+=pause;}
    if(now-s->since<1800)return 0;
    s->since=now;return 1;
}
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
