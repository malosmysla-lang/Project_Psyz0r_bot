"""Winner and damage-leader cohorts; observed movement is not recovered input."""
import collections,concurrent.futures as cf,gzip,hashlib,json,math,re,statistics
from pathlib import Path
from analyze_strafe_starts import analyse_rows,summary
from analyze_tactical_patterns import continuous,foot_pattern,resource_sequences,percentile
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'out/reserve200-079'
GUNS={1:'gauntlet',2:'machinegun',3:'shotgun',4:'grenadeLauncher',5:'rocketLauncher',6:'lightningGun',7:'railgun',8:'plasmaGun',9:'bfg'}
def clean(s):return re.sub(r'\^[0-9]','',s or '').strip().casefold()

def select_cohorts(meta,demo_id):
    result=[]
    for index,m in enumerate(meta.get('matchStats',[])):
        if m.get('gameTypeShort')!='1v1':continue
        players=[p for p in m.get('playerStats',[]) if p.get('team')=='free' and p.get('clientNumber',-1)>=0]
        winner=[p for p in players if clean(p.get('cleanName',p.get('name')))==clean(m.get('winner'))]
        leaders=[]
        # A single available damage row cannot establish a duel's damage leader.
        if len(players)==2 and all(isinstance(p.get('damageGiven'),(int,float)) for p in players):
            best=max(p['damageGiven'] for p in players)
            leaders=[p for p in players if p['damageGiven']==best]
        result.append(dict(demo_id=str(demo_id),match_index=index,state=m['gameStateIndex']+1,start=m['startTime'],end=m['endTime'],
            winner_clients=[p['clientNumber'] for p in winner] if len(winner)==1 else [],
            damage_leader_clients=[p['clientNumber'] for p in leaders],damage_tied=len(leaders)>1,
            players=players))
    return result

def inspect(record):
    ident=str(record['archive_id']);folder=OUT/ident
    try:
        path=next((folder/'metadata').glob('*.json'));meta=json.loads(path.read_text(encoding='utf-8-sig'))
        cohorts=select_cohorts(meta,ident)
        rows=[];prior=None;life=0;valid_life={};foot=collections.defaultdict(collections.Counter)
        last_fire=-999999;last_gun=-1;openings=[]
        with gzip.open(folder/'snapshots.jsonl.gz','rt',encoding='utf-8') as stream:
            for line in stream:
                r=json.loads(line)
                match=next((m for m in cohorts if m['state']==r['game_state_number'] and m['start']<=r['time_ms']<=m['end'] and r['client'] in set(m['winner_clients']+m['damage_leader_clients'])),None)
                valid=match is not None and r.get('health',0)>0 and r.get('pm_type') in (0,2)
                if not valid:
                    # Preserve a boundary row: filtering dead/warmup/other POVs
                    # out entirely could join two lives separated by <100ms.
                    rows.append(dict(r,health=0));prior=None;life+=1;last_fire=-999999;continue
                rows.append(r)
                ok=prior is not None and continuous(prior,r)
                if not ok:life+=1;last_fire=-999999
                valid_life[(r['client'],r['segment'],r['time_ms'])]=life
                fired=any(e.get('kind')=='weapon_fired' for e in r['events'])
                if fired:last_fire=r['time_ms'];last_gun=r['weapon_id']
                if ok and r['time_ms']-last_fire<=100 and last_gun==r['weapon_id']:
                    dt=r['time_ms']-prior['time_ms'];kind,_=foot_pattern(r);s=foot[str(last_gun)]
                    s['firing_ms']+=dt;s[kind+'_ms']+=dt;s['ground_ms']+=dt*(r['ground_entity']!=1023)
                    rate=abs((r['viewangles'][1]-prior['viewangles'][1]+180)%360-180)*1000/dt
                    s['steady_view_ms']+=dt*(rate<=60)
                prior=r
        jumps=analyse_rows(rows,ident)
        for j in jumps:j.pop('view_trace',None)
        with gzip.open(folder/'observed_approaches.json.gz','rt',encoding='utf-8') as stream:routes=json.load(stream)['routes']
        edges,chains,dwells=resource_sequences(routes,valid_life,True)
        for m in cohorts:
            for client in sorted(set(m['winner_clients']+m['damage_leader_clients'])):
                pickups=[dict(kind=r['kind'],elapsed_ms=r['pickup_ms']-m['start'],position=r['points'][-1]['p']) for r in routes if r['client']==client and 0<=r['pickup_ms']-m['start']<=30000 and (r['client'],r['segment'],r['pickup_ms']) in valid_life]
                openings.append(dict(client=client,state=m['state'],sequence=pickups,optimality_verified=False))
        return dict(demo_id=ident,source_sha256=record['sha256'],matches=cohorts,observed_selected_clients=sorted({r['client'] for r in rows if r.get('health',0)>0}),footwork={k:dict(v) for k,v in foot.items()},jumps=jumps,transitions=edges,openings=openings,dwells=dwells)
    except Exception as e:return dict(demo_id=ident,error=str(e))

def accuracy_table(matches,cohort):
    observations=[]
    for m in matches:
        clients=m[cohort+'_clients']
        for p in m['players']:
            if p['clientNumber'] not in clients:continue
            for wid,prefix in GUNS.items():
                accuracy=p.get(prefix+'Accuracy');shots=p.get(prefix+'Shots')
                if not isinstance(accuracy,(int,float)) or not shots or not 0<=accuracy<=100:continue
                observations.append(dict(demo_id=m['demo_id'],match_index=m['match_index'],client=p['clientNumber'],weapon_id=wid,accuracy=accuracy,shots=shots,hits=p.get(prefix+'Hits'),damage=p.get(prefix+'Damage')))
    table=[]
    for wid,prefix in GUNS.items():
        sample=[r for r in observations if r['weapon_id']==wid];values=[r['accuracy'] for r in sample]
        table.append(dict(weapon_id=wid,weapon=prefix,n=len(values),mean=round(statistics.mean(values),2) if values else None,median=statistics.median(values) if values else None,p10=percentile(values,.1),p90=percentile(values,.9)))
    return dict(table=table,observations=observations)

def main():
    records=json.loads((ROOT/'docs/training/RESERVE200_079_MANIFEST.json').read_text(encoding='utf-8'))['records']
    reports=[]
    with cf.ProcessPoolExecutor(max_workers=4) as pool:
        for i,r in enumerate(pool.map(inspect,records),1):
            reports.append(r);(OUT/(r['demo_id']+'.research.json')).write_text(json.dumps(r,ensure_ascii=False),encoding='utf-8')
            if i%20==0:print('RESEARCH',i,'/',len(records),flush=True)
    valid=[r for r in reports if 'error' not in r];matches=[m for r in valid for m in r['matches']]
    prior=[]
    for p in (ROOT/'out/tactical-research/metadata').glob('*/*.json'):
        prior+=select_cohorts(json.loads(p.read_text(encoding='utf-8-sig')),p.parent.name)
    # Cohorts stay separate. The same winner/damage leader is never counted twice
    # inside a combined match-player cohort; a tied leader is explicitly retained.
    foot=collections.defaultdict(collections.Counter);edges=collections.defaultdict(list)
    jumps=[j for r in valid for j in r['jumps']]
    full=[j for j in jumps if j['observed_horizon_ms']>=3900]
    for r in valid:
        for w,v in r['footwork'].items():foot[w].update(v)
        for a,b,dt in r['transitions']:edges[(a,b)].append(dt)
    report=dict(version='0.7.9',new_unique_demos=len(records),parsed=len(valid),errors=[r for r in reports if 'error' in r],
        reserve_matches=len(matches),combined_matches=len(matches+prior),
        demos_with_selected_pov=sum(bool(r['observed_selected_clients']) for r in valid),
        different_winner_and_damage_leader=sum(bool(m['winner_clients'] and m['damage_leader_clients'] and set(m['winner_clients'])!=set(m['damage_leader_clients'])) for m in matches),
        accuracy_reserve={c:accuracy_table(matches,c) for c in ['winner','damage_leader']},
        accuracy_combined={c:accuracy_table(matches+prior,c) for c in ['winner','damage_leader']},
        footwork={k:dict(v) for k,v in foot.items()},start_jumps=len(jumps),full4s_starts=len(full),
        jump_metrics={k:summary([j[k] for j in jumps]) for k in ['pre_jump_speed','first_air_max_speed','second_air_max_speed','peak_2s','peak_4s']},
        best_observed_full4s=max(full,key=lambda j:j['peak_4s']) if full else None,
        resource_transitions=[dict(sequence=list(k),n=len(v),median_ms=percentile(v,.5),p90_ms=percentile(v,.9)) for k,v in sorted(edges.items(),key=lambda kv:-len(kv[1]))[:30]],
        opening_examples=[dict(demo_id=r['demo_id'],**o) for r in valid for o in r['openings'] if o['sequence']][:50],
        raw_input_verified=False,physics_verified=False,winning_strength_proven=False,
        limitations=['Movement only for recorded POVs of selected clients; no invisible POV reconstruction','Winner and damage-leader tables overlap and must not be added as independent samples','Zero shots excluded; zero accuracy with shots retained','No grenade accuracy tuning; splash hit semantics differ from hitscan','Historical protocols converted for extraction; movement physics equivalence unverified','Best observed speed is a candidate, not a verified attainable route benchmark'],
        pipeline_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (ROOT/'docs/training/RESERVE200_RESEARCH_079.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:report[k] for k in ['new_unique_demos','parsed','reserve_matches','combined_matches','different_winner_and_damage_leader','start_jumps','full4s_starts']}),flush=True)
if __name__=='__main__':main()
