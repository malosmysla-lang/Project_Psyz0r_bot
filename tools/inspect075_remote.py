from pathlib import Path
import json,re,subprocess,sys
sys.path.insert(0,'/home/qlserver/psyz0r-bot/iteration-074')
import trial075_remote as t
p=Path('/home/qlserver/psyz0r-test-server-home/console.log')
with p.open('rb') as f:
 f.seek(max(0,p.stat().st_size-4_000_000));s=f.read().decode(errors='replace')
print('\n'.join(l for l in s.splitlines() if any(x in l for x in ['Fatal','switched more','PSYZ_LG_STYLE','Error:'])))
t.guard();t.cmd('set timelimit 10');t.cmd('set g_warmup 10');t.cmd('status')
Path('/home/qlserver/psyz0r-bot/trials075-lg-20261019-long/console-tail.log').write_text(s)
print('GUARDED_TEST_READY')
