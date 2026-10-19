#include <cmath>
#include <iostream>
#include <stdexcept>
#include "../adapter/native/psyz_combo_policy.h"
static void check(bool ok,const char *why){if(!ok)throw std::runtime_error(why);}
int main(){try{
    int ammo[16]{};for(int i=1;i<9;i++)ammo[i]=100;
    PsyzComboContext c{6,0x1fe,ammo,450,100,50,60,0,1,1,6,100,0,0,0};
    check(Psyz_ComboChoose(&c).weapon==7,"LG -> rail for visible low-stack retreating contact");
    c.distance=650;c.closing=1;
    check(Psyz_ComboChoose(&c).weapon==7,"Distant one-rail finish does not require walking backwards");
    c.distance=500;c.enemy_health=100;
    check(Psyz_ComboChoose(&c).weapon==6,"Medium duel keeps LG instead of manufacturing a combo");
    c.distance=140;c.closing=1;c.enemy_health=100;
    check(Psyz_ComboChoose(&c).weapon==5,"LG -> rocket when closing with safe HP");
    c.own_health=60;
    check(Psyz_ComboChoose(&c).weapon!=5,"Low HP cannot force close splash rocket");
    c.own_health=100;c.distance=50;c.enemy_health=30;c.revenge_active=1;c.melee_path_clear=1;
    check(Psyz_ComboChoose(&c).weapon==1,"Safe visible one-hit gauntlet revenge");
    c.enemy_armor=100;
    check(Psyz_ComboChoose(&c).weapon!=1,"Thirty HP with armor is not one gauntlet hit");
    c.enemy_armor=0;c.melee_path_clear=0;
    check(Psyz_ComboChoose(&c).weapon!=1,"Blocked melee path prevents revenge");
    c.enemy_visible=0;
    check(Psyz_ComboChoose(&c).reason==PSYZ_COMBO_NO_OBSERVATION,"No hidden-target finishing");
    c.enemy_visible=1;c.stack_known=0;
    check(Psyz_ComboChoose(&c).weapon==c.current_weapon,"Unknown stack preserves stock AI");
    c.stack_known=1;c.last_hit_age_ms=901;
    check(Psyz_ComboChoose(&c).reason==PSYZ_COMBO_STALE_HIT,"Old hit cannot drive endless push");
    c.last_hit_age_ms=100;c.distance=450;c.closing=0;ammo[7]=0;ammo[6]=0;
    check(Psyz_ComboChoose(&c).weapon==c.current_weapon,"No empty-weapon switch");
    c.distance=NAN;
    check(Psyz_ComboChoose(&c).reason==PSYZ_COMBO_NO_OBSERVATION,"Invalid geometry is rejected");
    std::cout<<"Combo finishing safety scenarios passed\n";return 0;
}catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}}
