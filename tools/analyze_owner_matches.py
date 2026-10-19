"""Read all surviving game demos; compare recorded scoreboard statistics, not guessed skill."""
import concurrent.futures as cf,hashlib,json,subprocess,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
GAME=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Quake Live')
OUT=ROOT/'out/owner-match-audit-076'
def one(p):
    digest=hashlib.sha256(p.read_bytes()).hexdigest();folder=OUT/digest[:16];folder.mkdir(parents=True,exist_ok=True);dest=folder/(p.stem+'.json')
    try:
        if not dest.exists():
            run=subprocess.run([str(ROOT/'tools/udt/bin/UDT_json.exe'),'-a=gsdm','-t=1','-o='+str(folder.resolve()),str(p)],capture_output=True,timeout=90)
            if run.returncode:raise RuntimeError('UDT exit '+str(run.returncode))
        data=json.loads(dest.read_text(encoding='utf-8-sig'))
        if hashlib.sha256(p.read_bytes()).hexdigest()!=digest:raise RuntimeError('Original changed')
        return {'demo':p.name,'sha256':digest,'matches':data.get('matchStats',[]),'maps':list({g.get('configStringValues',{}).get('mapname','unknown') for g in data.get('gameStates',[])})}
    except Exception as e:return {'demo':p.name,'error':str(e)}
def main():
    OUT.mkdir(parents=True,exist_ok=True);seen={}
    for p in GAME.rglob('*.dm_*'):
        if p.suffix.lower() in {'.dm_91','.dm_90','.dm_73'}:seen.setdefault(hashlib.sha256(p.read_bytes()).hexdigest(),p)
    for p in (ROOT/'демки для обучения/RESTORED_DEMOS_20261019').glob('*.dm_*'):
        seen.setdefault(hashlib.sha256(p.read_bytes()).hexdigest(),p)
    paths=sorted(seen.values())
    with cf.ThreadPoolExecutor(max_workers=4) as ex:records=list(ex.map(one,paths))
    matches=[]
    for r in records:
        for m in r.get('matches',[]):
            names=' '.join([m.get('firstPlaceName',''),m.get('secondPlaceName','')]).lower()
            category='psyz0r' if 'psyz' in names or 'pzyz' in names else 'xaero' if 'xaero' in names else 'other'
            matches.append(dict(demo=r['demo'],category=category,map=m.get('map'),game_type=m.get('gameTypeShort'),duration=m.get('duration'),observed_interval_ms=m.get('endTime',0)-m.get('startTime',0),overtimes=m.get('overtimeCount'),first=m.get('firstPlaceName'),second=m.get('secondPlaceName'),first_score=m.get('firstPlaceScore'),second_score=m.get('secondPlaceScore'),players=m.get('playerStats',[]),forfeited=m.get('forfeited')))
    summary=[]
    for category in ['psyz0r','xaero']:
        selected=[m for m in matches if m['category']==category and m['game_type']=='1v1' and m['map'] in {'bloodrun','ztntourney1','bloodrunintel'}]
        bots=[p for m in selected for p in m['players'] if any(t in p.get('cleanName',p.get('name','')).lower() for t in (['psyz','pzyz'] if category=='psyz0r' else ['xaero']))]
        summary.append(dict(category=category,matches=len(selected),scoreboards_with_bot_stats=len(bots),red=sum(p.get('redArmorPickups',0) for p in bots),mega=sum(p.get('megaHealthPickups',0) for p in bots),yellow=sum(p.get('yellowArmorPickups',0) for p in bots),damage=sum(p.get('damageGiven',0) for p in bots),kills=sum(p.get('kills',0) for p in bots),deaths=sum(p.get('deaths',0) for p in bots)))
    report={'files':len(paths),'parsed':sum('error' not in r for r in records),'errors':[r for r in records if 'error' in r],'matches':matches,'bloodrun_comparison':summary,'longest_recorded_intervals':sorted(matches,key=lambda m:m.get('observed_interval_ms') or 0,reverse=True)[:10],'limits':['Different versions/opponents/settings are not a controlled comparison','Scoreboard availability depends on recorded server data','overtimeCount can be zero for an 18-minute 10-minute-limit match; report observed interval separately','No inference of raw keyboard or mouse input','No demos modified']}
    (ROOT/'docs/training/OWNER_MATCHES_076.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'files':report['files'],'parsed':report['parsed'],'matches':len(matches),'comparison':summary,'max_overtimes':max((m['overtimes'] or 0 for m in matches),default=0)}),flush=True)
if __name__=='__main__':main()
