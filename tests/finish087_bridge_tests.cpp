#include <cstdio>
#include <cstring>
#include <cmath>
#include <cassert>
#define STAT_ARMOR 0
#define STAT_WEAPONS 1
#define MOD_GAUNTLET 1
#define MOD_LIGHTNING 6
#define MOD_RAILGUN 7
struct cvar_t{int integer;};
struct usercmd_t{int serverTime,angles[3],buttons;unsigned char weapon;};
struct playerState_t{int weapon,stats[4],ammo[16];float origin[3];};
struct Client{struct {usercmd_t cmd;} pers;playerState_t ps;};
struct gentity_t{int health;struct {int number;} s;Client *client;bool ours;};
static int port=27962,enabled=1;
static cvar_t *Cvar_FindVar(const char *name){static cvar_t p,t,e;p.integer=port;t.integer=1;e.integer=enabled;return !strcmp(name,"net_port")?&p:!strcmp(name,"qlx_psyzFinish087")?&e:&t;}
static int Psyz_IsOurBot(const gentity_t *e){return e && e->ours;}
static float Psyz_Distance(const float *a,const float *b){return std::sqrt((a[0]-b[0])*(a[0]-b[0])+(a[1]-b[1])*(a[1]-b[1])+(a[2]-b[2])*(a[2]-b[2]));}
#include "../adapter/native/psyz_finish087.h"
int main(){
 Client a{},b{},v{};
 gentity_t one{100,{0},&a,true},two{100,{1},&b,true},victim{60,{2},&v,false};
 a.ps.weapon=b.ps.weapon=6;a.ps.stats[STAT_WEAPONS]=b.ps.stats[STAT_WEAPONS]=(1<<7);a.ps.ammo[7]=b.ps.ammo[7]=10;
 a.pers.cmd.serverTime=b.pers.cmd.serverTime=1000;a.pers.cmd.buttons=b.pers.cmd.buttons=1;
 a.pers.cmd.weapon=b.pers.cmd.weapon=6;v.ps.origin[0]=450;
 Psyz_Finish087Reset();Psyz_Finish087Hit(&victim,&one,100,MOD_LIGHTNING);
 Psyz_Finish087Command(&two);assert(b.pers.cmd.weapon==6);
 Psyz_Finish087Command(&one);assert(a.pers.cmd.weapon==7);
 // An old contact cannot bleed into a second command or a different bot.
 a.pers.cmd.weapon=6;Psyz_Finish087Command(&one);assert(a.pers.cmd.weapon==6);
 Psyz_Finish087Hit(&victim,&one,100,MOD_LIGHTNING);port=27960;
 Psyz_Finish087Command(&one);assert(a.pers.cmd.weapon==6);
 port=27962;enabled=0;Psyz_Finish087Command(&one);assert(a.pers.cmd.weapon==6);
 std::puts("Finish087 two-bot isolation, consume-once and primary-port guards passed");
}
