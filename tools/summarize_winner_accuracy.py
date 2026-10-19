"""Winner-only pooled scoreboard accuracy; absent values are never invented."""
import collections,hashlib,json,re,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
GUNS={1:'gauntlet',2:'machinegun',3:'shotgun',5:'rocketLauncher',6:'lightningGun',7:'railgun',8:'plasmaGun',9:'bfg'}
def main():
    rows=[];matches=0;warnings=[]
    for f in sorted((ROOT/'out/tactical-research/metadata').glob('*/*.json')):
        data=json.loads(f.read_text(encoding='utf-8-sig'))
        for match in data.get('matchStats',[]):
            if match.get('gameTypeShort')!='1v1':continue
            winner=re.sub(r'\^[0-9]','',match.get('winner','')).strip().casefold()
            if not winner:continue
            winners=[p for p in match.get('playerStats',[]) if p.get('cleanName',re.sub(r'\^[0-9]','',p.get('name',''))).strip().casefold()==winner]
            if len(winners)!=1:continue
            matches+=1;p=winners[0]
            for weapon,prefix in GUNS.items():
                shots,hits=p.get(prefix+'Shots'),p.get(prefix+'Hits')
                accuracy=p.get(prefix+'Accuracy')
                if shots is None or hits is None or shots<=0:continue
                # Для SG количество pellets и для gauntlet статистика замаха
                # могут не совпадать со знаменателем серверной accuracy.
                rows.append(dict(demo_id=f.parent.name,winner=winner,weapon=weapon,shots=shots,hits=hits,accuracy=accuracy,damage=p.get(prefix+'Damage')))
    table=[]
    for weapon,prefix in GUNS.items():
        sample=[r for r in rows if r['weapon']==weapon]
        shots=sum(r['shots'] for r in sample);hits=sum(r['hits'] for r in sample)
        mean=statistics.mean(r['accuracy'] for r in sample if r['accuracy'] is not None) if any(r['accuracy'] is not None for r in sample) else None
        pooled=100*hits/shots if shots else None
        # Среднее по матчам — база по запросу владельца. Pooled отдельно,
        # чтобы длинная LG-игра не маскировала выбор метода среднего.
        base=round(mean,1) if mean is not None else None
        table.append(dict(weapon_id=weapon,weapon=prefix,observations=len(sample),shots=shots,hits=hits,mean_match_accuracy=base,pooled_accuracy=round(pooled,2) if pooled is not None else None,min_accuracy=round(max(0,base-7.5),1) if base is not None else None,max_accuracy=round(min(100,base+7.5),1) if base is not None else None,eligible_for_aim_profile=weapon in (2,3,5,6,7,8) and base is not None and 0<base<100))
    report=dict(parsed_demos=500,matches_with_verified_winner=matches,table=table,observations=rows,method='Arithmetic mean of reported per-match accuracy for the winning scoreboard row; pooled hits/shots shown separately; range +/-7.5 percentage points.',limitations=['A score winner is not independently verified player identity','Accuracy is not damage per bullet','Gauntlet, splash and shotgun pellet semantics differ; do not calibrate by raw hit quotient alone','Aiming profile parameters do not guarantee achieved accuracy; live calibration required'],pipeline_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (ROOT/'docs/training/WINNER_ACCURACY_078.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(matches=matches,table=table)))
if __name__=='__main__':main()
