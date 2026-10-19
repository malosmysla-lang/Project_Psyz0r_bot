"""Publish website only; leave both game processes untouched."""
import hashlib,subprocess,tarfile,os,shutil,json
from pathlib import Path
def run(*args):return subprocess.check_output(args,text=True).strip()
base=Path('/home/qlserver/websites/pracc-analytics')
archive=base/'site080.tar.gz'
assert hashlib.sha256(archive.read_bytes()).hexdigest()=='a0c334fd12d43af8b5f15569c73c60649f4ebf9c581f97d66a23069bc8dc6c06'
before={s:run('systemctl','show',s,'-p','MainPID','--value') for s in ['quakelive.service','psyz0r-test.service']}
target=base/'releases/20261020-080-charts';target.mkdir()
with tarfile.open(archive) as z:z.extractall(target,filter='data')
previous=str((base/'current').resolve())
os.symlink(target,base/'current-next');os.replace(base/'current-next',base/'current')
subprocess.run(['sudo','-n','systemctl','restart','pracc-analytics.service'],check=True)
assert run('systemctl','is-active','pracc-analytics.service')=='active'
assert all(run('systemctl','show',s,'-p','MainPID','--value')==pid for s,pid in before.items())
shutil.copy2(archive,Path('/home/qlserver/backups/pracc-analytics-20261020/site-latest.tar.gz'))
print(json.dumps(dict(release=str(target),previous=previous,game_pids=before)))
