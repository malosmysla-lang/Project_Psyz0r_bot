"""Re-extract the 500 saved top-player originals; never relabel old JSON as fresh."""
import json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CORPUS=ROOT/'демки для обучения/RESTORED_PRO_CORPUS_20261019'
OUT=ROOT/'out/reanalysis-top500';OUT.mkdir(parents=True,exist_ok=True)
def main():
    manifest=json.loads((ROOT/'docs/training/ZTN_TOP500_MANIFEST_20261019.json').read_text(encoding='utf-8'))
    (CORPUS/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    ps=[];streams=[]
    for shard in range(4):
        f=(OUT/f'worker{shard}.log').open('w',encoding='utf-8');streams.append(f)
        ps.append(subprocess.Popen([sys.executable,str(ROOT/'tools/analyze_bloodrun_corpus.py'),'--corpus',str(CORPUS),'--output',str(OUT),'--shard-index',str(shard),'--shard-count','4'],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT))
    codes=[p.wait() for p in ps]
    for f in streams:f.close()
    if any(codes):raise RuntimeError(f'Workers failed: {codes}')
    rows=[]
    for shard in range(4):rows+=json.loads((OUT/f'analysis_index_shard{shard}.json').read_text(encoding='utf-8'))['records']
    report={'records':rows,'recovered_originals':True,'parsed':sum(r['status']=='parsed' for r in rows),'total':len(rows)}
    (OUT/'analysis_index.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    (ROOT/'docs/training/REANALYSIS_TOP500_076.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Fresh extraction:',report['parsed'],'/',len(rows),flush=True)
if __name__=='__main__':main()
