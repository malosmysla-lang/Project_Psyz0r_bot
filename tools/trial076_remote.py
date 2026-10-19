"""Bounded 65s comparison smoke. Every mutation is guarded against human presence."""
import json,re,socket,time,subprocess
from pathlib import Path
HOME=Path('/home/qlserver/psyz0r-test-server-home');LOG=HOME/'console.log'
OUT=Path('/home/qlserver/psyz0r-bot/iteration-076-20261019')
GUARD='/home/qlserver/psyz0r-bot/iteration-074/trial074_remote.py'
def guard():subprocess.run(['python3',GUARD,'--guard-only'],check=True,stdout=subprocess.DEVNULL)
def cmd(text):
    guard()
    with socket.socket(socket.AF_UNIX) as s:s.settimeout(4);s.connect(str(HOME/'console.sock'));s.sendall((text+'\n').encode());s.recv(4096)
def read(offset):
    with LOG.open('rb') as f:f.seek(offset);return f.read().decode(errors='replace')
def main():
    guard();primary=subprocess.check_output(['systemctl','show','quakelive.service','--property=MainPID','--value'],text=True).strip()
    offset=LOG.stat().st_size
    cmd('set g_warmup 5');cmd('set timelimit 10');cmd('set fraglimit 0')
    cmd('addbot Psyz0r 5 free 0 Psyz0r_bot');cmd('addbot Xaero 5 free 0 Trial_Xaero')
    time.sleep(2);cmd('allready')
    for tick in range(13):
        time.sleep(5);guard()
        text=read(offset)
        if 'switched more than 50 AI nodes' in text or 'Fatal:' in text:
            (OUT/'trial076.log').write_text(text);raise RuntimeError('Engine error; this smoke is invalid')
        if tick%4==0:print('SMOKE_SECONDS',5*(tick+1),flush=True)
    cmd('status');text=read(offset);(OUT/'trial076.log').write_text(text)
    pickups=re.findall(r'^PSYZ_PICKUP .*',text,re.M)
    report={'seconds':65,'valid_smoke':True,'full_match':False,'pickups':len(pickups),'red_pickups':sum('class=item_armor_body ' in x for x in pickups),'mega_pickups':sum('class=item_health_mega ' in x for x in pickups),'nav_recoveries':len(re.findall(r'^PSYZ_NAV_RECOVERY ',text,re.M)),'lg_style_events':len(re.findall(r'^PSYZ_LG_STYLE ',text,re.M)),'opening_pickups':len(re.findall(r'^PSYZ_OPENING_PICKUP ',text,re.M)),'winner':None}
    assert subprocess.check_output(['systemctl','show','quakelive.service','--property=MainPID','--value'],text=True).strip()==primary
    (OUT/'trial076_summary.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
    # Leave only the user's bot for a human test, with the normal Duel limit.
    cmd('kick Trial_Xaero');cmd('set g_warmup 10');cmd('set nextmap "map bloodrun duel"')
if __name__=='__main__':main()
