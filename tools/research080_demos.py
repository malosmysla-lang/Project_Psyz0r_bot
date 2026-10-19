"""Preserve two fresh owner demos and inspect every POV in 200 cached demos."""
from pathlib import Path
import collections,json,gzip,hashlib,shutil,subprocess,sys,concurrent.futures as cf
from analyze_tactical_patterns import continuous,kill_sequence,preaim_window
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'out/research080';OUT.mkdir(exist_ok=True)
WEAPONS={1:'gauntlet',2:'machinegun',3:'shotgun',4:'grenade',5:'rocket',6:'lightning',7:'railgun',8:'plasma'}
def inspect(task):
    ident,meta_path,snap=task
    meta=json.loads(meta_path.read_text(encoding='utf-8-sig'));kills=collections.defaultdict(list)
    for k in meta.get('obituaries',[]):
        if k.get('attackerClientNumber',-1)>=0 and k.get('attackerClientNumber')!=k.get('targetClientNumber'):
            kills[(k['gameStateNumber'],k['attackerClientNumber'])].append(k)
    windows=[];history=collections.deque(maxlen=30);shots=collections.deque();prior=None;seen=set();rail=[];risk=[];last=None
    intervals={i+1:[(m['startTime'],m['endTime']) for m in s.get('matches',[])] for i,s in enumerate(meta.get('gameStates',[]))}
    opener=gzip.open if snap.suffix=='.gz' else open
    with opener(snap,'rt',encoding='utf-8') as f:
        for line in f:
            r=json.loads(line);now=r['time_ms'];state=r['game_state_number'];client=r['client']
            valid=r.get('health',0)>0 and r.get('pm_type') in (0,2) and any(a<=now<=b for a,b in intervals.get(state,[]))
            if not valid:prior=None;shots.clear();history.clear();continue
            if prior is None or not continuous(prior,r):shots.clear();history.clear()
            fired=any(e.get('kind')=='weapon_fired' for e in r.get('events',[]));gun=WEAPONS.get(r['weapon_id'],'unknown')
            if fired:
                shots.append(dict(t=now,state=state,client=client,segment=r['segment'],weapon=gun))
                if gun=='railgun':rail.append(dict(time_ms=now,position=r['position'],viewangles=r['viewangles'],preaim=preaim_window(history,r),health=r['health'],armor=r.get('armor')))
                if r['health']<70:risk.append(dict(time_ms=now,weapon=gun,health=r['health'],armor=r.get('armor'),position=r['position']))
            while shots and shots[0]['t']<now-5000:shots.popleft()
            for k in kills.get((state,client),[]):
                key=(state,client,k['serverTime'],k['targetClientNumber'])
                if key in seen or not 0<=now-k['serverTime']<=100:continue
                seen.add(key);seq=kill_sequence(shots,k,state,client,r['segment'])
                if seq:windows.append(dict(time_ms=k['serverTime'],state=state,client=client,target=k['targetClientNumber'],sequence=seq,multi_weapon=len(set(seq))>1,same_target_damage_verified=False))
                shots.clear()
            history.append(r);prior=r
    return dict(demo_id=str(ident),kill_windows=windows,rail_shots=rail,low_health_shots=risk,players=[p for m in meta.get('matchStats',[]) for p in m.get('playerStats',[])])
def main():
    sources=sorted(Path('C:/Program Files (x86)/Steam/steamapps/common/Quake Live/76561197961758497/baseq3/demos').glob('*vs-Psyz0r_bot-bloodrun-*.dm_91'),key=lambda p:p.stat().st_mtime,reverse=True)[:2]
    fresh=[];tasks=[]
    for p in reversed(sources):
        digest=hashlib.sha256(p.read_bytes()).hexdigest();folder=OUT/digest[:12];folder.mkdir(exist_ok=True)
        for target in [ROOT/'демки для обучения/OWNER_20261020'/p.name,Path('C:/Users/user/Desktop/Quake SERVER/PsyZ0r-bot/demos')/p.name]:
            target.parent.mkdir(parents=True,exist_ok=True)
            if not target.exists():shutil.copy2(p,target)
            assert hashlib.sha256(target.read_bytes()).hexdigest()==digest
        if not (folder/(p.stem+'.json')).exists():subprocess.run([sys.executable,'tools/extract_one_demo.py',str(p),'--output',str(folder)],check=True,stdout=subprocess.DEVNULL)
        if not (folder/'snapshots.jsonl').exists():subprocess.run([sys.executable,'tools/extract_movement.py',str(p),'--output',str(folder/'snapshots.jsonl')],check=True,stdout=subprocess.DEVNULL)
        result=inspect((p.name,folder/(p.stem+'.json'),folder/'snapshots.jsonl'));result.update(sha256=digest,owner_resource_concession= p==sources[0]);fresh.append(result)
    for r in json.loads((ROOT/'docs/training/RESERVE200_079_MANIFEST.json').read_text(encoding='utf-8'))['records']:
        folder=ROOT/'out/reserve200-079'/str(r['archive_id']);tasks.append((r['archive_id'],next((folder/'metadata').glob('*.json')),folder/'snapshots.jsonl.gz'))
    with cf.ThreadPoolExecutor(max_workers=4) as pool:pro=list(pool.map(inspect,tasks))
    counts=collections.Counter(' -> '.join(k['sequence']) for d in pro for k in d['kill_windows'] if k['multi_weapon'])
    result=dict(fresh=fresh,pro_files=len(pro),pro_observed_kills=sum(len(r['kill_windows']) for r in pro),pro_multi_weapon=sum(k['multi_weapon'] for r in pro for k in r['kill_windows']),combo_sequences=counts.most_common(),limits=['Observed shots before an own kill are combo candidates, not proof of damage by every gun to the same target','All available POVs included, not only winners; unavailable perspectives are not invented','Second chronological fresh demo tagged resource concession by owner'])
    (OUT/'all_pro_windows.json').write_text(json.dumps(pro,ensure_ascii=False),encoding='utf-8')
    (ROOT/'docs/training/RESEARCH_080.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(files=len(pro),kills=result['pro_observed_kills'],multi=result['pro_multi_weapon'],top=result['combo_sequences'][:10],fresh=[dict(demo=r['demo_id'],players=[{k:p.get(k) for k in ['cleanName','score','railgunAccuracy','redArmorPickups','megaHealthPickups']} for p in r['players']]) for r in fresh]),ensure_ascii=True))
if __name__=='__main__':main()
