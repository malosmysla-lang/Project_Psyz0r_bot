/* Local arrival planner; does not submit movement or override stock AAS. */
#ifndef PSYZ_ITEM_ARRIVAL_H
#define PSYZ_ITEM_ARRIVAL_H
#include <stdint.h>
enum {PSYZ_ARRIVAL_UNKNOWN,PSYZ_ARRIVAL_DEFER,PSYZ_ARRIVAL_APPROACH,
      PSYZ_ARRIVAL_HOLD,PSYZ_ARRIVAL_LATE,PSYZ_ARRIVAL_UNSAFE};
typedef struct {
    int64_t now_ms,due_ms,route_p90_ms;
    int route_verified,item_available,inside_pickup_volume,safe_to_hold;
    int preposition_ms;
} PsyzArrivalInput;
typedef struct {int action;int64_t depart_ms,arrival_ms,lateness_ms;} PsyzArrivalPlan;
static PsyzArrivalPlan Psyz_PlanItemArrival(const PsyzArrivalInput *in){
    PsyzArrivalPlan out={PSYZ_ARRIVAL_UNKNOWN,-1,-1,0};
    // Доверяем ETA только для проверенного пути. Прямое расстояние через стену
    // не становится временем маршрута; эта функция не создаёт телепорт/ускорение.
    if(!in->route_verified || in->now_ms<0 || in->route_p90_ms<0 ||
       in->route_p90_ms>30000 || in->preposition_ms<0 || in->preposition_ms>5000 ||
       in->now_ms>INT64_MAX-in->route_p90_ms)return out;
    out.arrival_ms=in->now_ms+in->route_p90_ms;
    if(in->item_available){out.action=PSYZ_ARRIVAL_APPROACH;out.depart_ms=in->now_ms;return out;}
    if(in->due_ms<=in->now_ms)return out;
    out.depart_ms=in->due_ms-in->route_p90_ms-in->preposition_ms;
    if(out.depart_ms<0)out.depart_ms=0;
    // DEFER значит «ещё можно собирать другие ресурсы», а не «замри на месте».
    if(in->now_ms<out.depart_ms){out.action=PSYZ_ARRIVAL_DEFER;return out;}
    // Самого расстояния 48/64u недостаточно для stopwatch: нужна реальная
    // достижимость объёма подбора. Под платформой красного HOLD не возникает.
    if(in->inside_pickup_volume){
        if(!in->safe_to_hold){out.action=PSYZ_ARRIVAL_UNSAFE;return out;}
        if(in->due_ms-in->now_ms<=in->preposition_ms){out.action=PSYZ_ARRIVAL_HOLD;return out;}
    }
    out.lateness_ms=out.arrival_ms>in->due_ms?out.arrival_ms-in->due_ms:0;
    out.action=out.lateness_ms>1000?PSYZ_ARRIVAL_LATE:PSYZ_ARRIVAL_APPROACH;
    return out;
}
#endif
