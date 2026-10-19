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
// Короткое ожидание защищает только подход на том же уровне у предмета.
// Таймер красного наверху не оправдывает неподвижность под платформой.
static int Psyz_ItemWaitAllowed(float distance,float height,int available,int due,int now){
    return isfinite(distance) && isfinite(height) && distance>=0 && distance<64 &&
        fabsf(height)<40 && !available && due>now && due-now<=3000;
}
static int Psyz_OpeningRedCanApproach(PsyzItemClock c,int now,int opening_elapsed,float travel) {
    // Резерв второго красного не означает «стоять у него с пятой секунды».
    // Сначала собираем дебютные пушки. Выход начинаем по реальным часам,
    // чтобы ранний неподвижный поход не завершился watchdog-ban до spawn.
    return opening_elapsed>=20000 && Psyz_TimerCandidate(c,now,travel,1);
}
#endif
