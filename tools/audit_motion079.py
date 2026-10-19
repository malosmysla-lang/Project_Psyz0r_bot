"""Stationary candidates, not automatically proven navigation failures."""
import argparse,collections,json,math,re
from pathlib import Path
def audit(text):
    rows=[];pickups=collections.Counter();escapes=0;target=-1
    for line in text.splitlines():
        v=dict(re.findall(r'(\w+)=([^ ]+)',line))
        if line.startswith('PSYZ_TARGET '):target=int(v['entity'])
        if line.startswith('PSYZ_PICKUP ') and 'class' in v:pickups[v['class']]+=1
        if line.startswith('PSYZ_STOCK_ESCAPE '):escapes+=1
        if not line.startswith('PSYZ_NAV '):continue
        if v.get('pmtype','0')!='0':continue
        rows.append(dict(t=int(v['t']),p=[float(x) for x in v['pos'].split(',')],target=int(v.get('target',target)),
            forward=int(v['forward']) if 'forward' in v else None,right=int(v['right']) if 'right' in v else None,
            armor=int(v['armor']) if 'armor' in v else None,health=int(v['health'])))
    runs=[];start=prior=None;members=[]
    def finish():
        if len(members)>1 and members[-1]['t']-members[0]['t']>=1800:
            runs.append(dict(start_ms=members[0]['t'],duration_ms=members[-1]['t']-members[0]['t'],position=members[0]['p'],
                target_at_start=members[0]['target'],without_overlay_target=all(r['target']<0 for r in members),
                movement_intent_observed=any(r['forward'] or r['right'] for r in members if r['forward'] is not None),
                commands_available=all(r['forward'] is not None for r in members)))
    for r in rows:
        if start is None or prior is None or not 0<r['t']-prior['t']<=500 or math.dist(start['p'],r['p'])>24:
            finish();start=r;members=[]
        members.append(r);prior=r
    finish()
    return dict(samples=len(rows),observed_ms=rows[-1]['t']-rows[0]['t'] if rows else 0,pickups=dict(pickups),stock_escapes=escapes,
        stationary_candidates=len(runs),no_target_candidates=sum(r['without_overlay_target'] for r in runs),
        longest_candidates=sorted(runs,key=lambda r:-r['duration_ms'])[:20],
        limits=['Stationary radius 24u for >=1.8s; combat, waiting and game phase can also produce candidates','No commands in older log means movement intent is unknown, not zero'])
def main():
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args()
    raw=a.source.read_bytes();text=raw.decode('utf-16') if raw.startswith(b'\xff\xfe') else raw.decode('utf-8',errors='replace')
    result=audit(text);a.output.write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k!='longest_candidates'}))
if __name__=='__main__':main()
