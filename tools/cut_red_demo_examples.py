"""Create local playable dm_91 excerpts; never modify source recordings."""
import gzip
import hashlib
import json
import math
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main():
    output=ROOT/'out/red_approaches/demo_clips';output.mkdir(parents=True,exist_ok=True)
    sources=list((ROOT/'\u0434\u0435\u043c\u043a\u0438 \u0434\u043b\u044f \u043e\u0431\u0443\u0447\u0435\u043d\u0438\u044f').rglob('*.dm_91'))
    bysha={hashlib.sha256(p.read_bytes()).hexdigest():p for p in sources}
    audit=json.loads((ROOT/'docs/training/ZTN_solo_01_rocketjumps.json').read_text())
    jobs=[]
    for r in audit['results']:
        if r.get('status')=='success' and any(p['kind']=='red' for p in r.get('pickups',[])):
            jobs.append(dict(kind='owner_rocketjump_red',source_sha256=audit['demo_sha256'],
                             start_ms=r['start_ms']-2000,end_ms=max(p['time_ms'] for p in r['pickups'])+2000))
    with gzip.open(ROOT/'out/red_approaches/all_episodes.json.gz','rt') as f:episodes=json.load(f)
    seen=set()
    for e in episodes:
        if e['category']!='longjump_candidate' or e['source_sha256'] in seen:continue
        metadata=next(p for p in (ROOT/'out'/e['corpus']/e['demo_id']).glob('*.json') if p.name!='snapshots.summary.json')
        if len(json.loads(metadata.read_text(encoding='utf-8-sig'))['gameStates'])!=1:continue
        seen.add(e['source_sha256'])
        jobs.append(dict(kind='longjump_candidate_red',source_sha256=e['source_sha256'],
                         start_ms=e['start_ms']-1000,end_ms=e['pickup_ms']+2000))
        if len(seen)>=6:break
    manifest=[]
    for i,job in enumerate(jobs):
        source=bysha.get(job['source_sha256'])
        if source is None:
            fallback=Path('C:/Program Files (x86)/Steam/steamapps/common/Quake Live/76561197961758497/baseq3/demos/nekitz0r_ZTN_solo_01.dm_91')
            if fallback.exists() and hashlib.sha256(fallback.read_bytes()).hexdigest()==job['source_sha256']:source=fallback
        if source is None:raise FileNotFoundError('Original demo missing: '+job['source_sha256'])
        dest=output/f'{i+1:02d}_{job["kind"]}';dest.mkdir(exist_ok=False)
        subprocess.run([str(ROOT/'tools/udt/bin/UDT_cutter.exe'),'t','-q','-o='+str(dest),'-g=0',
                        '-s='+str(max(0,job['start_ms']//1000)),'-e='+str(math.ceil(job['end_ms']/1000)),str(source)],check=True)
        clips=list(dest.glob('*.dm_91'))
        if len(clips)!=1 or clips[0].stat().st_size<100:raise RuntimeError('No playable clip generated')
        manifest.append(dict(**job,clip=clips[0].relative_to(ROOT/'out').as_posix(),
                             clip_sha256=hashlib.sha256(clips[0].read_bytes()).hexdigest()))
    (ROOT/'docs/training/BLOODRUN_RED_CLIPS.json').write_text(json.dumps(manifest,indent=2))
    print('Created local demo clips:',len(manifest))


if __name__=='__main__':main()
