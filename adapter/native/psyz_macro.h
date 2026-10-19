/* Bounded resource policy; no hidden enemy positions or invented safe cover. */
enum {PSYZ_MACRO_RECOVER,PSYZ_MACRO_ANCHOR,PSYZ_MACRO_CYCLE};
static int Psyz_MacroMode(int health,int armor,int ready,int recovering){
    if(recovering || health<80 || ready==0)return PSYZ_MACRO_RECOVER;
    if(health>=120 && armor>=80 && ready>=2)return PSYZ_MACRO_CYCLE;
    return PSYZ_MACRO_ANCHOR;
}
static float Psyz_MacroWeight(int mode,const char *classname,float base){
    if(base<=15)return base; /* Never chase resources already not needed. */
    if(mode==PSYZ_MACRO_RECOVER){
        if(!strcmp(classname,"item_armor_combat"))return base*1.15f;
        if(!strncmp(classname,"item_health",11) && strcmp(classname,"item_health_mega"))return base*1.1f;
    }else if(mode==PSYZ_MACRO_CYCLE){
        if(!strcmp(classname,"item_armor_combat") || !strcmp(classname,"item_armor_shard"))return base*1.2f;
        if(!strncmp(classname,"ammo_",5))return base*1.1f;
    }
    return base;
}
