/* Owner-console-only combat fixture. Never active on training/public ports.
 * Position/inventory writes occur once per requested empty-LAB initial state;
 * switching, shot cooldown and damage then execute in normal game physics.
 */
static int psyz_v2_combat_probe,psyz_v2_combat_probe_at,psyz_v2_combat_probe_slot=-1;
static int psyz_v2_combat_target=-1,psyz_v2_combat_log;
static int Psyz_V2CombatProbeRequested(void){
    cvar_t *v=Cvar_FindVar("qlx_psyzV2CombatProbe");
    return Psyz_V2Enabled() && Psyz_V2LabEmpty() && v && (v->integer==1 || v->integer==2)?v->integer:0;
}
static void Psyz_V2CombatProbePreCommand(gentity_t *own){
    if(!Psyz_V2CombatProbeRequested() || !Psyz_IsOurBot(own) || own->s.number!=psyz_v2_combat_probe_slot)return;
    int now=own->client->pers.cmd.serverTime;
    if(now>=psyz_v2_combat_probe_at && now-psyz_v2_combat_probe_at<=4500){
        Psyz_V2View(&own->client->pers.cmd,&own->client->ps,0,180);own->client->pers.cmd.buttons|=1;
    }
}
static void Psyz_V2CombatProbeCommand(gentity_t *own){
    int request=Psyz_V2CombatProbeRequested();
    if(!request){psyz_v2_combat_probe=0;return;}
    if(!Psyz_IsOurBot(own))return;
    playerState_t *ps=&own->client->ps;usercmd_t *cmd=&own->client->pers.cmd;int now=cmd->serverTime;
    if(psyz_v2_combat_probe!=request){
        gentity_t *other=NULL;
        for(int i=0;i<64;i++)if(g_entities[i].inuse && g_entities[i].client && g_entities[i].health>0 && g_entities[i].client->ps.pm_type==0 && (g_entities[i].r.svFlags&8) && !Psyz_IsOurBot(&g_entities[i])){other=&g_entities[i];break;}
        if(!other)return;
        const float start[3]={600,-112,536.125f};float target[3]={250,-112,536.125f};
        if(request==2)target[0]=530;
        memcpy(ps->origin,start,12);memcpy(own->r.currentOrigin,start,12);memset(ps->velocity,0,12);
        memcpy(other->client->ps.origin,target,12);memcpy(other->r.currentOrigin,target,12);memset(other->client->ps.velocity,0,12);
        own->health=ps->stats[STAT_HEALTH]=200;ps->stats[STAT_ARMOR]=150;
        other->health=other->client->ps.stats[STAT_HEALTH]=200;other->client->ps.stats[STAT_ARMOR]=0;
        ps->stats[STAT_WEAPONS]|=(1<<3)|(1<<5)|(1<<6)|(1<<7);ps->ammo[3]=10;ps->ammo[5]=20;ps->ammo[6]=100;ps->ammo[7]=10;
        ps->weapon=7;ps->weaponTime=0;
        Psyz_Finish087Reset();psyz_v2_combat_probe=request;psyz_v2_combat_probe_at=now;psyz_v2_combat_probe_slot=own->s.number;
        psyz_v2_combat_target=other->s.number;psyz_v2_combat_log=0;
        fprintf(stderr,"PSYZ_V2_COMBAT_PROBE slot=%d t=%d type=%d range=%d empty_lab=1 initial_state_only=1\n",own->s.number,now,request,request==2?70:350);
    }
    if(own->s.number!=psyz_v2_combat_probe_slot || now<psyz_v2_combat_probe_at || now-psyz_v2_combat_probe_at>4500)return;
    cmd->forwardmove=cmd->rightmove=cmd->upmove=0;Psyz_V2View(cmd,ps,0,180);cmd->buttons|=1;
    if(now-psyz_v2_combat_probe_at<100)cmd->buttons&=~1; /* Let both relocated entities relink before the seed shot. */
    /* Seed one real Rail shot. Thereafter the normal V2 lease owns selection. */
    if(ps->ammo[7]>=10)cmd->weapon=7;
    if(now-psyz_v2_combat_log>=500 && psyz_v2_combat_target>=0 && psyz_v2_combat_target<64){
        psyz_v2_combat_log=now;gentity_t *e=&g_entities[psyz_v2_combat_target];
        fprintf(stderr,"PSYZ_V2_COMBAT_FIXTURE t=%d target_slot=%d hp=%d pos=%.2f,%.2f,%.2f linked=%.2f,%.2f,%.2f range=%.2f weapon=%d\n",now,e->s.number,e->health,e->client->ps.origin[0],e->client->ps.origin[1],e->client->ps.origin[2],e->r.currentOrigin[0],e->r.currentOrigin[1],e->r.currentOrigin[2],Psyz_Distance(ps->origin,e->client->ps.origin),ps->weapon);
    }
}
static int Psyz_V2CombatProbePauseOther(gentity_t *ent){
    if(!Psyz_V2Enabled() || !Psyz_V2LabEmpty() || Psyz_IsOurBot(ent) || !ent || !ent->inuse || !ent->client || !(ent->r.svFlags&8))return 0;
    cvar_t *move=Cvar_FindVar("qlx_psyzV2MoveProbe");int active=Psyz_V2CombatProbeRequested() || (move && move->integer>0);
    for(int i=0;i<64;i++)if(psyz_v2[i].jump>=0 && psyz_v2[i].jump_probe_active)active=1;
    if(!active)return 0;
    usercmd_t *cmd=&ent->client->pers.cmd;cmd->buttons=ent->health<=0?1:0;cmd->forwardmove=cmd->rightmove=cmd->upmove=0;return 1;
}
