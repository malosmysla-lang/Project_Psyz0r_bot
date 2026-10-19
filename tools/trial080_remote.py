"""Bounded natural-combat smoke. Immediately remove only our diagnostic bot on human join."""
import sys,time,re,json,subprocess
from pathlib import Path
sys.path.insert(0,'/home/qlserver/psyz0r-bot/iteration-079-20261019')
import console_078_remote as c
STAGE=Path(__file__).resolve().parent;NAME='Trial080_Xaero'
def status():return c.command('status').split('PSYZ_')[0]
def humans(s):
    return any(re.match(r'^\s*\d+\s+-?\d+\s+\d+\s+',line) and ' bot ' not in line for line in s.splitlines())
def main():
    subprocess.run(['python3','/home/qlserver/psyz0r-bot/iteration-074/trial074_remote.py','--guard-only'],check=True,stdout=subprocess.DEVNULL)
    before=(c.HOME/'console.log').stat().st_size
    c.command(f'addbot Xaero 5 free 0 {NAME}');c.command('allready');interrupted=False
    for _ in range(45):
        time.sleep(2)
        s=status()
        if humans(s):interrupted=True;break
    s=status()
    if NAME in s and any(NAME in line and ' bot ' in line for line in s.splitlines()):c.command('kick '+NAME)
    with (c.HOME/'console.log').open('rb') as f:f.seek(before);log=f.read().decode(errors='replace')
    (STAGE/'trial080.log').write_text(log)
    switches=[line for line in log.splitlines() if line.startswith('PSYZ_COMBO_SWITCH ')]
    result=dict(version='0.8.0',seconds=90,interrupted_for_human=interrupted,combo_switches=switches,brakes=sum(line.startswith('PSYZ_COMBAT_BRAKE ')for line in log.splitlines()),fatal='Fatal:' in log or 'switched more than 50 AI nodes' in log,status=status(),full_match=False)
    (STAGE/'trial080.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='status'}))
if __name__=='__main__':main()
