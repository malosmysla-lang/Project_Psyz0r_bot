"""Leave one practice bot ready, with a short read-only observation window."""
import hashlib,json,subprocess,time
from pathlib import Path
import console_078_remote as console
HOME=console.HOME;STAGE=Path(__file__).resolve().parent
GUARD='/home/qlserver/psyz0r-bot/iteration-074/trial074_remote.py'
def guard():subprocess.run(['python3',GUARD,'--guard-only'],check=True,stdout=subprocess.DEVNULL)
def main():
    guard();primary=subprocess.check_output(['systemctl','show','quakelive.service','--property=MainPID','--value'],text=True).strip()
    offset=(HOME/'console.log').stat().st_size
    status=console.command('status')
    if 'Psyz0r_bot' not in status:guard();console.command('addbot Psyz0r 5 free 0 Psyz0r_bot')
    interrupted=False
    for _ in range(6):
        time.sleep(5)
        try:guard()
        except subprocess.CalledProcessError:interrupted=True;break
    with (HOME/'console.log').open('rb') as f:f.seek(offset);text=f.read().decode(errors='replace')
    (STAGE/'verify079.log').write_text(text)
    result=dict(version='0.7.9',seconds=30,interrupted_for_human=interrupted,status=console.command('status'),version_response=console.command('qlx_psyzVersion'),
        pickups=sum(s.startswith('PSYZ_PICKUP ') and 'class=' in s for s in text.splitlines()),
        pmtype_diagnostics='pmtype=0' in text,fatal='Fatal:' in text or 'switched more than 50 AI nodes' in text,
        primary_pid_unchanged=subprocess.check_output(['systemctl','show','quakelive.service','--property=MainPID','--value'],text=True).strip()==primary)
    (STAGE/'verify079.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
if __name__=='__main__':main()
