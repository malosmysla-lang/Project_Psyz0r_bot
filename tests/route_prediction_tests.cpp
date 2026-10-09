#include "psyz0r/route_prediction.hpp"
#include <iostream>
using namespace psyz0r;
int main(int argc,char** argv) {
    int failures=0;auto check=[&](bool v,const char* n){if(!v){++failures;std::cerr<<n<<'\n';}};
    RoutePredictor p;
    check(!p.observe({"hidden","",0,false}),"unperceived zones ignored");
    const char* zones[]={"mega","rail","yellow"};
    for(int i=0;i<8;++i)p.observe({zones[i%3],"synthetic_visible_zone",static_cast<double>(i),true});
    check(!p.forecast(7),"not enough completed repeats");
    p.observe({"yellow","synthetic_visible_zone",8,true});
    auto f=p.forecast(8);
    check(f&&f->next_zone=="mega"&&f->expected_time==9,"three timed observed cycles predict next zone");
    check(!p.forecast(30),"prediction expires");
    p.observe({"yellow","synthetic_visible_zone",8.5,true});
    check(p.forecast(8.5).has_value(),"remaining in same zone is not a route deviation");
    p.observe({"other","synthetic_audible_known_zone",9,true});
    check(!p.forecast(9),"changed route lowers confidence");
    p.reset();check(!p.forecast(0),"new opponent/match clears history");
    for(int i=0;i<20;++i)p.observe({"mega","synthetic_test",static_cast<double>(i),true});
    check(!p.forecast(19),"standing in one zone is not a cycle");
    p.reset();double time=0;
    for(int i=0;i<9;++i){time+=i<3?1:i<6?3:1;p.observe({zones[i%3],"synthetic_test",time,true});}
    check(!p.forecast(time),"timing mismatch prevents reliable prediction");
    if(argc>1) {
        auto loaded=RoutePatternSettings::load(argv[1]);
        check(loaded.min_repeats==3&&loaded.max_observations==64,"load actual route prediction configuration");
    }
    return failures?1:0;
}
