"""Recompute opening and start-jump evidence across all available corpora."""
import json,subprocess,sys
from pathlib import Path
from analyze_strafe_starts import summary
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'out/audit074';CORPORA=['bloodrun_corpus','owner_bloodrun_corpus','bloodrun_additional_300_20261019','bloodrun_top500_20261019']
def main():
    OUT.mkdir(parents=True,exist_ok=True);jobs=[];streams=[]
    for shard in range(4):
        command=[sys.executable,'tools/analyze_openings.py','--shard-index',str(shard),'--shard-count','4','--output',str(OUT/f'opening{shard}.json')]
        for corpus in CORPORA:command+=['--corpus',corpus]
        stream=(OUT/f'opening{shard}.log').open('w');streams.append(stream)
        jobs.append(subprocess.Popen(command,cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT))
    if any(p.wait() for p in jobs):raise RuntimeError('Opening worker failed')
    openings=[]
    for shard in range(4):openings+=json.loads((OUT/f'opening{shard}.json').read_text())['records']
    target=ROOT/'docs/training/OPENINGS_ALL_074.json'
    target.write_text(json.dumps(dict(records=openings,counts=dict(total=len(openings),observed=sum(r['status']=='observed' for r in openings),complete=sum(r.get('completion')=='complete' for r in openings)),optimality_verified=False),indent=2),encoding='utf-8')
    print('OPENINGS COMPLETE',len(openings),flush=True)
    jobs=[]
    for shard in range(4):
        command=[sys.executable,'tools/analyze_strafe_starts.py',str(ROOT/'out'/CORPORA[0]),str(OUT/f'strafe{shard}.json'),'--shard-index',str(shard),'--shard-count','4']
        for corpus in CORPORA[1:]:command+=['--extra-corpus',str(ROOT/'out'/corpus)]
        stream=(OUT/f'strafe{shard}.log').open('w');streams.append(stream)
        jobs.append(subprocess.Popen(command,cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT))
    if any(p.wait() for p in jobs):raise RuntimeError('Strafe worker failed')
    reports=[json.loads((OUT/f'strafe{s}.json').read_text()) for s in range(4)]
    samples=[sample for report in reports for sample in report['samples']]
    fields=reports[0]['metrics']
    full=[s for s in samples if s['observed_horizon_ms']>=3900]
    best=max(full,key=lambda s:s['peak_4s']) if full else None
    report=dict(files_scanned=sum(r['files_scanned'] for r in reports),sample_count=len(samples),samples=samples,metrics={k:summary([s[k] for s in samples]) for k in fields},full_4s_samples=len(full),best_observed_4s_candidate=best,benchmark_tolerance_ups=15,raw_mouse_or_keys_verified=False,physics_verified=False)
    (ROOT/'docs/training/STRAFE_ALL_074.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    for stream in streams:stream.close()
    print('STRAFE COMPLETE',len(samples),'full4s',len(full),'best',best['peak_4s'] if best else None,flush=True)
if __name__=='__main__':main()
