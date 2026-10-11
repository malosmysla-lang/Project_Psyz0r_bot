/* Read-only diagnostic hook, only for the pinned test QL binary.
 * Caller provides qagame, Cvar_FindVar and Hook from the lab minqlx build.
 * No bot_state layout or goal fields are assumed. No goals/commands are written.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
static int (*psyz_original_item_goal)(void*, int, void*);
static unsigned long long psyz_goal_observations;
static int Psyz_GoalObserverEnabled(void) {
    cvar_t *test_var = Cvar_FindVar("qlx_psyzTestInstance");
    cvar_t *port_var = Cvar_FindVar("net_port");
    cvar_t *mode_var = Cvar_FindVar("qlx_psyzControlMode");
    return test_var && test_var->integer == 1 && port_var && port_var->integer == 27961 &&
           mode_var && mode_var->integer == 3;
}
static int Psyz_ObserveItemGoal(void *state, int travel_flags, void *goal) {
    /* Exactly one original call, preserving its arguments and result. */
    int result = psyz_original_item_goal(state, travel_flags, goal);
    if (result && goal && Psyz_GoalObserverEnabled()) {
        unsigned long long sequence = ++psyz_goal_observations;
        /* A bounded prefix only. Layout remains unverified; never cast to Q3 goal. */
        if ((sequence-1) % 16 == 0) {
            unsigned char bytes[48];
            char hex[97];
            static const char digits[] = "0123456789abcdef";
            memcpy(bytes, goal, sizeof(bytes));
            for (size_t i=0; i<sizeof(bytes); ++i) {
                hex[2*i] = digits[bytes[i] >> 4];
                hex[2*i+1] = digits[bytes[i] & 15];
            }
            hex[96] = 0;
            fprintf(stderr,"PSYZ_STOCK_GOAL sequence=%llu state=%p travel_flags=%d result=%d prefix48=%s source=stock_ltg layout=unverified\n",
                    sequence,state,travel_flags,result,hex);
        }
    }
    return result;
}
static int Psyz_InstallGoalObserver(void) {
    /* Opt-in AND isolated test runtime; default remains completely inactive. */
    const char *enabled = getenv("PSYZ_STOCK_GOAL_OBSERVER");
    if (!enabled || strcmp(enabled,"1") || !Psyz_GoalObserverEnabled()) return 0;
    if (psyz_original_item_goal) return 1;
    /* qagame SHA256 must also be checked by prepare_control_lab.py --qagame.
     * This runtime fingerprint rejects changes to the intercepted entry. */
    static const unsigned char expected[16] = {
        0x41,0x56,0x41,0x89,0xf6,0x48,0x89,0xd6,
        0x41,0x55,0x41,0x54,0x49,0x89,0xd4,0x55
    };
    if (!qagame || memcmp((char*)qagame+0x2c920,expected,sizeof(expected))) {
        fprintf(stderr,"PSYZ_STOCK_GOAL refused: entry fingerprint mismatch\n");
        return 0;
    }
    int error = Hook((char*)qagame+0x2c920,Psyz_ObserveItemGoal,(void*)&psyz_original_item_goal);
    if (error) {
        psyz_original_item_goal = NULL;
        fprintf(stderr,"PSYZ_STOCK_GOAL refused: hook error=%d\n",error);
        return 0;
    }
    fprintf(stderr,"PSYZ_STOCK_GOAL installed: read_only=1 prefix_bytes=48 layout=unverified\n");
    return 1;
}
