#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cstddef>
#include <cmath>
#include <stdexcept>
#include <iostream>
// A small ABI-independent world. Retail ABI is separately fingerprinted on Linux.
enum {STAT_HEALTH,STAT_HOLDABLE_ITEM,STAT_RUNE,STAT_WEAPONS,STAT_ARMOR};
struct usercmd_t {int serverTime,buttons,angles[3];unsigned char weapon;signed char forwardmove,rightmove,upmove;};
struct playerState_t {float origin[3],velocity[3],viewangles[3];int delta_angles[3],stats[18],ammo[16],groundEntityNum,weapon,weaponTime;};
struct Client {playerState_t ps;struct {usercmd_t cmd;} pers;};
struct gitem_t {const char *classname,*pickup_name;int giTag;};
struct gentity_t {int inuse,health,nextthink;struct {int number,modelindex;} s;struct {int svFlags,contents;float currentOrigin[3];} r;gitem_t *item;Client *client;};
struct trace_t {};
struct cvar_t {int integer;const char *string;};
static gentity_t world[1024];static gentity_t *g_entities=world;
static unsigned char game_memory[0x2d8010],imports_memory[0x600];static void *qagame=game_memory;
static cvar_t enabled{1,"1"},mapvar{0,"bloodrun"},testvar{1,"1"},portvar{27961,"27961"};
static cvar_t openingvar{0,"0"},phasevar{0,"PRE_GAME"};
static cvar_t combatvar{0,"0"},aimvar{0,"0"};
static cvar_t preparevar{0,"0"};
static cvar_t *Cvar_FindVar(const char *name){return !strcmp(name,"qlx_psyzLoadoutPreparation")?&preparevar:!strcmp(name,"qlx_psyzAimHumanize")?&aimvar:!strcmp(name,"qlx_psyzGroundCombat")?&combatvar:!strcmp(name,"qlx_psyzOpening")?&openingvar:!strcmp(name,"g_gameState")?&phasevar:!strcmp(name,"qlx_psyzPreAlpha")?&enabled:!strcmp(name,"mapname")?&mapvar:!strcmp(name,"qlx_psyzTestInstance")?&testvar:!strcmp(name,"net_port")?&portvar:nullptr;}
static int Hook(void*,void(*)(gentity_t*,gentity_t*,trace_t*),void*){return 0;}
#include "../adapter/native/psyz_prealpha.h"
static void check(bool v,const char *message){if(!v)throw std::runtime_error(message);}
static unsigned char pushed[64];
static void pop(int){}
static void push(int,void *p){memcpy(pushed,p,64);}
static int registry_ready;static unsigned char late_goal[64];
static int get_item(int cursor,const char *name,void *out){
 if(registry_ready && cursor<0 && !strcmp(name,"Heavy Armor")){memcpy(out,late_goal,64);return 1;}
 return -1;
}
static Client client;
static gitem_t red{"item_armor_body","Heavy Armor",0},mega{"item_health_mega","Mega Health",0};
static void reset(){
 memset(world,0,sizeof(world));memset(&client,0,sizeof(client));Psyz_PreAlphaReset();enabled.integer=1;
 openingvar.integer=0;phasevar.string="PRE_GAME";portvar.integer=27961;
 registry_ready=0;combatvar.integer=0;aimvar.integer=0;preparevar.integer=0;
 world[0].client=&client;world[0].inuse=1;world[0].health=100;world[0].r.svFlags=8;
 client.ps.groundEntityNum=1022;client.pers.cmd.serverTime=20000;
 void *im=imports_memory;memcpy(game_memory+0x2d8000,&im,sizeof(im));
 auto p=pop;auto u=push;auto g=get_item;memcpy(imports_memory+0x468,&p,sizeof(p));memcpy(imports_memory+0x460,&u,sizeof(u));memcpy(imports_memory+0x4d0,&g,sizeof(g));
}
static void goal(unsigned char *out,int id,int area,const float *position){memset(out,0,64);memcpy(out,position,12);memcpy(out+12,&area,4);memcpy(out+40,&id,4);int flags=1;memcpy(out+48,&flags,4);}
int main(){try{
 reset();world[200].item=&red;world[200].inuse=1;world[200].r.contents=1;
 client.ps.stats[STAT_ARMOR]=190;
 check(Psyz_ItemWeight(&world[200],&world[0],0)<10,"Do not chase redundant armor at full stack");
 world[200].item=&mega;world[0].health=50;client.ps.stats[STAT_ARMOR]=0;
 check(Psyz_ItemWeight(&world[200],&world[0],0)>100,"Mega is valuable below full health");

 // Exact opponent stack changes recovery choices; no opponent coordinates are supplied.
 reset();gitem_t yellow{"item_armor_combat","Armor",0};
 world[200].inuse=world[201].inuse=1;world[200].item=&mega;world[201].item=&yellow;
 world[200].r.contents=world[201].r.contents=1;world[200].r.currentOrigin[0]=world[201].r.currentOrigin[0]=100;
 client.ps.stats[STAT_ARMOR]=50;unsigned char state[0x1970]{},out[64];
 goal(out,200,10,world[200].r.currentOrigin);goal(psyz_goal_cache[201],201,10,world[201].r.currentOrigin);psyz_goal_known[201]=1;psyz_debug_logged=1;
 Psyz_PreAlphaGoal(state,0,out);check(psyz_goal_target==200,"At adequate stack prefer Mega");
 Client enemy{};world[1].inuse=1;world[1].client=&enemy;world[1].health=200;enemy.ps.stats[STAT_ARMOR]=200;
 psyz_goal_target=-1;goal(out,200,10,world[200].r.currentOrigin);Psyz_PreAlphaGoal(state,0,out);
 check(psyz_goal_target==201,"Outstacked bot should recover on yellow armor");
 // Entity IDs change between FFA and Duel; position and class must retain the route.
 const auto &r=psyz_routes[0];gitem_t mapped{r.classname,"test",0};world[333].item=&mapped;
 memcpy(world[333].r.currentOrigin,r.target,12);memcpy(client.ps.origin,r.points[0].p,12);
 Psyz_SelectDemoRoute(&world[0],333);check(psyz_active_route>=0,"Route should survive entity renumbering");
 reset();const auto &jump=psyz_jumps[0];memcpy(client.ps.origin,jump.start,12);world[200].item=&red;
 memcpy(world[200].r.currentOrigin,jump.landing,12);psyz_goal_target=200;client.ps.stats[STAT_WEAPONS]=1<<5;
 client.ps.weapon=5;client.ps.ammo[5]=0;psyz_last_move_time=19975;
 Psyz_PreAlphaMove(&world[0]);check(psyz_rj<0,"No rocket jump without ammunition");
 client.ps.ammo[5]=5;world[0].health=200;client.pers.cmd.serverTime+=25;Psyz_PreAlphaMove(&world[0]);
 check(psyz_rj>=0,"Valid recorded launch point should begin jump");
 client.ps.velocity[1]=320;client.pers.cmd.serverTime+=25;Psyz_PreAlphaMove(&world[0]);
 int start=psyz_rj_time;client.pers.cmd.serverTime=start+jump.shot_delay+25;psyz_last_move_time=client.pers.cmd.serverTime-25;
 Psyz_PreAlphaMove(&world[0]);check(client.pers.cmd.buttons&1,"A late frame must still issue the rocket shot");
 client.pers.cmd.serverTime+=25;Psyz_PreAlphaMove(&world[0]);check(!(client.pers.cmd.buttons&1),"Recorded jump must not spam rockets");
 reset();client.pers.cmd.upmove=-127;psyz_last_move_time=19975;Psyz_PreAlphaMove(&world[0]);check(client.pers.cmd.upmove==0,"Crouch disabled by default");
 enabled.integer=0;client.pers.cmd.upmove=-127;client.pers.cmd.serverTime+=25;Psyz_PreAlphaMove(&world[0]);check(client.pers.cmd.upmove==-127,"Disabled policy preserves stock commands");
 // Attach-in-progress is not a new opening. A real phase transition is required.
 reset();openingvar.integer=1;phasevar.string="IN_PROGRESS";
 Psyz_OpeningTick(&world[0]);check(!psyz_opening_active,"No invented opening on midgame attach");
 phasevar.string="PRE_GAME";Psyz_OpeningTick(&world[0]);
 psyz_goal_known[210]=1;psyz_goal_target=210;
 Psyz_PreAlphaVmReset();
 check(psyz_opening_seen && !psyz_opening_playing && !psyz_goal_known[210] && psyz_goal_target<0,"VM reload retains phase but invalidates old goal pointers");
 phasevar.string="IN_PROGRESS";Psyz_OpeningTick(&world[0]);
 check(psyz_opening_active,"Warmup-to-match transition begins opening");
 const auto &op=psyz_openings[0];memcpy(client.ps.origin,op.start,12);
 gitem_t first_item{op.steps[0].classname,"opening",0};
 world[210].inuse=1;world[210].item=&first_item;world[210].r.contents=1;world[210].s.number=210;
 memcpy(world[210].r.currentOrigin,op.steps[0].position,12);psyz_goal_known[210]=1;
 check(Psyz_OpeningTarget(&world[0],0)==210,"Observed opening maps class and position to current entity");
 Psyz_OpeningPickup(&world[210],20001);check(psyz_opening_step==1,"Only actual matched pickup advances plan");
 Psyz_OpeningTarget(&world[0],1);check(!psyz_opening_active,"Recovery preempts opening");
 phasevar.string="PRE_GAME";Psyz_OpeningTick(&world[0]);phasevar.string="IN_PROGRESS";Psyz_OpeningTick(&world[0]);
 client.pers.cmd.serverTime+=30000;Psyz_OpeningTick(&world[0]);check(!psyz_opening_active,"Opening ends after 30 seconds");
 phasevar.string="PRE_GAME";Psyz_OpeningTick(&world[0]);phasevar.string="IN_PROGRESS";Psyz_OpeningTick(&world[0]);
 world[0].health=0;Psyz_OpeningTick(&world[0]);check(!psyz_opening_active,"Death does not replay opening on respawn");
 portvar.integer=27960;enabled.integer=1;check(!Psyz_PreAlphaEnabled(),"Policy must never activate on primary port");
 reset();world[200].inuse=1;world[200].item=&mega;world[200].r.contents=1;world[200].r.currentOrigin[0]=100;
 client.ps.stats[STAT_ARMOR]=50;psyz_debug_logged=1;
 goal(out,200,10,world[200].r.currentOrigin);goal(psyz_goal_cache[200],200,10,world[200].r.currentOrigin);
 psyz_goal_known[200]=1;psyz_goal_target=200;psyz_active_route=0;psyz_progress_time=0;psyz_goal_since=0;
 Psyz_PreAlphaGoal(state,0,out);
 check(psyz_goal_target==200 && psyz_active_route<0,"Failed demo approach retries same item with stock AAS");
 check(psyz_demo_retry_after[200]>20000 && psyz_route_banned[0]>20000,"Failed approach is not immediately reselected");
 client.pers.cmd.serverTime=27001;goal(out,200,10,world[200].r.currentOrigin);Psyz_PreAlphaGoal(state,0,out);
 check(psyz_goal_target<0 && psyz_banned[200]>27001,"A second no-progress timeout releases failed stock goal");
 reset();world[201].inuse=1;world[201].item=&red;world[201].r.contents=1;world[201].r.currentOrigin[0]=100;
 goal(late_goal,201,10,world[201].r.currentOrigin);psyz_debug_logged=1;psyz_registry_retry=20000;
 goal(out,201,10,world[201].r.currentOrigin);int bad_flags=0;memcpy(out+48,&bad_flags,4);
 Psyz_PreAlphaGoal(state,0,out);check(!psyz_goal_known[201],"Unavailable registry entry is not fabricated");
 registry_ready=1;client.pers.cmd.serverTime=21001;goal(out,201,10,world[201].r.currentOrigin);memcpy(out+48,&bad_flags,4);
 Psyz_PreAlphaGoal(state,0,out);check(psyz_goal_known[201],"Late stock red goal is discovered on retry");
 reset();combatvar.integer=1;psyz_last_move_time=19975;client.pers.cmd.buttons=1;client.pers.cmd.upmove=127;
 Psyz_PreAlphaMove(&world[0]);check(client.pers.cmd.upmove==0,"Ground combat blocks new jump");
 client.pers.cmd.serverTime+=50;client.pers.cmd.buttons=0;client.pers.cmd.upmove=127;
 Psyz_PreAlphaMove(&world[0]);check(client.pers.cmd.upmove==0,"Ground combat persists between shots");
 client.pers.cmd.serverTime+=50;client.ps.groundEntityNum=1023;client.pers.cmd.upmove=127;
 Psyz_PreAlphaMove(&world[0]);check(client.pers.cmd.upmove==127,"Combat gate does not rewrite existing flight");
 client.pers.cmd.serverTime+=1500;psyz_last_move_time=client.pers.cmd.serverTime-25;client.ps.groundEntityNum=1022;client.pers.cmd.upmove=127;
 Psyz_PreAlphaMove(&world[0]);check(client.pers.cmd.upmove==127,"Combat hold expires outside firing");
 reset();gitem_t rocket{"weapon_rocketlauncher","Rocket Launcher",5};world[200].item=&rocket;
 client.ps.stats[STAT_WEAPONS]=1<<5;client.ps.ammo[5]=0;
 check(Psyz_ItemWeight(&world[200],&world[0],0)==180,"Empty rocket launcher is not ready");
 client.ps.ammo[5]=5;check(Psyz_ItemWeight(&world[200],&world[0],0)==8,"Armed rocket no longer missing");
 reset();aimvar.integer=1;usercmd_t shot{};shot.buttons=1;
 Psyz_HumanizeAim(&shot,7,20100);check(shot.angles[0]==0 && shot.angles[1]==0,"Rail aim unchanged");
 shot.weapon=6;Psyz_HumanizeAim(&shot,6,20100);check(shot.angles[0]!=0 || shot.angles[1]!=0,"LG aim error applied");
 check(std::abs(shot.angles[0])<=228 && std::abs(shot.angles[1])<=228,"LG angular error bounded");
 usercmd_t before{},after{};before.buttons=after.buttons=1;before.weapon=after.weapon=8;Psyz_HumanizeAim(&before,8,20159);Psyz_HumanizeAim(&after,8,20160);
 check(std::abs(before.angles[0]-after.angles[0])<10 && std::abs(before.angles[1]-after.angles[1])<10,"Aim interpolation continuous across noise boundary");
 shot={};Psyz_HumanizeAim(&shot,8,20100);check(shot.angles[0]==0 && shot.angles[1]==0,"Non-firing navigation aim unchanged");
 reset();world[200].inuse=1;world[200].item=&mega;world[200].r.contents=1;world[200].r.currentOrigin[0]=300;
 world[201].inuse=1;world[201].item=&rocket;world[201].r.contents=1;world[201].r.currentOrigin[0]=80;
 goal(psyz_goal_cache[200],200,10,world[200].r.currentOrigin);psyz_goal_known[200]=1;
 goal(psyz_goal_cache[201],201,10,world[201].r.currentOrigin);psyz_goal_known[201]=1;
 psyz_goal_target=200;psyz_goal_since=20000;psyz_debug_logged=1;client.ps.stats[STAT_ARMOR]=50;
 goal(out,200,10,world[200].r.currentOrigin);Psyz_PreAlphaGoal(state,0,out);
 check(psyz_goal_target==201,"Nearby missing main weapon interrupts retained resource target");
 reset();combatvar.integer=1;preparevar.integer=1;psyz_last_move_time=19975;
 client.pers.cmd.buttons=1;client.pers.cmd.forwardmove=127;client.pers.cmd.rightmove=64;
 Psyz_PreAlphaMove(&world[0]);
 check(client.pers.cmd.forwardmove==0 && client.pers.cmd.rightmove==64 && (client.pers.cmd.buttons&1),"Unarmed bot defends without voluntary forward push");
 client.ps.stats[STAT_WEAPONS]=(1<<5)|(1<<6);client.ps.ammo[5]=3;client.ps.ammo[6]=40;
 client.pers.cmd.serverTime+=25;client.pers.cmd.forwardmove=127;Psyz_PreAlphaMove(&world[0]);
 check(client.pers.cmd.forwardmove==127,"Two adequately supplied main weapons permit stock push");
 client.ps.ammo[6]=1;check(Psyz_TrinityReady(client.ps.stats[STAT_WEAPONS],client.ps.ammo)==1,"Last LG cell is not a full combat reserve");
 check(Psyz_AmmoNeed(client.ps.stats[STAT_WEAPONS],client.ps.ammo,6)==125,"Low LG reserve prioritizes cells");
 check(Psyz_AmmoNeed(client.ps.stats[STAT_WEAPONS],client.ps.ammo,7)==0,"Do not chase ammo for unowned weapon");
 reset();combatvar.integer=1;client.ps.stats[STAT_ARMOR]=100;psyz_last_move_time=19975;
 Psyz_PreAlphaMove(&world[0]);client.ps.stats[STAT_ARMOR]=60;client.pers.cmd.serverTime+=25;client.pers.cmd.upmove=127;
 Psyz_PreAlphaMove(&world[0]);check(client.pers.cmd.upmove==0,"Armor-only damage triggers grounded combat");
 std::cout<<"Native prealpha contextual scenarios passed\n";return 0;
 }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}}
