#include <iostream>
#include <stdexcept>
#include "../adapter/native/psyz_item_arrival.h"
static void check(bool ok,const char *why){if(!ok)throw std::runtime_error(why);}
int main(){try{
    PsyzArrivalInput in{10000,25000,4000,1,0,0,1,1500};
    auto p=Psyz_PlanItemArrival(&in);
    check(p.action==PSYZ_ARRIVAL_DEFER && p.depart_ms==19500,"Continue other pickups before departure window");
    in.now_ms=20000;check(Psyz_PlanItemArrival(&in).action==PSYZ_ARRIVAL_APPROACH,"Depart early using verified route p90");
    in.now_ms=24000;in.route_p90_ms=0;in.inside_pickup_volume=1;
    check(Psyz_PlanItemArrival(&in).action==PSYZ_ARRIVAL_HOLD,"Safe inside-volume arrival may hold for spawn");
    in.safe_to_hold=0;check(Psyz_PlanItemArrival(&in).action==PSYZ_ARRIVAL_UNSAFE,"Do not hold under known danger");
    in.safe_to_hold=1;in.inside_pickup_volume=0;
    check(Psyz_PlanItemArrival(&in).action!=PSYZ_ARRIVAL_HOLD,"Near platform is not actual pickup volume");
    in.route_p90_ms=4000;check(Psyz_PlanItemArrival(&in).action==PSYZ_ARRIVAL_LATE,"Late route is diagnosed explicitly");
    in.route_verified=0;check(Psyz_PlanItemArrival(&in).action==PSYZ_ARRIVAL_UNKNOWN,"Unknown route is never given a fabricated ETA");
    in.route_verified=1;in.due_ms=-1;check(Psyz_PlanItemArrival(&in).action==PSYZ_ARRIVAL_UNKNOWN,"Unknown item deadline remains unknown");
    in.item_available=1;check(Psyz_PlanItemArrival(&in).action==PSYZ_ARRIVAL_APPROACH,"Available item needs no invented deadline");
    in.now_ms=INT64_MAX-100;check(Psyz_PlanItemArrival(&in).action==PSYZ_ARRIVAL_UNKNOWN,"Invalid clock arithmetic cannot wrap");
    std::cout<<"Verified-route item arrival scenarios passed\n";return 0;
}catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}}
