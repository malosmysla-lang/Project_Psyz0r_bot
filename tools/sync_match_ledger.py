"""Publish only the sanitized server ledger, using an isolated Git worktree."""
import argparse,datetime,hashlib,json,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'out/live-ledger';WORK=ROOT/'out/live-ledger-worktree'
LEDGER='docs/training/MATCH_LEDGER.json'
REMOTE='qlserver@78.17.9.235:/home/qlserver/psyz0r-bot/match-telemetry/public_matches.json'
def run(args,cwd=ROOT):return subprocess.run(args,cwd=cwd,check=True,capture_output=True,text=True)
def merge(seed,live):
    records={r['id']:r for r in seed['matches']}
    for r in live.get('matches',[]):
        if not str(r.get('id','')).startswith('live:') or not r.get('bot',{}).get('is_psyz'):continue
        r=dict(r,actor='Psyz0r');records[r['id']]=r
    result=dict(seed,matches=list(records.values()),automatic_learning=False,learning_status='not_proven_manual_policy_updates')
    return result
def sync(dry_run=False):
    OUT.mkdir(parents=True,exist_ok=True)
    raw=OUT/'server-public.json'
    run(['scp','-q','-o','BatchMode=yes',REMOTE,str(raw)])
    live=json.loads(raw.read_text(encoding='utf-8'))
    if not WORK.exists():run(['git','worktree','add','--detach',str(WORK),'origin/main'])
    actual=Path(run(['git','rev-parse','--show-toplevel'],WORK).stdout.strip()).resolve()
    if actual!=WORK.resolve():raise RuntimeError('Refusing to switch a non-dedicated worktree')
    run(['git','fetch','origin','main'],WORK);run(['git','switch','--detach','origin/main'],WORK)
    target=WORK/LEDGER;seed=json.loads(target.read_text(encoding='utf-8'));updated=merge(seed,live)
    changed=updated['matches']!=seed['matches']
    if changed and not dry_run:
        updated['updated_at']=datetime.datetime.now(datetime.timezone.utc).isoformat()
        target.write_text(json.dumps(updated,ensure_ascii=False,indent=2),encoding='utf-8')
        run(['git','add','--',LEDGER],WORK);run(['git','commit','-m','data: update completed Psyz0r duel ledger'],WORK)
        run(['git','push','origin','HEAD:main'],WORK)
    status=dict(checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),changed=changed,dry_run=dry_run,live_matches=len(live.get('matches',[])),total_matches=len(updated['matches']))
    (OUT/'status.json').write_text(json.dumps(status,indent=2),encoding='utf-8')
    print(json.dumps(status),flush=True)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--once',action='store_true');ap.add_argument('--dry-run',action='store_true');a=ap.parse_args()
    while True:
        try:sync(a.dry_run)
        except Exception as e:
            # Do not log command output: credential helpers or remote config
            # could include account-specific diagnostics. Keep failures bounded.
            OUT.mkdir(parents=True,exist_ok=True);(OUT/'error.txt').write_text(type(e).__name__+'\n',encoding='utf-8');print('Ledger sync failed; retrying',flush=True)
            if a.once:raise
        if a.once:break
        time.sleep(20)
if __name__=='__main__':main()
