#include <cmath>
#include <cstring>
#include <iostream>
#include <stdexcept>
#include "../adapter/native/psyz_nav_recovery.h"
static void check(bool ok,const char *message){if(!ok)throw std::runtime_error(message);}
int main(){try{
 PsyzNavRecovery s;Psyz_NavReset(&s);float p[3]={0,0,0};
 check(Psyz_NavUpdate(&s,10,0,p,100,0,1,0,0)==0,"Start route");
 p[0]=128;check(Psyz_NavUpdate(&s,10,5500,p,200,0,1,0,0)==0,"Detour away from goal is valid new territory");
 p[0]=0;check(Psyz_NavUpdate(&s,10,11000,p,200,0,1,0,0)==0,"Do not reset progress for loop revisit");
 check(Psyz_NavUpdate(&s,10,11501,p,200,0,1,0,0)==1,"Repeated loop eventually falls back to AAS");
 check(Psyz_NavUpdate(&s,10,17502,p,200,-1,0,0,0)==2,"Failed AAS attempt releases goal");
 Psyz_NavReset(&s);Psyz_NavUpdate(&s,10,0,p,100,0,1,0,0);
 for(int t=1000;t<=10000;t+=1000)check(Psyz_NavUpdate(&s,10,t,p,100,0,1,1,0)==0,"Bounded combat pause");
 check(Psyz_NavUpdate(&s,10,11001,p,100,0,1,1,0)==1,"Continuous firing cannot freeze watchdog forever");
 Psyz_NavReset(&s);Psyz_NavUpdate(&s,10,0,p,100,0,1,0,0);
 check(Psyz_NavUpdate(&s,10,5900,p,100,2,1,0,0)==0,"Advancing route waypoint refreshes progress");
 check(Psyz_NavUpdate(&s,10,11000,p,100,2,1,0,0)==0,"Waypoint progress grants finite grace");
 check(Psyz_NavUpdate(&s,10,30000,p,100,3,1,0,0)==2,"Absolute deadline bounds endless movement");
 check(Psyz_NavUpdate(&s,11,30001,p,100,0,1,0,0)==0,"New item gets fresh progress state");
 std::cout<<"Navigation recovery scenarios passed\n";return 0;
 }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}}
