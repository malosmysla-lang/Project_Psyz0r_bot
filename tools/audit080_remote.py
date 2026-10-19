"""Print only explicitly public gameplay settings; never dump server configs."""
from pathlib import Path
import re,json,zipfile,subprocess,sys
sys.path.insert(0,'/home/qlserver/psyz0r-bot/iteration-079-20261019')
import console_078_remote as console
allowed={'sv_hostname','sv_tags','g_gametype','g_factory','timelimit','fraglimit','g_warmup','bot_minplayers','bot_enable','bot_nochat','developer','sv_pure','g_weaponrespawn','qlx_plugins','qlx_psyzVersion','g_startingWeapons','g_infiniteAmmo','g_spawnArmor','g_spawnHealth','g_forcerespawn'}
for name,path in [('primary',Path('/home/qlserver/server/baseq3/server.cfg')),('test',Path('/home/qlserver/psyz0r-test-server-home/baseq3/psyz_test.cfg'))]:
    rows={}
    for line in path.read_text().splitlines():
        m=re.match(r'\s*(?:set[as]?\s+)?(\w+)\s+(.+)',line)
        if m and m[1] in allowed:rows[m[1]]=m[2]
    print(name,json.dumps(rows))
print(console.command('status').split('PSYZ_')[0])
p=Path('/home/qlserver/psyz0r-test-server-home/baseq3/zzz_psyz_profile.pk3')
with zipfile.ZipFile(p) as z:
    for n in z.namelist():
        if n.endswith('.bot'):print('bot_profile',z.read(n).decode())
