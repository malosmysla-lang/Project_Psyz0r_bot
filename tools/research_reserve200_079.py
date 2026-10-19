"""Extract 200 saved originals outside the top500; preserve hashes and provenance."""
import concurrent.futures as cf
import hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'демки для обучения/RESTORED_PRO_CORPUS_20261019'
OUT=ROOT/'out/reserve200-079'
MANIFEST=ROOT/'docs/training/RESERVE200_079_MANIFEST.json'

def metadata(record):
    folder=OUT/str(record['archive_id'])/'metadata';folder.mkdir(parents=True,exist_ok=True)
    demo=SOURCE/record['filename']
    run=subprocess.run([str(ROOT/'tools/udt/bin/UDT_json.exe'),'-a=gsdm','-t=1','-o='+str(folder),str(demo)],capture_output=True,timeout=120)
    return dict(archive_id=record['archive_id'],ok=run.returncode==0 and (folder/(demo.stem+'.json')).exists())

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    old=json.loads((ROOT/'docs/training/ZTN_TOP500_MANIFEST_20261019.json').read_text(encoding='utf-8'))['records']
    excluded={r['sha256'] for r in old};chosen=[]
    # Original manifests contain provenance for the 400 originals outside top500.
    for name in ['BLOODRUN_300_MANIFEST_20261019.json','BLOODRUN_DOWNLOAD_MANIFEST.json']:
        for r in json.loads((ROOT/'docs/training'/name).read_text(encoding='utf-8'))['records']:
            if r['sha256'] in excluded or not (SOURCE/r['filename']).exists():continue
            if hashlib.sha256((SOURCE/r['filename']).read_bytes()).hexdigest()!=r['sha256']:raise ValueError('Original hash mismatch')
            chosen.append(r);excluded.add(r['sha256'])
            if len(chosen)==200:break
        if len(chosen)==200:break
    if len(chosen)!=200:raise RuntimeError('Fewer than 200 verified reserve originals')
    MANIFEST.write_text(json.dumps(dict(records=chosen,not_in_top500=True,new_downloads=False),ensure_ascii=False,indent=2),encoding='utf-8')
    streams=[];workers=[]
    for shard in range(4):
        stream=(OUT/f'worker{shard}.log').open('w');streams.append(stream)
        workers.append(subprocess.Popen([sys.executable,'tools/analyze_bloodrun_corpus.py','--corpus',str(SOURCE),'--manifest',str(MANIFEST),'--output',str(OUT),'--shard-index',str(shard),'--shard-count','4'],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT))
    codes=[p.wait() for p in workers]
    for f in streams:f.close()
    if any(codes):raise RuntimeError(str(codes))
    records=[]
    for shard in range(4):records+=json.loads((OUT/f'analysis_index_shard{shard}.json').read_text(encoding='utf-8'))['records']
    (OUT/'analysis_index.json').write_text(json.dumps(dict(records=records),indent=2),encoding='utf-8')
    print('SNAPSHOT_EXTRACTION',sum(r['status']=='parsed' for r in records),'/',len(records),flush=True)
    with cf.ThreadPoolExecutor(max_workers=4) as pool:
        meta=list(pool.map(metadata,chosen))
    (OUT/'metadata_index.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
    print('METADATA',sum(r['ok'] for r in meta),'/',len(meta),flush=True)
if __name__=='__main__':main()
