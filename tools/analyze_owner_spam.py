"""Extract reproducible GL/plasma demonstration windows, never invent their targets."""
import collections,json,math,statistics
from pathlib import Path
from analyze_tactical_patterns import angle,continuous
ROOT=Path(__file__).resolve().parents[1]
def main():
    file=ROOT/'out/feedback-078/demo0000-snapshots.jsonl'
    rows=[json.loads(line) for line in file.open(encoding='utf-8')]
    groups=[];current=None;pickups=[];spins=[];turn=[];sweep=0;prior=None
    for r in rows:
        fired=any(e.get('kind')=='weapon_fired' for e in r.get('events',[]))
        if fired and r['weapon_id'] in (4,8):
            if current is None or current['weapon']!=r['weapon_id'] or r['time_ms']-current['end_ms']>1500 or math.dist(r['position'],current['positions'][0])>192:
                current=dict(weapon=r['weapon_id'],start_ms=r['time_ms'],end_ms=r['time_ms'],positions=[],angles=[]);groups.append(current)
            current['end_ms']=r['time_ms'];current['positions'].append(r['position']);current['angles'].append(r['viewangles'])
        for event in r.get('observed_pov_pickups',[]):
            if event['kind'] in {'red','mega','yellow'}:pickups.append(dict(time_ms=r['time_ms'],kind=event['kind'],position=r['position']))
        if prior is not None and continuous(prior,r) and r['speed_xy']>150 and not fired:
            if turn:sweep+=angle(r['viewangles'][1],turn[-1]['viewangles'][1])
            turn.append(r)
            while turn and r['time_ms']-turn[0]['time_ms']>2000:
                first=turn.pop(0)
                if turn:sweep-=angle(turn[0]['viewangles'][1],first['viewangles'][1])
            if turn and 350<=abs(sweep)<=410 and r['time_ms']-turn[0]['time_ms']>=250:
                spins.append(dict(start_ms=turn[0]['time_ms'],end_ms=r['time_ms'],sweep_deg=round(sweep,1),position=r['position']));turn=[];sweep=0
        else:turn=[];sweep=0
        prior=r
    episodes=[]
    for g in groups:
        if len(g['positions'])<2:continue
        yaw=math.degrees(math.atan2(sum(math.sin(math.radians(a[1])) for a in g['angles']),sum(math.cos(math.radians(a[1])) for a in g['angles'])))
        episodes.append(dict(weapon_id=g['weapon'],start_ms=g['start_ms'],end_ms=g['end_ms'],demo_seconds=round((g['start_ms']-rows[0]['time_ms'])/1000,3),shots=len(g['positions']),position=[round(statistics.mean(p[i] for p in g['positions']),2) for i in range(3)],yaw=round(yaw,2),pitch=round(statistics.mean(a[0] for a in g['angles']),2),geometry_verified=False,target_verified=False,live_enabled=False))
    summary=json.loads((ROOT/'out/feedback-078/demo0000-snapshots.summary.json').read_text())
    report=dict(demo=summary['demo'],sha256=summary['demo_sha256'],snapshots=len(rows),shots=dict(collections.Counter(r['weapon_id'] for r in rows if any(e.get('kind')=='weapon_fired' for e in r.get('events',[])))),spam_candidates=episodes,major_pickups=pickups,spin_candidates=spins,raw_input_verified=False,limits=['This owner demonstration is not a pro duel and has no match scoreboard','View direction is not verified target or projectile collision','User-specified GL conditions require opponent location confidence and no fast closing path before any live activation'])
    (ROOT/'docs/training/OWNER_SPAM_CIRCLE_078.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(demo=report['demo'],spam_candidates=episodes,pickups=collections.Counter(x['kind'] for x in pickups),spins=len(spins))))
if __name__=='__main__':main()
