#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
#include <iostream>
struct cvar_t { int integer; };
static cvar_t test{1}, port{27961}, mode{3};
static bool missing=false;
static const char* optin=nullptr;
static void* qagame=nullptr;
static int calls=0, hooks=0, hook_error=0, original_result=1;
static void* seen_state=nullptr;
static int seen_flags=0;
static cvar_t* Cvar_FindVar(const char* name) {
    if(missing) return nullptr;
    return !std::strcmp(name,"qlx_psyzTestInstance")?&test:
           !std::strcmp(name,"net_port")?&port:&mode;
}
static const char* test_getenv(const char*) { return optin; }
static int original(void* state,int flags,void* goal) {
    ++calls;seen_state=state;seen_flags=flags;
    if(goal && original_result) std::memset(goal,0xa5,48);
    return original_result;
}
static int Hook(void*,int(*)(void*,int,void*),void* trampoline) {
    ++hooks;
    if(!hook_error) *static_cast<int(**)(void*,int,void*)>(trampoline)=original;
    return hook_error;
}
#define getenv test_getenv
#include "../adapter/native/psyz_stock_goal_observer.h"
#undef getenv
int main() {
    int failures=0;
    auto check=[&](bool condition,const char* why){if(!condition){++failures;std::cerr<<why<<'\n';}};
    std::vector<unsigned char> binary(0x2c940,0);
    qagame=binary.data();
    const unsigned char fingerprint[]={0x41,0x56,0x41,0x89,0xf6,0x48,0x89,0xd6,0x41,0x55,0x41,0x54,0x49,0x89,0xd4,0x55};
    std::memcpy(binary.data()+0x2c920,fingerprint,16);
    check(!Psyz_InstallGoalObserver() && hooks==0,"default opt-out");
    optin="1";port.integer=27960;
    check(!Psyz_InstallGoalObserver() && hooks==0,"main server rejected");
    port.integer=27961;test.integer=0;
    check(!Psyz_InstallGoalObserver() && hooks==0,"unmarked runtime rejected");
    test.integer=1;mode.integer=2;
    check(!Psyz_InstallGoalObserver() && hooks==0,"command override mode rejected");
    mode.integer=3;missing=true;
    check(!Psyz_InstallGoalObserver() && hooks==0,"missing cvars rejected");
    missing=false;binary[0x2c920]=0;
    check(!Psyz_InstallGoalObserver() && hooks==0,"wrong entry rejected");
    binary[0x2c920]=fingerprint[0];hook_error=7;
    check(!Psyz_InstallGoalObserver() && !psyz_original_item_goal,"hook error stays inactive");
    hook_error=0;
    check(Psyz_InstallGoalObserver() && hooks==2,"valid test entry installed");
    check(Psyz_InstallGoalObserver() && hooks==2,"installation idempotent");
    unsigned char state[16]={},before[16]={},goal[64]={};
    check(Psyz_ObserveItemGoal(state,123,goal)==1 && calls==1,"original once/result preserved");
    check(seen_state==state && seen_flags==123,"arguments preserved");
    check(!std::memcmp(state,before,16),"state not modified");
    for(int i=0;i<64;++i)check(goal[i]==(i<48?0xa5:0),"observer does not modify goal");
    original_result=0;
    check(Psyz_ObserveItemGoal(state,0,nullptr)==0 && calls==2,"no-result/null output passed through");
    original_result=37;mode.integer=0;
    auto count=psyz_goal_observations;
    check(Psyz_ObserveItemGoal(state,0,goal)==37 && calls==3,"disabled observer keeps stock result");
    check(psyz_goal_observations==count,"disabled observer does not record");
    return failures?1:0;
}
