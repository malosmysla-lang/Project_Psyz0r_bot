"""Describe per-player match accuracy; never treat it as per-shot aim probability."""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def percentile(values, q):
    values=sorted(values); index=(len(values)-1)*q
    lo=math.floor(index); hi=math.ceil(index)
    return round(values[lo]+(values[hi]-values[lo])*(index-lo),2)


def main():
    result={}
    for weapon, minimum in [('plasmaGun',100),('lightningGun',200),('railgun',20),('rocketLauncher',30)]:
        entries=[]
        for file in (ROOT/'out/playtest_comparison_20261012/corpus_stats').glob('*.json'):
            data=json.loads(file.read_text(encoding='utf-8-sig'))
            for match in data.get('matchStats',[]):
                for p in match.get('playerStats',[]):
                    shots=p.get(weapon+'Shots',0); hits=p.get(weapon+'Hits',0)
                    if shots<minimum:continue
                    entries.append(dict(demo=file.name,player=p.get('cleanName'),shots=shots,hits=hits,
                                        accuracy=100*hits/shots,winner=p.get('cleanName')==match.get('firstPlaceName')))
        groups={}
        for name,rows in [('all',entries),('winners',[e for e in entries if e['winner']])]:
            if not rows:groups[name]={'samples':0};continue
            acc=[e['accuracy'] for e in rows]
            groups[name]=dict(samples=len(rows),p25=percentile(acc,.25),median=percentile(acc,.5),
                              p75=percentile(acc,.75),p90=percentile(acc,.9),
                              pooled_accuracy=round(100*sum(e['hits'] for e in rows)/sum(e['shots'] for e in rows),2))
        result[weapon]=dict(minimum_shots=minimum,groups=groups,entries=entries)
    report=dict(note='Per-player-match observations; repeated players possible; not all verified professionals. '
                     'Sample thresholds exclude very small use. Accuracy is not direct aim-setting probability.',weapons=result)
    (ROOT/'docs/training/WEAPON_ACCURACY_CORPUS_20261012.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:{'minimum_shots':v['minimum_shots'],**v['groups']} for k,v in result.items()}))


if __name__=='__main__':main()
