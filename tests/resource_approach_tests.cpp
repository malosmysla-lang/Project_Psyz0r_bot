#include "psyz0r/resource_approach.hpp"
#include <iostream>
#include <limits>
using namespace psyz0r;
int main(){
 int failed=0;auto check=[&](bool ok,const char* s){if(!ok){++failed;std::cerr<<s<<'\n';}};
 ResourceApproach a; ResourceGoal goal{"bloodrun","classic","red-route-1",{100,0,100},3,true};
 OwnState own;own.alive=own.state_verified=true;own.position={100,0,0};
 a.set_goal(goal);check(a.update(own,"bloodrun","classic").phase==ResourcePhase::Approach,"another floor is not arrival");
 own.position[2]=100;own.server_time_ms=50;check(a.update(own,"bloodrun","classic").phase==ResourcePhase::AwaitPickup,"proximity is not pickup");
 PickupEvidence event{"red-route-1",3,50,false};
 check(a.update(own,"bloodrun","classic",event).phase==ResourcePhase::AwaitPickup,"unverified pickup rejected");
 event.own_pickup_verified=true;event.goal_id="other";
 check(a.update(own,"bloodrun","classic",event).phase==ResourcePhase::AwaitPickup,"wrong resource rejected");
 event.goal_id=goal.id;event.server_time_ms=100;
 check(a.update(own,"bloodrun","classic",event).phase==ResourcePhase::AwaitPickup,"future event rejected");
 event.server_time_ms=50;check(a.update(own,"bloodrun","classic",event).phase==ResourcePhase::Complete,"verified own event completes");
 a.set_goal(goal);own.server_time_ms=0;a.update(own,"bloodrun","classic");
 for(int t=50;t<=1500;t+=50){own.server_time_ms=t;a.update(own,"bloodrun","classic");}
 check(a.update(own,"bloodrun","classic").phase==ResourcePhase::Replan,"missing pickup requests replan");
 a.set_goal(goal);own.server_time_ms=0;a.update(own,"bloodrun","classic");own.server_time_ms=500;
 check(a.update(own,"bloodrun","classic").phase==ResourcePhase::Replan,"gap invalidates");
 a.set_goal(goal);check(a.update(own,"bloodrun","pql").phase==ResourcePhase::Replan,"physics mismatch");
 goal.position_reviewed=false;a.set_goal(goal);check(a.update(own,"bloodrun","classic").phase==ResourcePhase::Replan,"unreviewed demo position blocked");
 return failed?1:0;
}
