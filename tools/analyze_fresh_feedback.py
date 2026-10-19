"""Preserve two completed owner demos and correlate POV stats with bot console telemetry."""
import collections,hashlib,json,re,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
GAME=Path('C:/Program Files (x86)/Steam/steamapps/common/Quake Live')
OUT=ROOT/'out/feedback-078';OUT.mkdir(parents=True,exist_ok=True)

def main():
    sources=sorted(GAME.rglob('*vs-Psyz0r_bot-bloodrun-*.dm_91'),key=lambda p:p.stat().st_mtime,reverse=True)[:2]
    assert len(sources)==2
    records=[]
    for original in sources:
        before=original.stat();sha=hashlib.sha256(original.read_bytes()).hexdigest()
        saved=ROOT/'демки для обучения/RESTORED_DEMOS_20261019'/original.name
        visible=Path('C:/Users/user/Desktop/Quake SERVER/PsyZ0r-bot/demos')/original.name
        for dest in (saved,visible):
            dest.parent.mkdir(parents=True,exist_ok=True)
            if dest.exists():assert hashlib.sha256(dest.read_bytes()).hexdigest()==sha
            else:shutil.copy2(original,dest)
        assert original.stat().st_size==before.st_size and hashlib.sha256(original.read_bytes()).hexdigest()==sha
        folder=OUT/sha[:12];folder.mkdir(exist_ok=True)
        subprocess.run([sys.executable,str(ROOT/'tools/extract_one_demo.py'),str(saved),'--output',str(folder)],check=True)
        subprocess.run([sys.executable,str(ROOT/'tools/extract_movement.py'),str(saved),'--output',str(folder/'snapshots.jsonl')],check=True)
        meta=json.loads((folder/(saved.stem+'.json')).read_text(encoding='utf-8-sig'))
        intervals=[dict(game_state=i+1,start=m['startTime'],end=m['endTime']) for i,gs in enumerate(meta.get('gameStates',[])) for m in gs.get('matches',[])]
        players=[p for m in meta.get('matchStats',[]) for p in m.get('playerStats',[])]
        # Собственные POV-кадры не выдаём за движение бота. Для него отдельный серверный лог.
        pov=collections.Counter();speeds=[];shots=collections.Counter();angles=[];prior=None
        for line in (folder/'snapshots.jsonl').open(encoding='utf-8'):
            row=json.loads(line)
            if not any(x['game_state']==row['game_state_number'] and x['start']<=row['time_ms']<=x['end'] for x in intervals):continue
            pov[str(row['client'])]+=1;speeds.append(row['speed_xy'])
            for e in row.get('events',[]):
                if e.get('kind')=='weapon_fired':shots[str(row['weapon_id'])]+=1
        records.append(dict(demo=saved.name,sha256=sha,intervals=intervals,player_stats=players,pov_frames=dict(pov),pov_max_speed=max(speeds,default=0),pov_shots=dict(shots),raw_input_verified=False))
    raw=subprocess.check_output(['ssh','-o','BatchMode=yes','qlserver@78.17.9.235','tail -n 100000 /home/qlserver/psyz0r-test-server-home/console.log'])
    (OUT/'server-console.log').write_bytes(raw)
    log=raw.decode(errors='replace').splitlines()
    # После перезагрузки карты serverTime повторяется. Не складываем старые
    # smoke-прогоны с текущими матчами: выбираем последнюю подходящую эпоху.
    epochs=[[]];last_nav=None
    for line in log:
        mt=re.match(r'PSYZ_NAV t=(\d+)',line)
        if mt:
            t=int(mt[1])
            if last_nav is not None and t<last_nav-1000:epochs.append([])
            last_nav=t
        epochs[-1].append(line)
    for record in records:
        intervals=record['intervals']
        candidates=[]
        for index,epoch in enumerate(epochs):
            times=[int(m[1]) for s in epoch if (m:=re.match(r'PSYZ_NAV t=(\d+)',s))]
            if times:
                coverage=sum(max(0,min(max(times),x['end'])-max(min(times),x['start'])) for x in intervals)
                candidates.append((coverage,index,epoch))
        coverage,index,epoch=max(candidates,key=lambda c:(c[0],c[1]))
        selected=[]
        for line in epoch:
            mt=re.search(r'\bt=(\d+)',line)
            if mt and any(x['start']<=int(mt[1])<=x['end'] for x in intervals):selected.append(line)
        counts=collections.Counter(re.match(r'(PSYZ_[A-Z_]+)',s)[1] for s in selected if re.match(r'(PSYZ_[A-Z_]+)',s))
        pickups=collections.Counter(re.search(r'class=(\S+)',s)[1] for s in selected if s.startswith('PSYZ_PICKUP ') and 'class=' in s)
        stalls=[];window=[];target=-1
        for line in selected:
            if line.startswith('PSYZ_TARGET '):target=int(re.search(r'entity=(-?\d+)',line)[1])
            if not line.startswith('PSYZ_NAV '):continue
            m=re.search(r't=(\d+) pos=([^ ]+) .*health=(-?\d+)',line)
            if not m:continue
            now=int(m[1]);pos=[float(v) for v in m[2].split(',')]
            if int(m[3])<=0:window=[];continue
            if window and (now-window[-1][0]>500 or sum((a-b)**2 for a,b in zip(pos,window[0][1]))>32**2):
                if window[-1][0]-window[0][0]>=1500:stalls.append(dict(start=window[0][0],end=window[-1][0],position=window[0][1],target=window[0][2]))
                window=[]
            window.append((now,pos,target))
        if window and window[-1][0]-window[0][0]>=1500:stalls.append(dict(start=window[0][0],end=window[-1][0],position=window[0][1],target=window[0][2]))
        record['server_correlation']=dict(log_epoch=index,coverage_ms=coverage,counts=dict(counts),actual_pickups=dict(pickups),stationary_candidates=stalls,nav_recovery=[s for s in selected if s.startswith('PSYZ_NAV_RECOVERY ')],major_clock_samples=[s for s in selected if s.startswith('PSYZ_ITEM_TIMER ')][-30:])
        (OUT/(record['sha256'][:12]+'-correlation.log')).write_text('\n'.join(selected),encoding='utf-8')
    result=dict(records=records,limits=['POV movement is the owner, not automatically the bot','Server-time correlation can be ambiguous across repeated map restarts; inspect match/state before conclusions','Stationary episodes may include deliberate combat/hold; not every episode is a technical stall','No raw mouse/WASD or hidden enemy tracker'])
    (ROOT/'docs/training/FRESH_FEEDBACK_078.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps([dict(demo=r['demo'],players=[dict(name=p.get('cleanName',p.get('name')),kills=p.get('kills'),deaths=p.get('deaths'),red=p.get('redArmorPickups'),mega=p.get('megaHealthPickups'),yellow=p.get('yellowArmorPickups')) for p in r['player_stats']],server=r['server_correlation']['actual_pickups'],stationary=len(r['server_correlation']['stationary_candidates'])) for r in records],ensure_ascii=True))
if __name__=='__main__':main()
