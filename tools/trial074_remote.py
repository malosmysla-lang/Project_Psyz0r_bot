"""Two short real bot-v-bot trials on isolated 27961; abort for human presence."""
import json,re,socket,time,sys
from pathlib import Path
HOME=Path('/home/qlserver/psyz0r-test-server-home')
LOG=HOME/'console.log'
OUT=Path('/home/qlserver/psyz0r-bot/trials074-20261019-release')
def cmd(text):
    with socket.socket(socket.AF_UNIX) as s:
        s.settimeout(4);s.connect(str(HOME/'console.sock'));s.sendall(text.encode()+b'\n');s.recv(1024)
def read(offset):
    with LOG.open('rb') as f:f.seek(offset);return f.read().decode(errors='replace')
def guard():
    pid=int((HOME/'server.pid').read_text());line=Path(f'/proc/{pid}/cmdline').read_bytes()
    if b'27961' not in line or str(HOME).encode() not in line:raise RuntimeError('Wrong runtime')
    offset=LOG.stat().st_size;cmd('status');time.sleep(.4);status=read(offset)
    if 'map:' not in status:raise RuntimeError('No confirmed console status')
    for line in status.splitlines():
        if re.match(r'^\s*\d+\s+-?\d+\s+\d+\s',line) and ' bot ' not in line:
            raise RuntimeError('Human present; no mutations')
def main():
    guard();OUT.mkdir(exist_ok=True)
    results=[]
    try:
        for trial in range(1):
            guard();offset=LOG.stat().st_size
            cmd('kick Trial_Xaero');cmd('kick Psyz0r_bot');cmd('set timelimit 1');cmd('set fraglimit 0');cmd('set g_warmup 5');cmd('map bloodrun duel');time.sleep(3)
            guard();cmd('addbot Psyz0r 5 free 0 Psyz0r_bot');time.sleep(.5);cmd('addbot Xaero 5 free 0 Trial_Xaero');time.sleep(2)
            status_offset=LOG.stat().st_size;cmd('status');time.sleep(.5)
            status=read(status_offset)
            if 'Trial_Xaero' not in status or 'Psyz0r_bot' not in status:raise RuntimeError('Both participants not confirmed; trial invalid')
            cmd('allready')
            for tick in range(16):time.sleep(5);guard()
            text=read(offset);(OUT/f'trial{trial+1}.log').write_text(text)
            if 'switched more than 50 AI nodes' in text or 'Fatal:' in text:raise RuntimeError('Engine AI error: trial invalid; inspect saved log')
            results.append(dict(trial=trial+1,seconds=80,psyz_pickups=len(re.findall(r'^PSYZ_PICKUP ',text,re.M)),
                major_pickups=len(re.findall(r'^PSYZ_PICKUP .*class=item_(?:armor_body|health_mega)',text,re.M)),
                stalls=len(re.findall(r'^PSYZ_NAV_RECOVERY ',text,re.M)),
                opening_pickups=len(re.findall(r'^PSYZ_OPENING_PICKUP ',text,re.M)),
                stock_xaero_asset='pak00.pk3/botfiles/bots/xaero_c.c',winner='inspect saved score output'))
            (OUT/'summary.json').write_text(json.dumps(results,indent=2));print(results[-1],flush=True)
    finally:
        guard();cmd('set timelimit 10');cmd('kick Trial_Xaero');cmd('set g_warmup 10')
if __name__=='__main__':
    if '--guard-only' in sys.argv:guard();print('NO_HUMANS_CONFIRMED')
    else:main()
