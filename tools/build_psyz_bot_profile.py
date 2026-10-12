"""Build original bot definitions using retail includes at runtime, not copied code."""
import zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def weapon(name,inventory,ammo,distances):
    body='switch(ENEMY_HORIZONTAL_DIST) { '+ ' '.join(
        ('default:' if limit is None else f'case {limit}:')+f' return {weight};'
        for limit,weight in distances)+' }'
    return f'weight "{name}" {{ switch({inventory}) {{ case 1: return 0; default: {{ switch({ammo}) {{ case 1: return 0; default: {{ {body} }} }} }} }} }}'


def main():
    weights=['#include "inv.h"']
    for args in [
        ('Machinegun','INVENTORY_MACHINEGUN','INVENTORY_BULLETS',[(None,25)]),
        # Adjacent integer boundaries avoid a broad fuzzy blend through the
        # fighting range (the retail engine interpolates switch weights).
        ('Shotgun','INVENTORY_SHOTGUN','INVENTORY_SHELLS',[(128,90),(129,20),(None,20)]),
        ('Rocket Launcher','INVENTORY_ROCKETLAUNCHER','INVENTORY_ROCKETS',[(128,85),(129,170),(None,170)]),
        ('Lightning Gun','INVENTORY_LIGHTNING','INVENTORY_LIGHTNINGAMMO',[(767,240),(768,0),(None,0)]),
        ('Railgun','INVENTORY_RAILGUN','INVENTORY_SLUGS',[(767,100),(768,260),(None,260)]),
        ('Plasma Gun','INVENTORY_PLASMAGUN','INVENTORY_CELLS',[(None,40)]),
        ('Grenade Launcher','INVENTORY_GRENADELAUNCHER','INVENTORY_GRENADES',[(None,0)]),
    ]:weights.append(weapon(*args))
    weights.append('weight "Gauntlet" { switch(INVENTORY_GAUNTLET) { case 1: return 0; default: return 5; } }')
    char={'NAME':'"Psyz0r"','GENDER':'"male"','WEAPONWEIGHTS':'"bots/psyz_w.c"',
          'ITEMWEIGHTS':'"bots/xaero_i.c"','CHAT_FILE':'"bots/xaero_t.c"','CHAT_NAME':'"xaero"',
          'ATTACK_SKILL':'.85','AIM_SKILL':'.85','AIM_ACCURACY':'.75','VIEW_FACTOR':'.8',
          'VIEW_MAXCHANGE':'240','REACTIONTIME':'.20','CROUCHER':'0','JUMPER':'.05',
          'WEAPONJUMPING':'0','AGGRESSION':'.65','SELFPRESERVATION':'.9','VENGEFULNESS':'.5',
          'CAMPER':'.1','EASY_FRAGGER':'.5','ALERTNESS':'.9','FIRETHROTTLE':'1'}
    for suffix,value in [('MACHINEGUN','.65'),('SHOTGUN','.65'),('ROCKETLAUNCHER','.75'),
                         ('GRENADELAUNCHER','.5'),('LIGHTNING','.65'),('PLASMAGUN','.6'),('RAILGUN','.75')]:
        char['AIM_ACCURACY_'+suffix]=value
    for suffix in ['ROCKETLAUNCHER','GRENADELAUNCHER','PLASMAGUN']:char['AIM_SKILL_'+suffix]='.8'
    files={'scripts/bots.txt':'{ name Psyz0r model sarge aifile bots/psyz_c.c }\n{ name Sarge model sarge aifile bots/sarge_c.c }\n',
           'botfiles/bots/psyz_c.c':'#include "chars.h"\nskill 5 {\n'+'\n'.join('CHARACTERISTIC_'+k+' '+v for k,v in char.items())+'\n}\n',
           'botfiles/bots/psyz_w.c':'\n'.join(weights)+'\n'}
    out=ROOT/'out/prealpha/zzz_psyz_profile.pk3';out.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
        for n,text in files.items():z.writestr(n,text)
    print(out.name)


if __name__=='__main__':main()
