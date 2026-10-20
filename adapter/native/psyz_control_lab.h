/* Test-only command hook for the pinned Linux QL build. Not a general ABI. */
#include <stddef.h>
#include "psyz_prealpha.h"
#define PSYZ_PREALPHA 1
#include "psyz_stock_goal_observer.h"
#include "psyz_live_combat.h"
static void (*psyz_real_think)(gentity_t*);
static int psyz_started = -1;
static int psyz_last_log = -1;
static void Psyz_Think(gentity_t* ent) {
    /* Independent finisher does not enable the legacy route/aim policy. */
    Psyz_Finish087Command(ent);
    cvar_t *test = Cvar_FindVar("qlx_psyzTestInstance");
    cvar_t *mode = Cvar_FindVar("qlx_psyzControlMode");
    cvar_t *port = Cvar_FindVar("net_port");
    if (!test || test->integer != 1 || !mode || (mode->integer != 1 && mode->integer != 2 && mode->integer != 3) ||
        !port || port->integer != 27961 || !Psyz_IsOurBot(ent) ||
        !(ent->r.svFlags & 8) || !ent->client || ent->health <= 0) {
        if (!mode || mode->integer == 0) psyz_started = -1;
        if(Psyz_IsOurBot(ent) && ent->health<=0){
            psyz_rj=-1;
            if(Psyz_PreAlphaEnabled() && ent->client)Psyz_OpeningEnd(ent->client->pers.cmd.serverTime,"death");
            psyz_goal_target=psyz_active_route=psyz_rj_plan=-1;
        }
        psyz_real_think(ent); return;
    }
    usercmd_t *cmd = &ent->client->pers.cmd;
    int now = cmd->serverTime;
    if (mode->integer == 3) {
        /* Install lazily: custom cvars may not exist during VM load. */
        Psyz_InstallGoalObserver();
        /* Preserve stock AAS; explicitly enabled prealpha may alter this bot. */
        Psyz_PreAlphaMove(ent);
        Psyz_LiveCombatCommand(ent);
        psyz_real_think(ent);
        if (now - psyz_last_log >= 200) {
            psyz_last_log = now;
            // Отличаем отсутствие движения при намерении идти от ожидания/боя.
            // Скорость ps сама по себе не доказывает перемещение между кадрами.
            fprintf(stderr,"PSYZ_NAV t=%d pos=%.3f,%.3f,%.3f vel=%.3f,%.3f,%.3f yaw=%.2f weapon=%d health=%d ground=%d source=stock_aas_plus_optin_prealpha forward=%d right=%d up=%d buttons=%d target=%d route=%d armor=%d escape=%d pmtype=%d\n",
                now,ent->client->ps.origin[0],ent->client->ps.origin[1],ent->client->ps.origin[2],
                ent->client->ps.velocity[0],ent->client->ps.velocity[1],ent->client->ps.velocity[2],
                ent->client->ps.viewangles[1],ent->client->ps.weapon,ent->health,ent->client->ps.groundEntityNum,
                cmd->forwardmove,cmd->rightmove,cmd->upmove,cmd->buttons,psyz_goal_target,psyz_active_route,
                ent->client->ps.stats[STAT_ARMOR],now<psyz_stock_escape_until,ent->client->ps.pm_type);
        }
        return;
    }
    if (psyz_started < 0) psyz_started = now;
    int elapsed = now - psyz_started;
    int cycle = elapsed / 7000;
    if (mode->integer == 2 && elapsed >= 0) elapsed %= 7000;
    if (elapsed < 0 || (mode->integer == 1 && elapsed >= 5000)) { psyz_real_think(ent); return; }
    cmd->buttons = 0;
    cmd->forwardmove = elapsed >= 1000 && elapsed < 3000 ? 127 : 0;
    cmd->rightmove = 0;
    cmd->upmove = elapsed >= 2000 && elapsed < 2100 ? 127 : 0;
    cmd->weapon = ent->client->ps.weapon;
    for (int k=0;k<3;k++) cmd->angles[k] = -ent->client->ps.delta_angles[k];
    if (mode->integer == 2 && (cycle & 1)) cmd->angles[1] += 32768;
    float before[3]; memcpy(before,ent->client->ps.origin,sizeof(before));
    psyz_real_think(ent);
    if (now - psyz_last_log >= 100) {
        psyz_last_log = now;
        fprintf(stderr,"PSYZ_CONTROL t=%d elapsed=%d forward=%d up=%d before=%.3f,%.3f,%.3f after=%.3f,%.3f,%.3f angles=%.2f,%.2f ground=%d\n",
          now,elapsed,cmd->forwardmove,cmd->upmove,before[0],before[1],before[2],
          ent->client->ps.origin[0],ent->client->ps.origin[1],ent->client->ps.origin[2],
          ent->client->ps.viewangles[0],ent->client->ps.viewangles[1],ent->client->ps.groundEntityNum);
    }
}
static void Psyz_Install(void) {
    if (!getenv("PSYZ_CONTROL_LAB")) return;
    /* Old VM is unloaded here. Reuse only our successful VM-hook slots,
       leaving permanent engine hooks untouched. Full Python HookVm rewinds
       its own hooks after installation; our slots must rewind in both builds. */
    if(psyz_vm_hook_count && !seek_hook_slot(-psyz_vm_hook_count)){
        fprintf(stderr,"PSYZ_CONTROL refused: cannot rewind VM hooks\n");return;
    }
    psyz_vm_hook_count=0;
    /* Duel allready reloads qagame. Preserve only observed match phase,
       never pointers, cached goals or the previous opening plan. */
    Psyz_PreAlphaVmReset();
    Psyz_LiveCombatReset();
    Psyz_Finish087Reset();
    Psyz_InstallPickup();
    Psyz_InstallDamageObserver();
    psyz_original_item_goal = NULL; /* VM reload invalidates the old trampoline. */
    /* Caller also verifies SHA256 of bin.pk3. Verify the target prologue here. */
    unsigned char expected[] = {0x41,0x57,0x41,0x56,0x41,0x55,0x41,0x54};
    void *target = (char*)qagame + 0x59df0;
    if (memcmp(target,expected,sizeof(expected)) || offsetof(gclient_t,pers.cmd)!=0x254 || sizeof(usercmd_t)!=28) {
        fprintf(stderr,"PSYZ_CONTROL refused: ABI mismatch cmd=%zu offset=%zu\n",sizeof(usercmd_t),offsetof(gclient_t,pers.cmd));return;
    }
    Psyz_InstallGoalObserver();
    psyz_started = -1;
    int error = Hook(target,Psyz_Think,(void*)&psyz_real_think);
    if(!error)psyz_vm_hook_count++;
    fprintf(stderr,"PSYZ_CONTROL install=%d\n",error);
}
