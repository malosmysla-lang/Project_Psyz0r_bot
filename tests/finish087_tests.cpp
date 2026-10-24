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
 c.weapons|=(1<<3)|(1<<6);ammo[3]=4;ammo[6]=40;
 c.current=7;c.last_weapon=7;c.distance=400;c.target_health=120;
 assert(Psyz_Finish087Choose(&c).weapon==6); // Rail hit -> sustained shaft in range.
 c.distance=701;assert(Psyz_Finish087Choose(&c).weapon==7);
 c.distance=400;ammo[6]=11;assert(Psyz_Finish087Choose(&c).weapon==7);
 ammo[6]=40;c.distance=100;c.target_health=50;c.own_health=20;
 assert(Psyz_Finish087Choose(&c).weapon==3); // Low own HP: shotgun, never self-rocket.
 ammo[3]=0;assert(Psyz_Finish087Choose(&c).weapon==7);
 ammo[3]=4;c.own_health=0;assert(Psyz_Finish087Choose(&c).weapon==7);
 c.own_health=20;c.age_ms=101;assert(Psyz_Finish087Choose(&c).weapon==7);
 std::cout<<"Finish087 contact age, stack, ammo, close splash and revenge checks passed\n";
}
