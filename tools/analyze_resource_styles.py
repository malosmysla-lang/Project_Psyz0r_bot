"""Item-pattern candidates from demo POV, not inferred intentions or omniscience."""
import argparse,gzip,json
from collections import Counter,defaultdict
from pathlib import Path
def main():
    ap=argparse.ArgumentParser();ap.add_argument('corpus',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args()
    records=[]
    for folder in sorted(a.corpus.iterdir()):
        path=folder/'observed_approaches.json.gz'
        if not path.exists():continue
        meta=next((p for p in folder.glob('*.json') if p.name!='snapshots.summary.json'),None)
        if meta is None:continue
        data=json.loads(meta.read_text(encoding='utf-8-sig'))
        matches=data.get('matchStats',[]) or [m for gs in data.get('gameStates',[]) for m in gs.get('matches',[])]
        intervals=[(m['startTime'],m['endTime']) for m in matches if 'endTime' in m]
        with gzip.open(path,'rt',encoding='utf-8') as f:approaches=json.load(f)
        windows=defaultdict(list)
        for route in approaches['routes']:
            start=next((start for start,end in intervals if start<=route['pickup_ms']<=end),None)
            if start is None:continue
            windows[(route['client'],route['segment'],start,(route['pickup_ms']-start)//60000)].append(route)
        for (client,segment,start,bucket),routes in windows.items():
            counts=Counter(r['kind'] for r in routes);major=counts['red']+counts['mega']
            secondary=sum(counts[k] for k in ('yellow','green','health','health_small','health_large','shard'))
            if counts['red'] and counts['mega'] and secondary>=2:mode='cycle_candidate'
            elif counts['mega'] and not counts['red']:mode='mega_anchor_candidate'
            elif counts['red'] and not counts['mega']:mode='red_anchor_candidate'
            elif major==0 and secondary>=2:mode='secondary_recovery_candidate'
            else:mode='unclassified'
            records.append(dict(demo_id=folder.name,source_sha256=approaches['source_sha256'],client=client,segment=segment,start_ms=start+bucket*60000,observed_pickups=dict(counts),mode=mode,intent_verified=False))
    report=dict(method='60-second in-match POV item-pattern windows; not proof of control, hiding or opponent position',records=records,counts=dict(Counter(r['mode'] for r in records)))
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report['counts']))
if __name__=='__main__':main()
