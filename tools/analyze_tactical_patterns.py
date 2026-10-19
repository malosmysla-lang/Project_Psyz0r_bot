"""Observed resource transitions, footwork, pre-shot aim and multi-gun kill candidates.

No raw keys/mouse input, enemy positions or hit attribution are inferred.
All candidates remain offline until geometry and runtime sensors are validated.
"""
import argparse,collections,concurrent.futures as cf,gzip,hashlib,json,math,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
WEAPONS={1:'gauntlet',2:'machinegun',3:'shotgun',4:'grenade',5:'rocket',6:'lightning',7:'railgun',8:'plasma'}
MAJORS={'red','mega'}
STRATEGIC={'red','mega','yellow','green','rocket','lightning','railgun','health','health_large'}

def percentile(values,q):
    if not values:return None
    xs=sorted(values);p=(len(xs)-1)*q;a=int(p);b=min(a+1,len(xs)-1)
    return round(xs[a]+(xs[b]-xs[a])*(p-a),3)

def angle(a,b):return (a-b+180)%360-180

def continuous(a,b):
    return (a['client']==b['client'] and a['segment']==b['segment'] and
            a['game_state_number']==b['game_state_number'] and
            0<b['time_ms']-a['time_ms']<=100 and
            a.get('health',0)>0 and b.get('health',0)>0 and
            a.get('pm_type')==b.get('pm_type') and b.get('pm_type') in (0,2) and
            math.dist(a['position'],b['position'])<=128)

def foot_pattern(row):
    yaw=math.radians(row['viewangles'][1]);vx,vy=row['velocity'][:2]
    forward=vx*math.cos(yaw)+vy*math.sin(yaw)
    right=vx*math.sin(yaw)-vy*math.cos(yaw)
    if math.hypot(vx,vy)<35:kind='pause'
    elif abs(right)>abs(forward)*1.4:kind='lateral'
    elif forward>abs(right)*1.4:kind='forward'
    elif forward<-abs(right)*1.4:kind='backward'
    else:kind='diagonal'
    return kind,right

def preaim_window(rows,shot):
    """Measure a continuous 250ms pre-shot view, without a target/hit claim."""
    window=[r for r in rows if shot['time_ms']-250<=r['time_ms']<shot['time_ms']]
    if not window or shot['time_ms']-window[0]['time_ms']<225:return None
    seq=window+[shot]
    if any(not continuous(a,b) for a,b in zip(seq,seq[1:])):return None
    yaw=max(abs(angle(r['viewangles'][1],shot['viewangles'][1])) for r in window)
    pitch=max(abs(angle(r['viewangles'][0],shot['viewangles'][0])) for r in window)
    return dict(yaw_span=yaw,pitch_span=pitch,held=yaw<=6 and pitch<=4,
                moving=percentile([r['speed_xy'] for r in window],.5)>=60)

def kill_sequence(shots,kill,state,client,segment):
    """Only own observed shots; multiple guns do not prove damage to this victim."""
    if kill['gameStateNumber']!=state or kill['attackerClientNumber']!=client:return None
    chain=[]
    for s in shots:
        if (s['state']==state and s['client']==client and s['segment']==segment and
                kill['serverTime']-5000<=s['t']<=kill['serverTime']):
            if not chain or chain[-1]!=s['weapon']:chain.append(s['weapon'])
    return chain

def resource_sequences(routes,valid_life,strategic_only=False):
    """Keep pickup chains within one observed life, never connect two POVs."""
    groups=collections.defaultdict(list)
    for r in routes:
        if strategic_only and r['kind'] not in STRATEGIC:continue
        t=r['pickup_ms'];key=(r['client'],r['segment'],t)
        life=valid_life.get(key)
        if life is not None:groups[(r['client'],r['segment'],life)].append(r)
    transitions=[];ngrams=[];dwells=[]
    for key,seq in groups.items():
        seq=sorted({(r['pickup_ms'],r['kind']):r for r in seq}.values(),key=lambda r:r['pickup_ms'])
        for a,b in zip(seq,seq[1:]):
            dt=b['pickup_ms']-a['pickup_ms']
            if 0<dt<=30000:transitions.append((a['kind'],b['kind'],dt))
        for i in range(len(seq)-2):
            trio=seq[i:i+3]
            if all(0<b['pickup_ms']-a['pickup_ms']<=30000 for a,b in zip(trio,trio[1:])):
                ngrams.append((tuple(r['kind'] for r in trio),trio[-1]['pickup_ms']-trio[0]['pickup_ms']))
        for r in seq:
            if r['kind'] not in MAJORS or not r['points']:continue
            pts=r['points'];end=pts[-1];start=end['t']
            # Stationary within 64u of pickup is a dwell candidate, not proof of stopwatch.
            for p in reversed(pts):
                if end['t']-p['t']>2000 or math.dist(p['p'],end['p'])>64 or math.hypot(*p['v'][:2])>=35:break
                start=p['t']
            dwells.append({'kind':r['kind'],'pickup_ms':r['pickup_ms'],'stationary_ms':end['t']-start,'position':end['p'],'timer_verified':False})
    return transitions,ngrams,dwells

def inspect(task):
    folder,record=task;folder=Path(folder);ident=folder.name
    meta_folder=ROOT/'out/tactical-research/metadata'/ident;meta_folder.mkdir(parents=True,exist_ok=True)
    original=ROOT/'демки для обучения/RESTORED_PRO_CORPUS_20261019'/record['filename']
    mp=meta_folder/(original.stem+'.json')
    try:
        if hashlib.sha256(original.read_bytes()).hexdigest()!=record['sha256']:raise RuntimeError('Original SHA-256 differs from corpus manifest')
        if not mp.exists():
            run=subprocess.run([str(ROOT/'tools/udt/bin/UDT_json.exe'),'-a=gsdm','-t=1','-o='+str(meta_folder.resolve()),str(original)],capture_output=True,timeout=90)
            if run.returncode or not mp.exists():raise RuntimeError('Metadata export failed')
        meta=json.loads(mp.read_text(encoding='utf-8-sig'))
        intervals={i+1:[(m['startTime'],m['endTime']) for m in s.get('matches',[])] for i,s in enumerate(meta.get('gameStates',[]))}
        kills=collections.defaultdict(list)
        for k in meta.get('obituaries',[]):
            if k.get('attackerClientNumber',-1)<0 or k.get('attackerClientNumber')==k.get('targetClientNumber'):continue
            kills[(k['gameStateNumber'],k['attackerClientNumber'])].append(k)
        for seq in kills.values():seq.sort(key=lambda k:k['serverTime'])
        kill_index=collections.Counter();shots=collections.deque();history=collections.deque(maxlen=24)
        prior=None;life=0;valid_life={};stats=collections.defaultdict(lambda:collections.Counter());switches=collections.Counter();anchors={};combos=[];preaim=[];spins=[]
        spin_rows=collections.deque();spin_sweep=0.;last_shot=-100000;last_fire_gun=None;last_gun=None;prior_valid=False
        with gzip.open(folder/'snapshots.jsonl.gz','rt',encoding='utf-8') as stream:
            for line in stream:
                row=json.loads(line);now=row['time_ms'];state=row['game_state_number'];client=row['client'];identity=(state,client)
                in_match=any(start<=now<=end for start,end in intervals.get(state,[]))
                valid=in_match and row.get('health',0)>0 and row.get('pm_type') in (0,2)
                if not valid:
                    if prior_valid:life+=1
                    prior_valid=False;prior=None;history.clear();shots.clear();spin_rows.clear();spin_sweep=0.;last_gun=None;last_fire_gun=None
                    continue
                prior_valid=True
                ok=prior is not None and continuous(prior,row)
                if not ok:
                    if prior is not None:life+=1
                    history.clear();shots.clear();spin_rows.clear();spin_sweep=0.;last_shot=-100000;last_gun=None;last_fire_gun=None
                valid_life[(client,row['segment'],now)]=life
                fired=any(e.get('kind')=='weapon_fired' for e in row.get('events',[]))
                gun=WEAPONS.get(row['weapon_id'],'unknown')
                if fired:
                    last_shot=now;last_fire_gun=gun;shots.append(dict(t=now,state=state,client=client,segment=row['segment'],weapon=gun))
                    if last_gun and last_gun!=gun:switches[last_gun+' → '+gun]+=1
                    last_gun=gun
                    if gun in {'rocket','railgun','lightning'}:
                        pre=preaim_window(history,row)
                        if pre:
                            preaim.append((gun,pre['held'],pre['moving'],pre['yaw_span']))
                            if pre['held']:
                                cell=(math.floor(row['position'][0]/128),math.floor(row['position'][1]/128),math.floor(row['position'][2]/64),gun)
                                a=anchors.setdefault(cell,dict(n=0,sin=0,cos=0,pitch=0,position=[0,0,0],examples=[]))
                                a['n']+=1;a['sin']+=math.sin(math.radians(row['viewangles'][1]));a['cos']+=math.cos(math.radians(row['viewangles'][1]));a['pitch']+=row['viewangles'][0]
                                for d in range(3):a['position'][d]+=row['position'][d]
                                if len(a['examples'])<2:
                                    start=next(start for start,end in intervals[state] if start<=now<=end)
                                    a['examples'].append(dict(time_ms=now,match_elapsed_ms=now-start,client=client,game_state=state,position=row['position'],viewangles=row['viewangles']))
                while shots and shots[0]['t']<now-5000:shots.popleft()
                if ok and now-last_shot<=100 and last_fire_gun==gun and gun in {'rocket','railgun','lightning'}:
                    dt=now-prior['time_ms'];pattern,side=foot_pattern(row);rate=abs(angle(row['viewangles'][1],prior['viewangles'][1]))*1000/dt
                    stats[gun]['firing_ms']+=dt;stats[gun][pattern+'_ms']+=dt;stats[gun]['ground_ms']+=dt*(row['ground_entity']!=1023);stats[gun]['steady_view_ms']+=dt*(rate<=60)
                queue=kills.get(identity,[]);ki=kill_index[identity]
                while ki<len(queue) and queue[ki]['serverTime']<=now:
                    k=queue[ki];ki+=1
                    if now-k['serverTime']>100 or not ok:continue
                    chain=kill_sequence(shots,k,state,client,row['segment'])
                    if not chain:continue
                    combos.append(dict(time_ms=k['serverTime'],client=client,target=k['targetClientNumber'],cause=k.get('causeOfDeath'),sequence=chain,multi_weapon=len(set(chain))>=2,same_target_damage_verified=False))
                    # The previous frag's firing sequence must not become evidence
                    # for another victim's combo after a fast respawn.
                    while shots and shots[0]['t']<=k['serverTime']:shots.popleft()
                kill_index[identity]=ki
                # Rare movement spin candidates: net yaw, no firing, no teleport and finite turn rate.
                if ok and now-last_shot>2000 and row['speed_xy']>=150 and abs(angle(row['viewangles'][1],prior['viewangles'][1]))*1000/(now-prior['time_ms'])<=1440:
                    if spin_rows:spin_sweep+=angle(row['viewangles'][1],spin_rows[-1]['viewangles'][1])
                    spin_rows.append(row)
                    while spin_rows and now-spin_rows[0]['time_ms']>2000:
                        first=spin_rows.popleft()
                        if spin_rows:spin_sweep-=angle(spin_rows[0]['viewangles'][1],first['viewangles'][1])
                    if len(spin_rows)>2:
                        sweep=spin_sweep
                        duration=now-spin_rows[0]['time_ms']
                        if 350<=abs(sweep)<=410 and 250<=duration<=2000:
                            spins.append(dict(start_ms=spin_rows[0]['time_ms'],end_ms=now,sweep_deg=round(sweep,2),position=row['position'],intent_verified=False));spin_rows.clear();spin_sweep=0.
                else:spin_rows.clear();spin_sweep=0.
                history.append(row);prior=row
        with gzip.open(folder/'observed_approaches.json.gz','rt',encoding='utf-8') as f:routes=json.load(f)['routes']
        transitions,ngrams,dwells=resource_sequences(routes,valid_life)
        macro_edges,macro_chains,_=resource_sequences(routes,valid_life,True)
        return dict(demo_id=ident,source_sha256=record['sha256'],stats={k:dict(v) for k,v in stats.items()},switches=dict(switches),preaim=preaim,anchors=[dict(cell=list(k),**v) for k,v in anchors.items()],combos=combos,transitions=transitions,ngrams=ngrams,macro_transitions=macro_edges,macro_ngrams=macro_chains,dwells=dwells,spins=spins)
    except Exception as e:return dict(demo_id=ident,error=str(e))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--limit',type=int,default=500);a=ap.parse_args()
    manifest=json.loads((ROOT/'docs/training/ZTN_TOP500_MANIFEST_20261019.json').read_text(encoding='utf-8'))['records'][:a.limit]
    tasks=[(str(ROOT/'out/reanalysis-top500'/str(r['archive_id'])),r) for r in manifest]
    out=ROOT/'out/tactical-research';out.mkdir(parents=True,exist_ok=True)
    reports=[]
    with cf.ProcessPoolExecutor(max_workers=4) as pool:
        for i,r in enumerate(pool.map(inspect,tasks),1):
            reports.append(r)
            (out/(r['demo_id']+'.json')).write_text(json.dumps(r),encoding='utf-8')
            if i%25==0:print('Tactical analysis',i,'/',len(tasks),flush=True)
    valid=[r for r in reports if 'error' not in r];foot=collections.defaultdict(collections.Counter);pre=collections.defaultdict(list);edges=collections.defaultdict(list);chains=collections.defaultdict(list);anchor_groups=collections.defaultdict(list);combo_counts=collections.Counter();spin_examples=[];dwell=collections.defaultdict(list)
    kills=0;multi=0;macro_edges=collections.defaultdict(list);macro_chains=collections.defaultdict(list)
    for r in valid:
        for w,s in r['stats'].items():foot[w].update(s)
        for w,held,moving,yaw in r['preaim']:pre[w].append((held,moving,yaw))
        for a,b,t in r['transitions']:edges[(a,b)].append((t,r['demo_id']))
        for chain,t in r['ngrams']:chains[tuple(chain)].append((t,r['demo_id']))
        for a,b,t in r['macro_transitions']:macro_edges[(a,b)].append((t,r['demo_id']))
        for chain,t in r['macro_ngrams']:macro_chains[tuple(chain)].append((t,r['demo_id']))
        for anchor in r['anchors']:anchor_groups[tuple(anchor['cell'])].append((anchor,r['demo_id']))
        for k in r['combos']:
            kills+=1
            if k['multi_weapon']:multi+=1;combo_counts[' → '.join(k['sequence'])]+=1
        for d in r['dwells']:dwell[d['kind']].append(d['stationary_ms'])
        spin_examples.extend(dict(demo_id=r['demo_id'],**s) for s in r['spins'])
    anchors=[]
    for key,rows in anchor_groups.items():
        n=sum(a['n'] for a,_ in rows);sources=sorted({ident for _,ident in rows})
        sin=sum(a['sin'] for a,_ in rows);cos=sum(a['cos'] for a,_ in rows);concentration=math.hypot(sin,cos)/n
        if n<8 or len(sources)<3 or concentration<.8:continue
        anchors.append(dict(cell=list(key[:3]),weapon=key[3],shots=n,demos=len(sources),source_ids=sources[:8],examples=[dict(demo_id=ident,**e) for a,ident in rows[:3] for e in a['examples'][:1]],yaw_deg=round(math.degrees(math.atan2(sin,cos)),2),pitch_deg=round(sum(a['pitch'] for a,_ in rows)/n,2),concentration=round(concentration,3),position=[round(sum(a['position'][d] for a,_ in rows)/n,2) for d in range(3)],geometry_verified=False,ready_for_execution=False))
    summary=dict(files=len(tasks),parsed=len(valid),errors=[r for r in reports if 'error' in r],method='In-match alive POV; continuity <=100ms; teleport/death boundaries reset aim/shot windows. No target-hit attribution or raw input.',footwork={w:dict(v) for w,v in foot.items()},preaim={w:dict(windows=len(v),held=sum(x[0] for x in v),held_while_moving=sum(x[0] and x[1] for x in v),yaw_span_p50=percentile([x[2] for x in v],.5)) for w,v in pre.items()},observed_kill_windows=kills,multi_weapon_before_kill=multi,multi_weapon_fraction=round(multi/kills,4) if kills else None,combo_sequences=combo_counts.most_common(20),resource_transitions=[dict(sequence=list(k),observations=len(v),demos=len({x[1] for x in v}),median_ms=percentile([x[0] for x in v],.5),p90_ms=percentile([x[0] for x in v],.9)) for k,v in sorted(edges.items(),key=lambda x:-len(x[1]))[:40]],resource_triplets=[dict(sequence=list(k),observations=len(v),demos=len({x[1] for x in v}),median_ms=percentile([x[0] for x in v],.5)) for k,v in sorted(chains.items(),key=lambda x:-len(x[1]))[:30]],stationary_before_major={k:dict(observations=len(v),median_ms=percentile(v,.5),p90_ms=percentile(v,.9),timer_verified=False) for k,v in dwell.items()},aim_anchors=sorted(anchors,key=lambda x:-x['shots'])[:80],movement_spin_candidates=len(spin_examples),spin_examples=spin_examples[:30],limitations=['Multi-gun shots before a kill do not prove damage by each gun to the same target','Dwell before pickup does not prove exact respawn timing or successful stopwatch','Aim anchors are view directions at player cells, not validated line-of-sight or spam targets','Never feed demo omniscience into a live enemy tracker','360 candidates do not establish player intention or superiority'])
    summary['macro_resource_transitions']=[dict(sequence=list(k),observations=len(v),demos=len({x[1] for x in v}),median_ms=percentile([x[0] for x in v],.5),p90_ms=percentile([x[0] for x in v],.9)) for k,v in sorted(macro_edges.items(),key=lambda x:-len(x[1]))[:40]]
    summary['macro_resource_triplets']=[dict(sequence=list(k),observations=len(v),demos=len({x[1] for x in v}),median_ms=percentile([x[0] for x in v],.5)) for k,v in sorted(macro_chains.items(),key=lambda x:-len(x[1]))[:30]]
    summary['pipeline_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    summary['combo_window_rule']='At most 5 seconds, cut after each observed own kill; no same-target damage proof'
    target=ROOT/'docs/training/TACTICAL_PATTERNS_077.json';target.write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:summary[k] for k in ['files','parsed','observed_kill_windows','multi_weapon_before_kill','movement_spin_candidates']}),flush=True)
if __name__=='__main__':main()
