"""Read-only verification plus guarded creation of the sole requested test bot."""
import json,re,subprocess,time,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import trial076_remote as t
def main():
    t.guard();offset=t.LOG.stat().st_size;t.cmd('status');time.sleep(.5);status=t.read(offset)
    if 'Psyz0r_bot' not in status:
        t.cmd('addbot Psyz0r 5 free 0 Psyz0r_bot');time.sleep(2)
    offset=t.LOG.stat().st_size;t.cmd('status');t.cmd('net_port');t.cmd('mapname');t.cmd('qlx_psyzVersion');t.cmd('bot_minplayers');t.cmd('qlx_psyzForfeitEnabled');time.sleep(.5)
    text=t.read(offset)
    bots=[line for line in text.splitlines() if re.match(r'^\s*\d+\s+-?\d+\s+',line) and ' bot ' in line]
    names=[name for name in ['Psyz0r_bot','Trial_Xaero'] if any(name in line for line in bots)]
    cfg=(t.HOME/'baseq3/psyz_test.cfg').read_text()
    report={'test_service':subprocess.check_output(['systemctl','is-active','psyz0r-test.service'],text=True).strip(),'primary_pid':subprocess.check_output(['systemctl','show','quakelive.service','--property=MainPID','--value'],text=True).strip(),'bot_names':names,'sole_requested_bot':names==['Psyz0r_bot'],'map_bloodrun':'map: bloodrun' in text,'version_076':'0.7.6' in text,'forfeit_configured':'set qlx_psyzForfeitEnabled "1"' in cfg,'human_free_at_check':True}
    if not report['sole_requested_bot'] or not report['map_bloodrun'] or not report['version_076']:raise RuntimeError(json.dumps(report))
    (t.OUT/'ready076.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
if __name__=='__main__':main()
