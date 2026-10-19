"""Apply tested 0.7.8 only to an empty isolated 27961; back up all four files."""
import hashlib,json,re,shutil,subprocess,time
from pathlib import Path
STAGE=Path(__file__).resolve().parent
HOME=Path('/home/qlserver/psyz0r-test-server-home')
RUNTIME=Path('/home/qlserver/psyz0r-test-server/psyz_test/minqlx_nopy.so')
BUILD=Path('/home/qlserver/psyz0r-bot/build-078-20261019')
GUARD='/home/qlserver/psyz0r-bot/iteration-074/trial074_remote.py'
def run(*args):return subprocess.check_output(args,text=True).strip()
def guard():run('python3',GUARD,'--guard-only')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    guard();primary=run('systemctl','show','quakelive.service','--property=MainPID','--value')
    native=BUILD/'bin/minqlx.x64.so';plugin=HOME/'minqlx-plugins/psyz_chat.py'
    profile=HOME/'baseq3/zzz_psyz_profile.pk3';cfg=HOME/'baseq3/psyz_test.cfg'
    targets=[RUNTIME,plugin,profile,cfg]
    backup=Path('/home/qlserver/backups')/time.strftime('psyz-078-%Y%m%dT%H%M%SZ',time.gmtime());backup.mkdir()
    for p in targets:shutil.copy2(p,backup/p.name)
    settings={'qlx_psyzVersion':'0.7.8','qlx_psyzAllWeaponAim':'1','qlx_psyzAimHumanize':'1','bot_nochat':'1'}
    observations=json.loads((STAGE/'WINNER_ACCURACY_078.json').read_text())
    for w in observations['table']:
        if not w['eligible_for_aim_profile']:continue
        for suffix,key in [('Base','mean_match_accuracy'),('Min','min_accuracy'),('Max','max_accuracy')]:
            settings['qlx_psyzAcc'+str(w['weapon_id'])+suffix]=str(w[key])
    for weapon,value in {2:.35,3:.6,5:.8,6:1.25,7:.35,8:3.0}.items():settings['qlx_psyzAimError'+str(weapon)]=str(value)
    text=cfg.read_text()
    for key,value in settings.items():
        text=re.sub(r'^\s*set[as]?\s+'+re.escape(key)+r'\s+.*\n?','',text,flags=re.M)
    text+='\n// 0.7.8: Xaero-derived skill 5; free majors; independent stall escape; bilingual chat.\n'
    text+='// Accuracy values are empirical targets; aiming commands change, damage never does.\n'
    text+=''.join(f'set {k} "{v}"\n' for k,v in settings.items())
    guard();run('sudo','systemctl','stop','psyz0r-test.service')
    try:
        for source,target in [(native,RUNTIME),(STAGE/'psyz_chat.py',plugin),(STAGE/'zzz_psyz_profile.pk3',profile)]:
            tmp=target.with_suffix(target.suffix+'.078-new');shutil.copy2(source,tmp);tmp.replace(target)
        cfg.write_text(text)
        sock=HOME/'console.sock'
        if sock.exists():sock.unlink()
        run('sudo','systemctl','start','psyz0r-test.service');time.sleep(3)
        if run('systemctl','is-active','psyz0r-test.service')!='active':raise RuntimeError('Inactive test service')
    except Exception:
        run('sudo','systemctl','stop','psyz0r-test.service')
        for p in targets:shutil.copy2(backup/p.name,p)
        run('sudo','systemctl','start','psyz0r-test.service');raise
    assert sha(RUNTIME)==sha(native)
    assert run('systemctl','show','quakelive.service','--property=MainPID','--value')==primary
    report=dict(version='0.7.8',backup=str(backup),primary_pid=primary,test_pid=run('systemctl','show','psyz0r-test.service','--property=MainPID','--value'),files={p.name:sha(p) for p in targets},settings=settings,gameplay_verified=False)
    (STAGE/'deployment078.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
