"""Bounded smoke with stock Xaero; stops mutations immediately if a human joins."""
import json,re,subprocess,time
from pathlib import Path
import console_078_remote as console
HOME=console.HOME;OUT=Path(__file__).resolve().parent
GUARD='/home/qlserver/psyz0r-bot/iteration-074/trial074_remote.py'
def guard():subprocess.run(['python3',GUARD,'--guard-only'],check=True,stdout=subprocess.DEVNULL)
def command(s):guard();return console.command(s)
def main():
    guard();primary=subprocess.check_output(['systemctl','show','quakelive.service','--property=MainPID','--value'],text=True)
    offset=(HOME/'console.log').stat().st_size
    status=command('status')
    if 'Psyz0r_bot' not in status:command('addbot Psyz0r 5 free 0 Psyz0r_bot')
    command('addbot Xaero 5 free 0 Trial_Xaero');command('set g_warmup 5');command('allready')
    valid=True
    for i in range(16):
        time.sleep(5)
        try:guard()
        except subprocess.CalledProcessError:valid=False;break
    with (HOME/'console.log').open('rb') as f:f.seek(offset);text=f.read().decode(errors='replace')
    (OUT/'trial078.log').write_text(text)
    pickups=re.findall(r'^PSYZ_PICKUP .*',text,re.M)
    report=dict(version='0.7.8',seconds=(i+1)*5,valid_smoke=valid,full_match=False,winning_strength_proven=False,pickups=len(pickups),red=sum('class=item_armor_body ' in s for s in pickups),mega=sum('class=item_health_mega ' in s for s in pickups),nav_recovery=len(re.findall(r'^PSYZ_NAV_RECOVERY ',text,re.M)),stock_escapes=len(re.findall(r'^PSYZ_STOCK_ESCAPE ',text,re.M)),lg_events=len(re.findall(r'^PSYZ_LG_STYLE ',text,re.M)),fatal=('switched more than 50 AI nodes' in text or 'Fatal:' in text))
    if valid:command('kick Trial_Xaero');command('set g_warmup 10')
    report['status']=console.command('status')
    assert subprocess.check_output(['systemctl','show','quakelive.service','--property=MainPID','--value'],text=True)==primary
    (OUT/'trial078_summary.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
if __name__=='__main__':main()
