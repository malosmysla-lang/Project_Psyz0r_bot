"""Export actual scoreboard observations; missing accuracy is never zero-filled."""
import concurrent.futures as cf
import json,subprocess
from collections import defaultdict
from pathlib import Path
import collect_ztn_top_players as corpus
ROOT=Path(__file__).resolve().parents[1]
WEAPONS=('lightningGun','railgun','rocketLauncher','plasmaGun')
def worker(record):
    out=ROOT/'out/top500_stats'/str(record['archive_id']);out.mkdir(parents=True,exist_ok=True)
    demo=corpus.OUT/record['filename'];file=out/(demo.stem+'.json')
    if not file.exists():
        result=subprocess.run([str(ROOT/'tools/udt/bin/UDT_json.exe'),'-a=s','-t=1','-o='+str(out),str(demo)],capture_output=True,timeout=90)
        if result.returncode:return dict(archive_id=record['archive_id'],error='UDT stats export failed')
    try:data=json.loads(file.read_text(encoding='utf-8-sig'))
    except (OSError,ValueError) as error:return dict(archive_id=record['archive_id'],error=str(error))
    observations=[]
    for match in data.get('matchStats',[]):
        for player in match.get('playerStats',[]):
            names=corpus.names(dict(players=[dict(nick=player.get('cleanName',player.get('name','')))]))
            for name in names:
                for weapon in WEAPONS:
                    shots=player.get(weapon+'Shots');hits=player.get(weapon+'Hits')
                    if shots is None or hits is None or shots<=0:continue
                    observations.append(dict(player=name,weapon=weapon,shots=shots,hits=hits,damage=player.get(weapon+'Damage'),archive_id=record['archive_id']))
    return dict(archive_id=record['archive_id'],observations=observations)
def main():
    manifest=json.loads((corpus.OUT/'manifest.json').read_text(encoding='utf-8'))['records']
    with cf.ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(worker,manifest))
    groups=defaultdict(list)
    for result in results:
        for row in result.get('observations',[]):groups[(row['player'],row['weapon'])].append(row)
    summaries=[]
    for (player,weapon),rows in sorted(groups.items()):
        shots=sum(r['shots'] for r in rows);hits=sum(r['hits'] for r in rows)
        summaries.append(dict(player=player,weapon=weapon,observations=len(rows),demos=len({r['archive_id'] for r in rows}),shots=shots,hits=hits,pooled_accuracy=round(100*hits/shots,2)))
    report=dict(demos=len(manifest),summaries=summaries,errors=[r for r in results if 'error' in r],note='Only observed scoreboard values; missing entries are not zeros. Includes direct/splash semantics of UDT; player aliases are not verified identities.',observations=[r for result in results for r in result.get('observations',[])])
    (ROOT/'docs/training/TOP500_WEAPON_OBSERVATIONS_074.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(dict(demos=report['demos'],errors=len(report['errors']),summaries=summaries)),flush=True)
if __name__=='__main__':main()
