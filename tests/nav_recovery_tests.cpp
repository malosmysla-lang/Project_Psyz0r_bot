#include <cmath>
#include <cstring>
#include <iostream>
#include <stdexcept>
#include "../adapter/native/psyz_nav_recovery.h"
static void check(bool ok,const char *message){if(!ok)throw std::runtime_error(message);}
int main(){try{
 check(Psyz_MotionExpected(1,0,-1,127,0),"Stock AAS movement without an overlay item is watched");
 check(!Psyz_MotionExpected(1,0,-1,0,0),"Intentional stock idle is not a route stall");
 check(!Psyz_MotionExpected(0,0,10,127,0),"Dead player cannot trigger movement recovery");
 check(!Psyz_MotionExpected(1,1,10,127,0),"Learned jump owns its bounded timeout");
 PsyzMotionWatch motion;Psyz_MotionReset(&motion);float still[3]={1,2,3};
 for(int t=0;t<1800;t+=100)check(!Psyz_MotionStalled(&motion,t,still,1,0),"Motion watch allows initial movement window");
 check(Psyz_MotionStalled(&motion,1800,still,1,0),"Independent motion stall survives item-target churn");
 Psyz_MotionReset(&motion);
 for(int t=0;t<=6000;t+=100){still[0]=t*.2f;check(!Psyz_MotionStalled(&motion,t,still,1,0),"Real route movement never triggers stationary escape");}
 Psyz_MotionReset(&motion);still[0]=0;int fired=0;
 for(int t=0;t<=6500;t+=100)fired+=Psyz_MotionStalled(&motion,t,still,1,1);
 check(fired==1,"Combat hold is finite even if firing never stops");
 PsyzNavRecovery s;Psyz_NavReset(&s);float p[3]={0,0,0};
 check(Psyz_NavUpdate(&s,10,0,p,100,0,1,0,0)==0,"Start route");
 p[0]=128;check(Psyz_NavUpdate(&s,10,5500,p,200,0,1,0,0)==0,"Detour away from goal is valid new territory");
 p[0]=0;check(Psyz_NavUpdate(&s,10,11000,p,200,0,1,0,0)==0,"Do not reset progress for loop revisit");
 check(Psyz_NavUpdate(&s,10,11501,p,200,0,1,0,0)==1,"Repeated loop eventually falls back to AAS");
 check(Psyz_NavUpdate(&s,10,17502,p,200,-1,0,0,0)==2,"Failed AAS attempt releases goal");
 Psyz_NavReset(&s);Psyz_NavUpdate(&s,10,0,p,100,0,1,0,0);
 for(int t=1000;t<=6000;t+=1000)check(Psyz_NavUpdate(&s,10,t,p,100,0,1,1,0)==0,"Bounded combat pause");
 check(Psyz_NavUpdate(&s,10,6500,p,100,0,1,1,0)==1,"Continuous fire cannot refresh the stationary clock after its hold budget");
 check(Psyz_NavUpdate(&s,10,8000,p,100,-1,0,1,0)==2,"Persistent firing releases failed AAS goal after fallback");
 Psyz_NavReset(&s);Psyz_NavUpdate(&s,10,0,p,30,0,1,0,1);
 for(int t=100;t<6500;t+=100)check(Psyz_NavUpdate(&s,10,t,p,30,0,1,0,1)==0,"Spawn waiting consumes finite shared budget");
 check(Psyz_NavUpdate(&s,10,6500,p,30,0,1,0,1)==1,"Stale spawn timer cannot conceal a stationary failed pickup");
 Psyz_NavReset(&s);Psyz_NavUpdate(&s,10,0,p,100,0,1,0,0);
 check(Psyz_NavUpdate(&s,10,5900,p,100,2,1,0,0)==0,"Advancing route waypoint refreshes progress");
 check(Psyz_NavUpdate(&s,10,11000,p,100,2,1,0,0)==1,"Waypoint progress cannot conceal a new stationary stall");
 check(Psyz_NavUpdate(&s,10,30000,p,100,3,1,0,0)==2,"Absolute deadline bounds endless movement");
 check(Psyz_NavUpdate(&s,11,30001,p,100,0,1,0,0)==0,"New item gets fresh progress state");
 Psyz_NavReset(&s);Psyz_NavUpdate(&s,10,0,p,100,0,1,0,0);
 check(Psyz_NavUpdate(&s,10,1501,p,100,0,1,0,0)==1,"Pixel stall falls back after 1.5 seconds");
 check(Psyz_NavUpdate(&s,10,3002,p,100,-1,0,0,0)==2,"Persisting pixel stall releases failed goal");
 Psyz_NavReset(&s);Psyz_NavUpdate(&s,10,0,p,30,0,1,0,0);
 check(Psyz_NavUpdate(&s,10,1501,p,30,0,1,0,0)==1,"Near item without pickup is still a stall");
 Psyz_NavReset(&s);Psyz_NavUpdate(&s,10,0,p,30,0,1,0,1);
 check(Psyz_NavUpdate(&s,10,2000,p,30,0,1,0,1)==0,"Real bounded spawn waiting is allowed");
 check(Psyz_NavUpdate(&s,10,3501,p,30,0,1,0,0)==1,"Expired wait must not conceal stationary stall");
 std::cout<<"Navigation recovery scenarios passed\n";return 0;
 }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}}
