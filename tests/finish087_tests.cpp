#include <cassert>
#include <cmath>
#include <iostream>
#include "../adapter/native/psyz_finish087_policy.h"
int main(){
 int ammo[16]={};ammo[5]=10;ammo[7]=5;
 PsyzFinish087Input c={6,(1<<1)|(1<<5)|(1<<7),ammo,100,50,60,0,50,1,6,0,450,2};
 assert(Psyz_Finish087Choose(&c).weapon==7);
 c.age_ms=101;assert(Psyz_Finish087Choose(&c).weapon==6);
 c.age_ms=50;c.turn_degrees=9;assert(Psyz_Finish087Choose(&c).weapon==6);
 c.turn_degrees=2;c.distance=180;assert(Psyz_Finish087Choose(&c).weapon==5);
 c.own_health=60;assert(Psyz_Finish087Choose(&c).weapon==6);
 c.own_health=100;c.distance=40;c.target_health=30;c.revenge=1;assert(Psyz_Finish087Choose(&c).weapon==1);
 c.target_armor=60;assert(Psyz_Finish087Choose(&c).weapon==6);
 c.target_armor=0;c.attack=0;assert(Psyz_Finish087Choose(&c).weapon==6);
 c.attack=1;c.distance=NAN;assert(Psyz_Finish087Choose(&c).weapon==6);
 c.distance=450;c.revenge=0;c.target_health=70;ammo[7]=0;assert(Psyz_Finish087Choose(&c).weapon==6);
 std::cout<<"Finish087 contact age, stack, ammo, close splash and revenge checks passed\n";
}
