"""Atomic native update on empty 27961, rollback and unchanged-primary verification."""
import hashlib,json,re,shutil,subprocess,time
from pathlib import Path
STAGE=Path(__file__).resolve().parent
HOME=Path('/home/qlserver/psyz0r-test-server-home')
RUNTIME=Path('/home/qlserver/psyz0r-test-server/psyz_test/minqlx_nopy.so')
NATIVE=Path('/home/qlserver/psyz0r-bot/build-080-20261020/bin/minqlx.x64.so')
GUARD='/home/qlserver/psyz0r-bot/iteration-074/trial074_remote.py'
def run(*args):return subprocess.check_output(args,text=True).strip()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def guard():run('python3',GUARD,'--guard-only')
def main():
    guard();primary=run('systemctl','show','quakelive.service','--property=MainPID','--value')
    cfg=HOME/'baseq3/psyz_test.cfg';profile=HOME/'baseq3/zzz_psyz_profile.pk3';chat=HOME/'minqlx-plugins/psyz_chat.py'
    unchanged={str(p):sha(p) for p in [profile,chat]}
    backup=Path('/home/qlserver/backups')/time.strftime('psyz-080-%Y%m%dT%H%M%SZ',time.gmtime());backup.mkdir()
    for p in [RUNTIME,cfg]:shutil.copy2(p,backup/p.name)
    text=re.sub(r'^\s*set[as]?\s+qlx_psyzVersion\s+.*\n?','',cfg.read_text(),flags=re.M)
    text+='\n// 0.8.0: confirmed-hit finishing bridge and nearby weapon recovery.\nset qlx_psyzVersion "0.8.0"\n'
    for key in ['qlx_psyzComboLive','sv_hostname']:
        text=re.sub(r'^\s*set[as]?\s+'+key+r'\s+.*\n?','',text,flags=re.M)
    text+='set qlx_psyzComboLive "1"\nset sv_hostname "^4ProQ^7room Server ^4Bot"\n'
    guard();run('sudo','systemctl','stop','psyz0r-test.service')
    try:
        temp=RUNTIME.with_suffix('.080-new');shutil.copy2(NATIVE,temp);temp.replace(RUNTIME);cfg.write_text(text)
        sock=HOME/'console.sock'
        if sock.exists():sock.unlink()
        run('sudo','systemctl','start','psyz0r-test.service');time.sleep(6)
        assert run('systemctl','is-active','psyz0r-test.service')=='active'
        assert sha(RUNTIME)==sha(NATIVE)
        assert all(sha(Path(p))==digest for p,digest in unchanged.items())
        assert run('systemctl','show','quakelive.service','--property=MainPID','--value')==primary
    except Exception:
        run('sudo','systemctl','stop','psyz0r-test.service')
        for p in [RUNTIME,cfg]:shutil.copy2(backup/p.name,p)
        run('sudo','systemctl','start','psyz0r-test.service');raise
    result=dict(version='0.8.0',backup=str(backup),primary_pid=primary,test_pid=run('systemctl','show','psyz0r-test.service','--property=MainPID','--value'),
        files={p.name:sha(p) for p in [RUNTIME,cfg,profile,chat]},unchanged_profile_and_chat=True,gameplay_verified=False)
    (STAGE/'deployment080.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
if __name__=='__main__':main()
