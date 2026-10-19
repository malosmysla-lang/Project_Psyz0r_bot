"""Validate corpus maps and extract observed own-POV approaches without live training."""
import argparse
import ctypes as c
import gzip
import hashlib
import json
import math
import subprocess
from collections import Counter,deque
from pathlib import Path
try:
    from .extract_movement import extract
    from .audit_rocketjumps import ITEMS
except ImportError:
    from extract_movement import extract
    from audit_rocketjumps import ITEMS
ROOT=Path(__file__).resolve().parents[1]
CORPUS=ROOT/'демки для обучения'/'BloodRun_100'
OUT=ROOT/'out'/'bloodrun_corpus'
def item_map(demo):
    dll=c.CDLL(str(ROOT/'tools/udt/bin/UDT.dll'));dll.udtInitLibrary()
    dll.udtGetProtocolByFilePath.argtypes=[c.c_char_p];dll.udtGetProtocolByFilePath.restype=c.c_uint32
    proto=dll.udtGetProtocolByFilePath(str(demo).encode())
    f=dll.udtGetUDTMagicNumber;f.argtypes=[c.POINTER(c.c_int32),c.c_uint32,c.c_int32,c.c_uint32,c.c_uint32];f.restype=c.c_int32
    mapping={}
    for i in range(256):
        v=c.c_int32()
        if f(c.byref(v),12,i,proto,0)==0 and v.value in ITEMS:mapping[i]=ITEMS[v.value]
    dll.udtShutDownLibrary();return mapping

def active_pov(x):
    return x["pm_type"]==0 or (x["pm_type"]==2 and bool(x.get("pm_flags",0)&4096))

def main():
    global CORPUS, OUT
    ap=argparse.ArgumentParser();ap.add_argument('--corpus',type=Path,default=CORPUS);ap.add_argument('--output',type=Path,default=OUT)
    ap.add_argument('--shard-index',type=int,default=0);ap.add_argument('--shard-count',type=int,default=1);args=ap.parse_args()
    if not 0<=args.shard_index<args.shard_count:ap.error('Invalid shard')
    CORPUS=args.corpus.resolve();OUT=args.output.resolve()
    OUT.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((CORPUS/'manifest.json').read_text(encoding='utf-8'));reports=[]
    index=OUT/('analysis_index.json' if args.shard_count==1 else f'analysis_index_shard{args.shard_index}.json')
    manifest['records']=[r for i,r in enumerate(manifest['records']) if i%args.shard_count==args.shard_index]
    cached={r['archive_id']:r for r in json.loads(index.read_text(encoding='utf-8'))['records']} if index.exists() else {}
    for n,record in enumerate(manifest['records'],1):
        if record['archive_id'] in cached and cached[record['archive_id']]['status']=='parsed' and cached[record['archive_id']].get('extractor_revision')==2 and cached[record['archive_id']].get('source_sha256')==record['sha256'] and hashlib.sha256((CORPUS/record['filename']).read_bytes()).hexdigest()==record['sha256']:
            reports.append(cached[record['archive_id']]);continue
        demo=CORPUS/record['filename'];folder=OUT/str(record['archive_id']);folder.mkdir(exist_ok=True)
        try:
            run=subprocess.run([str(ROOT/'tools/udt/bin/UDT_json.exe'),'-a=gm','-t=1','-o='+str(folder),str(demo)],capture_output=True,timeout=120)
            if run.returncode:raise RuntimeError('UDT JSON export failed')
            data=json.loads((folder/(demo.stem+'.json')).read_text(encoding='utf-8'));states=data['gameStates'];maps=sorted({s.get('configStringValues',{}).get('mapname','unknown') for s in states})
            if not maps or not {m.lower() for m in maps}<={'bloodrun','ztntourney1'}:raise ValueError('Unexpected recorded maps: '+str(maps))
            analysis_demo=demo;conversion=None
            if demo.suffix.lower() in ('.dm_73','.dm_90'):
                converted=folder/'converted';converted.mkdir(exist_ok=True)
                run=subprocess.run([str(ROOT/'tools/udt/bin/UDT_converter.exe'),'-p=91','-t=1','-o='+str(converted),str(demo)],capture_output=True,timeout=120)
                analysis_demo=converted/(demo.stem+'.dm_91')
                if run.returncode or not analysis_demo.exists():raise RuntimeError('UDT protocol conversion failed')
                conversion=dict(source_protocol=demo.suffix,tool='UDT_converter 1.3.1',converted_sha256=hashlib.sha256(analysis_demo.read_bytes()).hexdigest(),physics_verified=False)
            snapshots=folder/'snapshots.jsonl';summary=extract(analysis_demo,snapshots,ROOT/'tools/udt/bin/UDT.dll')
            if hashlib.sha256(demo.read_bytes()).hexdigest()!=record['sha256']:raise ValueError('Input SHA differs from manifest')
            mapping=item_map(analysis_demo);window=deque();prior=None;routes=[];counts=Counter();positions=[];active=0
            with snapshots.open() as source:
                for line in source:
                    x=json.loads(line);identity=(x['segment'],x['client'],x['game_state_number'])
                    if not active_pov(x) or x['health'] is None or x['health']<=0: window.clear();prior=None;continue
                    if prior is not None and (identity!=(prior['segment'],prior['client'],prior['game_state_number']) or not 0<x['time_ms']-prior['time_ms']<=100 or math.dist(x['position'],prior['position'])>256):window.clear()
                    active+=1;window.append(x)
                    while window and x['time_ms']-window[0]['time_ms']>3000:window.popleft()
                    for e in x['events']:
                        if e['udt_event_id'] not in (2,3) or e['parameter'] not in mapping:continue
                        kind=mapping[e['parameter']];counts[kind]+=1
                        if len(window)<2:continue
                        routes.append(dict(kind=kind,item_protocol_id=e['parameter'],pickup_ms=x['time_ms'],client=x['client'],segment=x['segment'],position_semantics='player_at_pickup',geometry_verified=False,physics_verified=False,ready_for_execution=False,points=[dict(t=y['time_ms'],p=y['position'],v=y['velocity'],angles=y['viewangles'],weapon=y['weapon_id'],ground=y['ground_entity']) for y in window]))
                    prior=x
            with gzip.open(folder/'observed_approaches.json.gz','wt',encoding='utf-8') as target:json.dump(dict(source_sha256=record['sha256'],map='bloodrun',physics='unknown',routes=routes),target)
            with snapshots.open('rb') as source,gzip.open(folder/'snapshots.jsonl.gz','wb') as target:
                import shutil;shutil.copyfileobj(source,target)
            snapshots.unlink()
            reports.append(dict(archive_id=record['archive_id'],filename=record['filename'],source_sha256=record['sha256'],conversion=conversion,maps=maps,status='parsed',snapshots=summary['snapshots'],segments=summary['segments'],active_pov_samples=active,pickups=dict(counts),approaches=len(routes),parser='UDT 1.3.1',physics_verified=False,extractor_revision=2))
        except Exception as e:reports.append(dict(archive_id=record['archive_id'],status='failed',error=str(e)))
        index.write_text(json.dumps(dict(records=reports),ensure_ascii=False,indent=2),encoding='utf-8')
        if n%5==0 or n==len(manifest['records']): print('Analyzed',n,'/',len(manifest['records']),'parsed',sum(r['status']=='parsed' for r in reports),flush=True)
    index.write_text(json.dumps(dict(records=reports),ensure_ascii=False,indent=2),encoding='utf-8')
if __name__=='__main__':main()
