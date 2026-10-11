"""Mine own-POV GL shots near GL platform; target/closure remain unverified."""
import gzip
import json
import math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def main():
    examples=[];shots=0;demos=0
    for f in sorted((ROOT/'out/bloodrun_corpus').glob('*/snapshots.jsonl.gz')):
        demos+=1
        with gzip.open(f.parent/'observed_approaches.json.gz','rt',encoding='utf-8') as s:
            sha=json.load(s)['source_sha256']
        with gzip.open(f,'rt',encoding='utf-8') as stream:
            for line in stream:
                r=json.loads(line)
                if r['weapon_id']!=4 or not any(e['kind']=='weapon_fired' for e in r['events']):continue
                if not (r['pm_type']==0 or (r['pm_type']==2 and r.get('pm_flags',0)&4096)):continue
                shots+=1
                if math.dist(r['position'],[-256,-320,400])>192:continue
                examples.append(dict(demo_id=f.parent.name,source_sha256=sha,time_ms=r['time_ms'],
                    client=r['client'],segment=r['segment'],position=r['position'],
                    viewangles=r['viewangles'],velocity=r['velocity'],
                    candidate='GL_platform_shot',target_verified=False,
                    enemy_position_verified=False,fast_closure_excluded=False,ready_for_execution=False))
    report=dict(demos=demos,observed_gl_fire_snapshots=shots,platform_candidates=len(examples),
                note='Near-platform shots only. Not proof of Mega aim or upper-TP zoning; no hidden enemy positions recovered.',examples=examples)
    (ROOT/'docs/training/GRENADE_ZONING_CANDIDATES.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(demos,shots,len(examples))


if __name__=='__main__':main()
