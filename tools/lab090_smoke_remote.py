"""Bounded private smoke check; restore stock empty standby in finally."""
from pathlib import Path
import subprocess,socket,time,re,json,os
home=Path('/home/qlserver/psyz0r-lab-home');stage=Path(__file__).resolve().parent
cfg=home/'baseq3/psyz_test.cfg';override='/etc/systemd/system/psyz0r-lab.service.d/zzz-rc2-smoke.conf'
def run(*args):return subprocess.check_output(args,text=True).strip()
def command(text):
 log=home/'console.log';offset=log.stat().st_size
 with socket.socket(socket.AF_UNIX) as s:
  s.settimeout(2);s.connect(str(home/'console.sock'));s.sendall(text.encode()+b'\n');s.recv(256)
 time.sleep(.4)
 with log.open('rb') as f:f.seek(offset);return f.read(65536).decode(errors='replace')
def ready():
 for _ in range(24):
  time.sleep(2)
  try:
   status=command('status')
   if 'map:' in status and 'steamid' in status:return status
  except (OSError,RuntimeError):pass
 raise RuntimeError('Lab console did not become ready')
status=command('status');assert 'map:' in status and 'steamid' in status
assert not any(len(p:=line.split())>=7 and p[0].isdigit() and p[1].lstrip('-').isdigit() for line in status.splitlines()),'Lab must be empty'
saved=cfg.read_bytes();backup=home/'psyz_test.cfg.before-rc2-smoke';assert not backup.exists();backup.write_bytes(saved);backup.chmod(0o600)
runner=home/'runner-rc2-smoke.py'
s=(home/'runner-standby.py').read_text().replace("environment.pop('LD_PRELOAD', None)","environment['LD_PRELOAD'] = '/home/qlserver/psyz0r-bot/build-090-rc2-20261025/bin/minqlx.x64.so' #")
runner.write_text(s)
text=saved.decode();values={'bot_enable':'1','bot_minplayers':'0','qlx_psyzTestInstance':'1','qlx_psyzFinish087':'1','qlx_psyzControlMode':'0','qlx_psyzPreAlpha':'0','qlx_plugins':'','timelimit':'1','fraglimit':'0','g_doWarmup':'0'}
for key,value in values.items():
 text=re.sub(r'^\s*set[as]?\s+'+re.escape(key)+r'\s+.*$', '', text,flags=re.M)
 text+='\nset '+key+' "'+value+'"\n'
drop='[Service]\nExecStart=\nExecStart=/usr/bin/python3 '+str(runner)+' --base /home/qlserver/psyz0r-lab-server --home '+str(home)+' --listen 0.0.0.0 --stock-goal-observer\nRestart=no\nRuntimeMaxSec=240\n'
offset=(home/'console.log').stat().st_size
try:
 run('sudo','-n','systemctl','stop','psyz0r-lab');cfg.write_text(text)
 subprocess.run(['sudo','-n','tee',override],input=drop,text=True,stdout=subprocess.DEVNULL,check=True)
 run('sudo','-n','systemctl','daemon-reload');run('sudo','-n','systemctl','start','psyz0r-lab');ready()
 for order in [('Psyz0r','Xaero'),('Xaero','Psyz0r')]:
  command('map bloodrun duel');time.sleep(3)
  for bot in order:command('addbot '+bot+' 5')
  command('allready');time.sleep(65)
  command('kick allbots')
 with (home/'console.log').open('rb') as f:f.seek(offset);evidence=f.read().decode(errors='replace')
 (stage/'lab-smoke.log').write_text(evidence)
 report={'candidate':'0.9.0-rc2','diagnosticRuns':2,'acceptedMatches':0,'installed':'PSYZ_CONTROL install=0' in evidence,'switches':len(re.findall('PSYZ_FINISH087 slot=',evidence)),'shotgunSwitches':len(re.findall(r'PSYZ_FINISH087[^\n]*to=3 ',evidence)),'lightningSwitches':len(re.findall(r'PSYZ_FINISH087[^\n]*to=6 ',evidence))}
 (stage/'lab-smoke.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
finally:
 run('sudo','-n','systemctl','stop','psyz0r-lab');cfg.write_bytes(saved)
 subprocess.run(['sudo','-n','rm','--',override],check=False)
 run('sudo','-n','systemctl','daemon-reload');run('sudo','-n','systemctl','start','psyz0r-lab')
 status=ready();assert not any(len(p:=line.split())>=7 and p[0].isdigit() and p[1].lstrip('-').isdigit() for line in status.splitlines()),'Restored lab is not empty'
 print('LAB_RESTORED_EMPTY_STOCK_STANDBY',flush=True)
