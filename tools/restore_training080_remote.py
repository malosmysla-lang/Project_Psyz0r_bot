"""Restore public practice settings from primary, isolated paths and bot presence."""
from pathlib import Path
import re,shutil,time,subprocess,json,sys
sys.path.insert(0,'/home/qlserver/psyz0r-bot/iteration-079-20261019')
import console_078_remote as console
ROOT=Path(__file__).resolve().parent;HOME=Path('/home/qlserver/psyz0r-test-server-home')
cfg=HOME/'baseq3/psyz_test.cfg';primary=Path('/home/qlserver/server/baseq3/server.cfg')
allowed={'g_gametype','timelimit','fraglimit','g_warmup','g_infiniteAmmo','g_startingWeapons','g_forcerespawn','g_weaponrespawn','g_quadfactor','sv_fps','sv_maxclients','g_allowVote','g_allowVoteMidGame'}
def main():
    subprocess.run(['python3','/home/qlserver/psyz0r-bot/iteration-074/trial074_remote.py','--guard-only'],check=True,stdout=subprocess.DEVNULL)
    primary_pid=subprocess.check_output(['systemctl','show','quakelive.service','--property=MainPID','--value'],text=True).strip()
    backup=Path('/home/qlserver/backups')/time.strftime('psyz-training080-%Y%m%dT%H%M%SZ',time.gmtime());backup.mkdir()
    shutil.copy2(cfg,backup/cfg.name)
    text=cfg.read_text();copied={}
    for line in primary.read_text().splitlines():
        m=re.match(r'\s*(?:set[as]?\s+)?(\w+)\s+("[^"]*"|\S+)',line)
        if m and m[1] in allowed:copied[m[1]]=m[2]
    overrides=dict(copied,sv_hostname='"^4ProQ^7room Server ^4Bot"',sv_tags='"pracc,duel,training,psyz0r,ztn"',bot_minplayers='"0"',bot_nochat='"1"',developer='"0"',qlx_plugins='"psyz_chat,psyz_presence"')
    for key in overrides:text=re.sub(r'^\s*set[as]?\s+'+re.escape(key)+r'\s+.*\n?','',text,flags=re.M)
    text+='\n// Public training settings; networking, credentials and primary plugins are not copied.\n'+''.join(f'set {k} {v}\n' for k,v in overrides.items())
    plugin=HOME/'minqlx-plugins/psyz_presence.py';shutil.copy2(ROOT/'psyz_presence.py',plugin)
    cfg.write_text(text)
    subprocess.run(['sudo','systemctl','stop','psyz0r-test.service'],check=True)
    socket=HOME/'console.sock'
    if socket.exists():socket.unlink()
    subprocess.run(['sudo','systemctl','start','psyz0r-test.service'],check=True)
    time.sleep(7)
    current=subprocess.check_output(['systemctl','show','quakelive.service','--property=MainPID','--value'],text=True).strip()
    assert current==primary_pid
    result={'backup':str(backup),'primary_pid_unchanged':True,'public_settings_copied':copied,'status':console.command('status').split('PSYZ_')[0],'hostname':overrides['sv_hostname']}
    (ROOT/'training_restore.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
if __name__=='__main__':main()
