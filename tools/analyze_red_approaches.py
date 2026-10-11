"""Cut derived red pickup episodes; flight labels are candidates, not raw input."""
import gzip
import json
import math
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def classify(points):
    air=[p for p in points if p['ground']==1023]
    if not air:return 'grounded'
    travel=max(math.dist(p['p'][:2],air[0]['p'][:2]) for p in air)
    if any(p['weapon']==5 for p in air):return 'rocket_equipped_airborne_candidate'
    return 'longjump_candidate' if travel>=128 else 'short_airborne'


def main():
    episodes=[]
    target=next(e for e in json.loads((ROOT/'out/research_stock_ai/bloodrun_items.json').read_text())
                if e['classname']=='item_armor_body')
    for corpus in ('bloodrun_corpus','owner_bloodrun_corpus'):
        for file in sorted((ROOT/'out'/corpus).glob('*/observed_approaches.json.gz')):
            with gzip.open(file,'rt') as f:data=json.load(f)
            for r in data['routes']:
                if r['kind']!='red' or math.dist(r['points'][-1]['p'],target['position'])>112:continue
                episodes.append(dict(demo_id=file.parent.name,corpus=corpus,source_sha256=data['source_sha256'],
                    start_ms=r['points'][0]['t'],pickup_ms=r['pickup_ms'],client=r['client'],segment=r['segment'],
                    category=classify(r['points']),pickup_observed=True,raw_controls_verified=False,
                    rocket_causality_verified=False,live_verified=False,points=r['points']))
    out=ROOT/'out/red_approaches';out.mkdir(exist_ok=True)
    with gzip.open(out/'all_episodes.json.gz','wt',encoding='utf-8') as f:json.dump(episodes,f)
    # Diverse approach origins; retain only grounded intermediate goals for
    # ordinary AAS execution. Airborne actions remain review-only.
    bank=[];seen=set()
    for e in sorted(episodes,key=lambda e:e['pickup_ms']-e['start_ms']):
        points=e['points'];key=tuple(round(v/96) for v in points[0]['p'])
        if key in seen or len(bank)>=24:continue
        grounded=[p for p in points if p['ground']==1022]
        if len(grounded)<2 or math.dist(grounded[-1]['p'],target['position'])>112:continue
        chosen=[]
        for p in grounded:
            if not chosen or math.dist(p['p'],chosen[-1]['p'])>=64:chosen.append(p)
        if chosen[-1]!=grounded[-1]:chosen.append(grounded[-1])
        if not 2<=len(chosen)<=24:continue
        seen.add(key);bank.append(dict(**{k:v for k,v in e.items() if k!='points'},points=chosen))
    from associate_demo_aas import AasLocator
    locator=AasLocator(ROOT/'out/research_stock_ai/bloodrun.aas')
    lines=['/* Generated red pickup approaches. Grounded goals; AAS still executes. */',
           'static const PsyzLearnedRoute psyz_red_routes[] = {']
    valid=[]
    for e in bank:
        areas=[locator.area(p['p']) for p in e['points']]
        if any(a<=0 for a in areas):continue
        pts=','.join('{{'+','.join(f'{v:.4f}f' for v in p['p'])+'},'+str(a)+'}' for p,a in zip(e['points'],areas))
        lines.append('{%d,%d,320.f,{%s},"item_armor_body",{%s}},'%(target['entity'],len(areas),','.join(f'{v:.4f}f' for v in target['position']),pts))
        valid.append(e)
    lines+=['};','#define PSYZ_RED_ROUTE_COUNT (sizeof(psyz_red_routes)/sizeof(psyz_red_routes[0]))']
    (ROOT/'adapter/native/psyz_red_routes.h').write_text('\n'.join(lines)+'\n')
    summary=dict(total_pickups=len(episodes),categories=dict(Counter(e['category'] for e in episodes)),
                 selected_grounded_approaches=valid,
                 note='All episodes stored locally as derived JSON cuts; rocket held does not prove rocketjump. No airborne replay enabled.')
    (ROOT/'docs/training/BLOODRUN_RED_APPROACHES.json').write_text(json.dumps(summary,indent=2))
    print('red pickups',len(episodes),'bank',len(valid),summary['categories'])


if __name__=='__main__':main()
