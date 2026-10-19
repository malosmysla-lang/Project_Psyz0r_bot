"""Deploy LG-only native update to empty isolated 27961; preserve 27960."""
import hashlib,json,subprocess,sys,time
from pathlib import Path
BASE=Path('/home/qlserver/psyz0r-test-server')
HOME=Path('/home/qlserver/psyz0r-test-server-home')
BUILD=Path('/home/qlserver/psyz0r-bot/build-074-20261019')
def run(*args):return subprocess.check_output(args,text=True).strip()
def main():
    guard='/home/qlserver/psyz0r-bot/iteration-074/trial074_remote.py'
    run('python3',guard,'--guard-only')
    primary=run('systemctl','show','quakelive.service','--property=MainPID','--value')
    backup=Path('/home/qlserver/backups')/time.strftime('psyz-lg075-%Y%m%dT%H%M%SZ',time.gmtime())
    backup.mkdir()
    cfg=HOME/'baseq3/psyz_test.cfg';runtime=BASE/'psyz_test/minqlx_nopy.so'
    (backup/cfg.name).write_bytes(cfg.read_bytes());(backup/runtime.name).write_bytes(runtime.read_bytes())
    data=(BUILD/'bin/minqlx.x64.so').read_bytes()
    settings={'qlx_psyzLGSmoothTracking':'1','qlx_psyzLGTurnRate':'240','qlx_psyzLGFootwork':'1','qlx_psyzNativeSocial':'0','qlx_psyzExperimentalJumps':'1'}
    text=cfg.read_text()
    import re
    for k,v in settings.items():
        text=re.sub(r'^\s*set[as]?\s+'+k+r'\s+.*\n?','',text,flags=re.M)
    text+='\n// LG 0.7.5: smooth tracking; social sensors remain disabled.\n'+''.join(f'set {k} "{v}"\n' for k,v in settings.items())
    # Recheck immediately before stopping; no shell fragments or main-service mutation.
    run('python3',guard,'--guard-only')
    run('sudo','systemctl','stop','psyz0r-test.service')
    try:
        cfg.write_text(text)
        tmp=runtime.with_suffix('.new');tmp.write_bytes(data);tmp.replace(runtime)
        sock=HOME/'console.sock'
        if sock.exists():sock.unlink()
        run('sudo','systemctl','start','psyz0r-test.service')
    except Exception:
        cfg.write_bytes((backup/cfg.name).read_bytes());runtime.write_bytes((backup/runtime.name).read_bytes())
        run('sudo','systemctl','start','psyz0r-test.service');raise
    assert run('systemctl','show','quakelive.service','--property=MainPID','--value')==primary
    report={'release':'0.7.5-lg','sha256':hashlib.sha256(data).hexdigest(),'backup':str(backup),'main_pid':primary,'settings':settings,'test_service':run('systemctl','is-active','psyz0r-test.service')}
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
