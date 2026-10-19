"""Build a separate checkout, then replace only isolated 27961 with verified rollback."""
import hashlib,json,os,shutil,subprocess,sys,time
from pathlib import Path
STAGE=Path(__file__).resolve().parent
BUILD=Path('/home/qlserver/psyz0r-bot/build-076-20261019')
HOME=Path('/home/qlserver/psyz0r-test-server-home')
RUNTIME=Path('/home/qlserver/psyz0r-test-server/psyz_test/minqlx_nopy.so')
GUARD='/home/qlserver/psyz0r-bot/iteration-074/trial074_remote.py'
def run(*args,**kw):return subprocess.check_output(args,text=True,**kw).strip()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    run('python3',GUARD,'--guard-only')
    primary=run('systemctl','show','quakelive.service','--property=MainPID','--value')
    if not BUILD.exists():shutil.copytree('/home/qlserver/psyz0r-bot/build-074-20261019',BUILD)
    for p in (STAGE/'adapter/native').glob('*.h'):shutil.copy2(p,BUILD/p.name)
    # Headers are not tracked by the legacy Makefile: force hooks.c recompilation.
    (BUILD/'hooks.c').touch()
    env=os.environ.copy();env['PATH']='/home/qlserver/psyz0r-bot/toolchain-bin:/usr/bin:/bin'
    with (STAGE/'build.log').open('w') as log:subprocess.run(['make','all'],cwd=BUILD,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    tests=[]
    for name in ['prealpha_native_tests','nav_recovery_tests','lg_style_tests']:
        binary=STAGE/name
        subprocess.run(['g++','-std=c++17',str(STAGE/'tests'/(name+'.cpp')),'-o',str(binary),'-lm'],check=True)
        tests.append({'name':name,'output':run(str(binary))})
    plugin=HOME/'minqlx-plugins/psyz_chat.py';cfg=HOME/'baseq3/psyz_test.cfg'
    new=BUILD/'bin/minqlx.x64.so'
    # Backups cover every live file this operation will change.
    backup=Path('/home/qlserver/backups')/time.strftime('psyz-076-%Y%m%dT%H%M%SZ',time.gmtime());backup.mkdir()
    for p in [RUNTIME,plugin,cfg]:shutil.copy2(p,backup/p.name)
    text=cfg.read_text()
    import re
    text=re.sub(r'^\s*set[as]?\s+qlx_psyzVersion\s+.*\n?','',text,flags=re.M)
    text+='\n// 0.7.6: close-item stall recovery; clock-gated second red; bounded chat.\nset qlx_psyzVersion "0.7.6"\n'
    text=re.sub(r'^\s*set[as]?\s+qlx_psyzForfeitEnabled\s+.*\n?','',text,flags=re.M)
    text+='// One 15% choice per match. Runtime also requires bot_minplayers 0.\nset qlx_psyzForfeitEnabled "1"\n'
    run('python3',GUARD,'--guard-only')
    run('sudo','systemctl','stop','psyz0r-test.service')
    try:
        tmp=RUNTIME.with_suffix('.new');shutil.copy2(new,tmp);tmp.replace(RUNTIME)
        shutil.copy2(STAGE/'psyz_chat.py',plugin);cfg.write_text(text)
        sock=HOME/'console.sock'
        if sock.exists():sock.unlink()
        run('sudo','systemctl','start','psyz0r-test.service')
        time.sleep(3)
        if run('systemctl','is-active','psyz0r-test.service')!='active':raise RuntimeError('Test service inactive')
    except Exception:
        for p in [RUNTIME,plugin,cfg]:shutil.copy2(backup/p.name,p)
        run('sudo','systemctl','start','psyz0r-test.service');raise
    assert run('systemctl','show','quakelive.service','--property=MainPID','--value')==primary
    assert sha(RUNTIME)==sha(new)
    report={'version':'0.7.6','binary_sha256':sha(RUNTIME),'plugin_sha256':sha(plugin),'backup':str(backup),'primary_pid':primary,'test_pid':run('systemctl','show','psyz0r-test.service','--property=MainPID','--value'),'service':'active','linux_tests':tests,'gameplay_verified':False}
    (STAGE/'deployment.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
