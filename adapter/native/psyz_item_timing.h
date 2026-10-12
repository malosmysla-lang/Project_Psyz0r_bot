/* Observer-authorized map-item timing. No opponent positions are used. */
#ifndef PSYZ_ITEM_TIMING_H
#define PSYZ_ITEM_TIMING_H
#include <math.h>
typedef struct { int valid,available,due,updated; } PsyzItemClock;
static PsyzItemClock Psyz_ReadItemClock(int available,int nextthink,int now) {
    PsyzItemClock c={1,available!=0,available?now:nextthink>now?nextthink:-1,now};return c;
}
static float Psyz_ItemTravelSeconds(float distance) {
    /* Coarse pre-positioning estimate, not a claim of AAS path cost.
       Include turns/vertical approaches; refine from observed travel later. */
    return distance/300.f+2.f;
}
static int Psyz_TimerCandidate(PsyzItemClock c,int now,float travel,int major) {
    if(!c.valid || !isfinite(travel) || travel<0)return 0;
    if(c.available)return 1;
    if(c.due<=now)return 0;
    float wait=(c.due-now)/1000.f;
    return major?wait<=15.f && wait<=travel+3.f:wait<=3.f;
}
static float Psyz_TimerIdle(PsyzItemClock c,int now,float travel) {
    if(c.available)return 0;
    return fmaxf(0,(c.due-now)/1000.f-travel);
}
#endif
