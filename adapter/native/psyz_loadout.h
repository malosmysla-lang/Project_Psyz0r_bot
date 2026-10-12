/* Pure policy shared by the retail adapter and ABI-independent tests. */
#ifndef PSYZ_LOADOUT_H
#define PSYZ_LOADOUT_H
static int Psyz_Reserve(int weapon) {
    return weapon==5?3:weapon==6?40:weapon==7?3:weapon==8?20:weapon==3?3:weapon==2?30:weapon==4?2:1;
}
static int Psyz_TrinityReady(int weapons,const int *ammo) {
    int count=0;
    for(int w=5;w<=7;w++)if((weapons&(1<<w)) && ammo[w]>=Psyz_Reserve(w))count++;
    return count;
}
static float Psyz_AmmoNeed(int weapons,const int *ammo,int weapon) {
    if(weapon<2 || weapon>8 || !(weapons&(1<<weapon)))return 0;
    if(ammo[weapon]<Psyz_Reserve(weapon))return weapon>=5 && weapon<=7?125.f:65.f;
    return ammo[weapon]<Psyz_Reserve(weapon)*2?35.f:0.f;
}
#endif
