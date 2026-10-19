#include <cmath>
#include <cstring>
#include <iostream>
#include <stdexcept>
#include "../adapter/native/psyz_lg_style.h"
static void check(bool ok,const char *why){if(!ok)throw std::runtime_error(why);}
int main(){try{
    PsyzLGSmooth s{};float current[2]={0,0},seed[2]={0,0};int angles[3]={0,32768,0};
    Psyz_LGSmoothCommand(&s,angles,current,1000,0,240,seed);
    check(std::abs(s.angle[1])<=6.01f,"A 180-degree request must not snap in one tick");
    float previous=s.angle[1];angles[1]=32768;
    Psyz_LGSmoothCommand(&s,angles,current,1025,0,240,seed);
    check(std::abs(Psyz_LGWrap(s.angle[1]-previous))<=6.01f,"Angular rate stays bounded");
    current[1]=90;angles[1]=16384;
    Psyz_LGSmoothCommand(&s,angles,current,2000,0,240,seed);
    check(std::abs(s.angle[1]-90)<.01f,"A new engagement starts at actual view");
    PsyzLGFeet feet{};signed char forward=127,right=127;
    Psyz_LGFeetCommand(&feet,&forward,&right,1000);
    forward=0;right=0;Psyz_LGFeetCommand(&feet,&forward,&right,1025);
    check(forward==0 && right==0,"Stock collision stop must remain immediate");
    forward=127;right=-127;Psyz_LGFeetCommand(&feet,&forward,&right,1050);
    check(forward>0 && right<0,"Footwork cannot reverse stock safe directions");
    std::cout<<"LG tracking and safe footwork contracts passed\n";return 0;
}catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}}
