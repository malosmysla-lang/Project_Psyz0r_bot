"""Four independent UDT processes; disjoint demo folders and per-worker indexes."""
import json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'out/bloodrun_top500_20261019'
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    old=OUT/'analysis_index.json'
    # Seed worker caches; preserve only complete successfully parsed records.
    cached=json.loads(old.read_text(encoding='utf-8'))['records'] if old.exists() else []
    manifest=json.loads((ROOT/'демки для обучения/BloodRun_top500_20261019/manifest.json').read_text(encoding='utf-8'))['records']
    processes=[];streams=[]
    for shard in range(4):
        ids={r['archive_id'] for i,r in enumerate(manifest) if i%4==shard}
        seed=[r for r in cached if r['archive_id'] in ids and r['status']=='parsed']
        (OUT/f'analysis_index_shard{shard}.json').write_text(json.dumps(dict(records=seed)),encoding='utf-8')
        stream=(OUT/f'worker{shard}.log').open('w');streams.append(stream)
        processes.append(subprocess.Popen([sys.executable,'tools/analyze_bloodrun_corpus.py','--corpus',str(ROOT/'демки для обучения/BloodRun_top500_20261019'),'--output',str(OUT),'--shard-index',str(shard),'--shard-count','4'],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT))
    codes=[p.wait() for p in processes]
    for stream in streams:stream.close()
    if any(codes):raise RuntimeError(f'Worker failures {codes}')
    records=[]
    for shard in range(4):records+=json.loads((OUT/f'analysis_index_shard{shard}.json').read_text(encoding='utf-8'))['records']
    if len(records)!=len(manifest) or len({r['archive_id'] for r in records})!=len(manifest):raise RuntimeError('Incomplete or duplicate worker index')
    old.write_text(json.dumps(dict(records=records),ensure_ascii=False,indent=2),encoding='utf-8')
    (ROOT/'docs/training/ZTN_TOP500_ANALYSIS_20261019.json').write_bytes(old.read_bytes())
    print('Completed',len(records),'records; parsed',sum(r['status']=='parsed' for r in records),flush=True)
if __name__=='__main__':main()
