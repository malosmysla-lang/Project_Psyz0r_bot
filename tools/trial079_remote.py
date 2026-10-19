"""Five-minute diagnostic match; verify both bots, abort changes if a human joins."""
import json,re,subprocess,time
from pathlib import Path
import console_078_remote as console
STAGE=Path(__file__).resolve().parent;HOME=console.HOME
GUARD='/home/qlserver/psyz0r-bot/iteration-074/trial074_remote.py'
def guard():subprocess.run(['python3',GUARD,'--guard-only'],check=True,stdout=subprocess.DEVNULL)
def command(text):guard();return console.command(text)
def main():
    guard();primary=subprocess.check_output(['systemctl','show','quakelive.service','--property=MainPID','--value'],text=True).strip()
    offset=(HOME/'console.log').stat().st_size
    command('set timelimit 5');command('set fraglimit 0');command('set g_warmup 5')
    status=command('status')
    if 'Psyz0r_bot' not in status:command('addbot Psyz0r 5 free 0 Psyz0r_bot')
    if 'Trial_Xaero' not in status:command('addbot Xaero 5 free 0 Trial_Xaero')
    time.sleep(2);status=command('status')
    if not all(name in status for name in ['Psyz0r_bot','Trial_Xaero']):raise RuntimeError('Both bots not confirmed: '+status)
    (STAGE/'participants079.txt').write_text(status)
    command('allready');print('BOTH_BOTS_CONFIRMED_MATCH_START',flush=True)
    started=time.monotonic();scores=[];interrupted=False
    for tick in range(65):
        time.sleep(5)
        try:guard()
        except subprocess.CalledProcessError:interrupted=True;break
        if tick%6==0:
            scores.append(dict(elapsed=round(time.monotonic()-started,1),status=command('status'),phase=command('g_gameState')))
            (STAGE/'trial079_progress.json').write_text(json.dumps(scores,indent=2))
            print('TRIAL_TICK',tick+1,flush=True)
        if scores and 'POST_GAME' in scores[-1]['phase']:break
    with (HOME/'console.log').open('rb') as f:f.seek(offset);text=f.read().decode(errors='replace')
    (STAGE/'trial079.log').write_text(text)
    result=dict(version='0.7.9',requested_minutes=5,elapsed_seconds=round(time.monotonic()-started,1),interrupted_for_human=interrupted,
        participants_verified=True,ten_minute_strength_proven=False,scores=scores,
        pickups=len(re.findall(r'^PSYZ_PICKUP .*class=',text,re.M)),red=len(re.findall(r'^PSYZ_PICKUP .*class=item_armor_body ',text,re.M)),
        mega=len(re.findall(r'^PSYZ_PICKUP .*class=item_health_mega ',text,re.M)),
        stock_escapes=len(re.findall(r'^PSYZ_STOCK_ESCAPE ',text,re.M)),fatal='Fatal:' in text or 'switched more than 50 AI nodes' in text)
    if not interrupted:
        command('kick Trial_Xaero');command('set timelimit 10');command('set g_warmup 10')
        result['ready_status']=command('status')
    assert subprocess.check_output(['systemctl','show','quakelive.service','--property=MainPID','--value'],text=True).strip()==primary
    (STAGE/'trial079_summary.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k not in ['scores','ready_status']}),flush=True)
if __name__=='__main__':main()
