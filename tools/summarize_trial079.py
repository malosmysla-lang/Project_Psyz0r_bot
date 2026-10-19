"""Cut at the first timelimit: do not mix intermission or an automatic rematch."""
import collections,json,re
from pathlib import Path
from audit_motion079 import audit
ROOT=Path(__file__).resolve().parents[1]
def main():
    source=ROOT/'out/reserve200-079/trial079.log';text=source.read_text(encoding='utf-8')
    marker='broadcast: print "Timelimit hit.'
    if marker not in text:raise RuntimeError('No confirmed first-match completion')
    active,after=text.split(marker,1)
    start=re.search(r'PSYZ_OPENING_BEGIN t=(\d+)',active)
    if not start:raise RuntimeError('No confirmed observed opening')
    start_ms=int(start[1]);selected=[]
    for line in active.splitlines():
        t=re.search(r'\bt=(\d+)',line)
        if t and int(t[1])>=start_ms:selected.append(line)
    active='\n'.join(selected)
    counts=collections.defaultdict(collections.Counter)
    for line in selected:
        if not line.startswith('PSYZ_CLOCK_PICKUP '):continue
        v=dict(re.findall(r'(\w+)=([^ ]+)',line));counts[v['picker']][v['class']]+=1
    scores={}
    for line in after.splitlines():
        m=re.match(r'^\s*(\d+)\s+(-?\d+)\s+\d+\s+(Psyz0r_bot|Trial_Xaero)',line)
        if m and m[3] not in scores:scores[m[3]]=int(m[2])
        if len(scores)==2:break
    old=json.loads((ROOT/'docs/training/PREALPHA_079_TRIAL.json').read_text())
    result={k:v for k,v in old.items() if k not in ('scores','ready_status')}
    result.update(elapsed_seconds=300,first_match_completed=True,final_score=scores,clock_pickups_by_slot={k:dict(v) for k,v in counts.items()},
        score_source='First status after Timelimit hit; later automatic rematch excluded',motion_audit=audit(active),
        pickups=sum(line.startswith('PSYZ_PICKUP ') and 'class=' in line for line in selected),
        red=counts['0']['item_armor_body'],mega=counts['0']['item_health_mega'],
        stock_escapes=sum(line.startswith('PSYZ_STOCK_ESCAPE ') for line in selected),
        tested_native_sha256=json.loads((ROOT/'docs/training/PREALPHA_079_DEPLOYMENT.json').read_text())['files']['minqlx_nopy.so'])
    (ROOT/'docs/training/PREALPHA_079_TRIAL.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({k:result[k] for k in ['final_score','pickups','red','mega','stock_escapes','clock_pickups_by_slot']}))
if __name__=='__main__':main()
