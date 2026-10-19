"""Record solo warmup after the smoke; never present it as duel validation."""
import collections,json,re
from pathlib import Path
STAGE=Path(__file__).resolve().parent
LOG=Path('/home/qlserver/psyz0r-test-server-home/console.log')
def main():
    lines=LOG.read_text(errors='replace').splitlines()
    cut=max(i for i,s in enumerate(lines) if s.strip()=='kick Trial_Xaero')
    lines=lines[cut+1:]
    snapshots=[];pickups=[];latest_clock={};clock_deltas=[]
    for line in lines:
        if line.startswith('PSYZ_NAV '):snapshots.append(int(re.search(r't=(\d+)',line)[1]))
        if line.startswith('PSYZ_ITEM_TIMER '):
            values=dict(re.findall(r'(\w+)=([^ ]+)',line))
            if values['available']=='0':latest_clock[int(values['entity'])]=int(values['due'])
        if line.startswith('PSYZ_PICKUP '):
            values=dict(re.findall(r'(\w+)=([^ ]+)',line))
            if 'class' not in values or 't' not in values:continue
            pickups.append(values)
            if values['class'] in {'item_health_mega','item_armor_body'}:
                due=latest_clock.get(int(values['entity']))
                if due is not None and int(values['t'])>=due:clock_deltas.append(dict(time_ms=int(values['t']),entity=int(values['entity']),kind=values['class'],due_ms=due,delay_ms=int(values['t'])-due))
    result=dict(mode='solo_warmup_after_xaero_smoke',full_duel=False,seconds=round((max(snapshots)-min(snapshots))/1000,2),pickups=dict(collections.Counter(v['class'] for v in pickups)),major_clock_pickups=clock_deltas,stock_escapes=sum(s.startswith('PSYZ_STOCK_ESCAPE ')for s in lines),new_client_connections=sum('connecting with' in s for s in lines),limits=['Only a single bot in warmup at the latest status, not duel opposition','Repeated clock delays may include approaching a late already-available item','A quick pickup in warmup does not validate early arrival under pressure'])
    (STAGE/'unopposed078.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
if __name__=='__main__':main()
