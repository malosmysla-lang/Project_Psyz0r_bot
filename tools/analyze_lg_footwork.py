"""Observe LG firing, view rates and local foot velocity; never claim raw keys."""
import argparse,concurrent.futures as cf,gzip,json,math
from collections import Counter,defaultdict
from pathlib import Path
import collect_ztn_top_players as names
def inspect(folder):
    path=folder/'snapshots.jsonl.gz'
    meta=next((p for p in folder.glob('*.json') if p.name!='snapshots.summary.json'),None)
    if meta is None:return {}
    states=json.loads(meta.read_text(encoding='utf-8-sig')).get('gameStates',[])
    result={};prior=None;last_fire=-100000;identity=None
    side_sign=0;side_since=0
    with gzip.open(path,'rt',encoding='utf-8') as stream:
        for line in stream:
            row=json.loads(line);key=(row['game_state_number'],row['segment'],row['client'])
            if key!=identity:last_fire=-100000;prior=None;side_sign=0;identity=key
            if row['weapon_id']!=6:prior=row;last_fire=-100000;continue
            if any(e.get('kind')=='weapon_fired' for e in row.get('events',[])):last_fire=row['time_ms']
            if prior is None:prior=row;continue
            dt=row['time_ms']-prior['time_ms']
            if not 0<dt<=100 or row['time_ms']-last_fire>100 or (row.get('health') or 0)<=0:prior=row;continue
            state=states[row['game_state_number']-1]
            if not any(m['startTime']<=row['time_ms']<=m['endTime'] for m in state.get('matches',[])):prior=row;continue
            player=next((p['cleanName'] for p in state.get('players',[]) if p['clientNumber']==row['client'] and p['startTime']<=row['time_ms']<=p['endTime']),None)
            canonical=names.names(dict(players=[dict(nick=player or '')]))
            if not canonical:prior=row;continue
            name=canonical[0];out=result.setdefault(name,dict(frames=0,duration_ms=0,grounded=0,yaw_hist={},speed_hist={},patterns={},reversal_hist={}))
            out['frames']+=1;out['duration_ms']+=dt;out['grounded']+=row['ground_entity']!=1023
            yaw=(row['viewangles'][1]-prior['viewangles'][1]+180)%360-180
            rate=min(1440,round(abs(yaw)*1000/dt))
            out['yaw_hist'][rate]=out['yaw_hist'].get(rate,0)+1
            speed=round(row['speed_xy']/10)*10;out['speed_hist'][speed]=out['speed_hist'].get(speed,0)+1
            angle=math.radians(row['viewangles'][1]);vx,vy=row['velocity'][:2]
            forward=vx*math.cos(angle)+vy*math.sin(angle);side=vx*math.sin(angle)-vy*math.cos(angle)
            if row['speed_xy']<35:pattern='pause'
            elif abs(side)>abs(forward)*1.4:pattern='lateral'
            elif forward>abs(side)*1.4:pattern='forward'
            elif forward<-abs(side)*1.4:pattern='backward'
            else:pattern='diagonal'
            out['patterns'][pattern]=out['patterns'].get(pattern,0)+1
            sign=1 if side>60 else -1 if side<-60 else 0
            if sign and sign!=side_sign:
                elapsed=row['time_ms']-side_since
                if side_sign and 75<=elapsed<=3000:
                    bucket=round(elapsed/25)*25;out['reversal_hist'][bucket]=out['reversal_hist'].get(bucket,0)+1
                side_sign=sign;side_since=row['time_ms']
            prior=row
    return result
def quantile(hist,q):
    total=sum(hist.values());threshold=total*q;count=0
    for value,n in sorted(hist.items()):
        count+=n
        if count>=threshold:return value
    return None
def main():
    ap=argparse.ArgumentParser();ap.add_argument('corpus',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args()
    folders=[p.parent for p in a.corpus.glob('*/snapshots.jsonl.gz')];merged={}
    with cf.ProcessPoolExecutor(max_workers=4) as pool:
        for report in pool.map(inspect,folders):
            for name,data in report.items():
                out=merged.setdefault(name,dict(frames=0,duration_ms=0,grounded=0,yaw_hist=Counter(),speed_hist=Counter(),patterns=Counter(),reversal_hist=Counter()))
                for k,v in data.items():
                    if isinstance(v,dict):out[k].update(v)
                    else:out[k]+=v
    players={name:dict(frames=d['frames'],observed_firing_seconds=round(d['duration_ms']/1000,2),grounded_fraction=round(d['grounded']/d['frames'],3),yaw_deg_s={f'p{int(q*100)}':quantile(d['yaw_hist'],q) for q in (.5,.75,.9,.95)},speed_ups={f'p{int(q*100)}':quantile(d['speed_hist'],q) for q in (.5,.9)},patterns=dict(d['patterns']),lateral_reversal_ms={f'p{int(q*100)}':quantile(d['reversal_hist'],q) for q in (.25,.5,.75)}) for name,d in merged.items()}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(dict(files=len(folders),method='Observed POV LG weapon_fired windows <=100ms; view angles and velocity relative to view, not raw keys or screen pixels. No enemy rocket trajectories exported.',players=players),indent=2),encoding='utf-8')
    print(json.dumps(players),flush=True)
if __name__=='__main__':main()
