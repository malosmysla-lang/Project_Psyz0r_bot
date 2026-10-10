/* Test-only command hook for the pinned Linux QL build. Not a general ABI. */
#include <stddef.h>
static void (*psyz_real_think)(gentity_t*);
static int psyz_started = -1;
static int psyz_last_log = -1;
static void Psyz_Think(gentity_t* ent) {
    cvar_t *test = Cvar_FindVar("qlx_psyzTestInstance");
    cvar_t *mode = Cvar_FindVar("qlx_psyzControlMode");
    cvar_t *port = Cvar_FindVar("net_port");
    if (!test || test->integer != 1 || !mode || (mode->integer != 1 && mode->integer != 2) ||
        !port || port->integer != 27961 || !ent || ent->s.number != 0 ||
        !(ent->r.svFlags & 8) || !ent->client || ent->health <= 0) {
        if (!mode || mode->integer == 0) psyz_started = -1;
        psyz_real_think(ent); return;
    }
    usercmd_t *cmd = &ent->client->pers.cmd;
    int now = cmd->serverTime;
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
    /* Caller also verifies SHA256 of bin.pk3. Verify the target prologue here. */
    unsigned char expected[] = {0x41,0x57,0x41,0x56,0x41,0x55,0x41,0x54};
    void *target = (char*)qagame + 0x59df0;
    if (memcmp(target,expected,sizeof(expected)) || offsetof(gclient_t,pers.cmd)!=0x254 || sizeof(usercmd_t)!=28) {
        fprintf(stderr,"PSYZ_CONTROL refused: ABI mismatch cmd=%zu offset=%zu\n",sizeof(usercmd_t),offsetof(gclient_t,pers.cmd));return;
    }
    psyz_started = -1;
    int error = Hook(target,Psyz_Think,(void*)&psyz_real_think);
    fprintf(stderr,"PSYZ_CONTROL install=%d\n",error);
}
