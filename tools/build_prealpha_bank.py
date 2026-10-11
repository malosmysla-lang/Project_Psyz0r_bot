"""Build a bounded Blood Run route/RJ bank from observed demos; no raw input claims."""
import gzip,json,math,statistics
from pathlib import Path
from associate_demo_aas import AasLocator
ROOT=Path(__file__).resolve().parents[1]
def kind(classname):
 return {'weapon_rocketlauncher':'rocket','weapon_lightning':'lightning','weapon_railgun':'railgun','weapon_shotgun':'shotgun','weapon_plasmagun':'plasma','weapon_grenadelauncher':'grenade','item_armor_body':'red','item_armor_combat':'yellow','item_health_mega':'mega','item_health':'health','item_health_large':'health_large','item_health_small':'health_small'}.get(classname)
def main():
 locator=AasLocator(ROOT/'out/research_stock_ai/bloodrun.aas')
 items=json.loads((ROOT/'out/research_stock_ai/bloodrun_items.json').read_text())
 best={};counts={}
 for corpus in ('bloodrun_corpus','owner_bloodrun_corpus'):
  for file in sorted((ROOT/'out'/corpus).glob('*/observed_approaches.json.gz')):
   with gzip.open(file,'rt') as f:data=json.load(f)
   if data['map']!='bloodrun':continue
   for r in data['routes']:
    pts=r['points'];end=pts[-1]['p'];matches=[e for e in items if kind(e['classname'])==r['kind'] and math.dist(end,e['position'])<112]
    if not matches:continue
    entity=min(matches,key=lambda e:math.dist(end,e['position']))['entity']
    duration=pts[-1]['t']-pts[0]['t'];length=sum(math.dist(a['p'],b['p']) for a,b in zip(pts,pts[1:]))
    if duration<500 or length<160 or length>2000 or sum(p['ground']==1022 for p in pts)/len(pts)<.65:continue
    # Coarse matching for comparison only; all original coordinates are retained.
    key=(entity,*(round(x/96) for x in pts[0]['p']))
    speed=statistics.median(math.hypot(p['v'][0],p['v'][1]) for p in pts)
    chosen=[]
    for p in pts:
     if not chosen or math.dist(p['p'],chosen[-1]['p'])>=64:chosen.append(p)
    if chosen[-1]!=pts[-1]:chosen.append(pts[-1])
    if len(chosen)>24:continue
    target=next(e for e in items if e['entity']==entity)
    candidate=dict(entity=entity,target_position=target['position'],target_class=target['classname'],kind=r['kind'],source_sha256=data['source_sha256'],pickup_ms=r['pickup_ms'],duration_ms=duration,length=length,median_speed=speed,points=[dict(p=p['p'],area=locator.area(p['p']),t=p['t']-pts[0]['t']) for p in chosen],source='demo_observation',live_verified=False)
    counts[key]=counts.get(key,0)+1
    if key not in best or duration<best[key]['duration_ms']:best[key]=candidate
 routes=sorted(best.items(),key=lambda kv:(-counts[kv[0]],kv[1]['duration_ms']))
 selected=[];byentity={}
 for key,r in routes:
  if byentity.get(r['entity'],0)>=12:continue
  r['comparable_observations']=counts[key];selected.append(r);byentity[r['entity']]=byentity.get(r['entity'],0)+1
 rj=json.loads((ROOT/'docs/training/ZTN_solo_01_rocketjumps.json').read_text())
 jumps=[r for r in rj['results'] if r.get('status')=='success']
 out=ROOT/'config/bloodrun_prealpha_bank.json'
 out.write_text(json.dumps(dict(map='bloodrun',aas_sha256=locator.graph['sha256'],routes=selected,rocketjumps=jumps,raw_controls_verified=False),indent=2),encoding='utf-8')
 lines=['/* Generated observed routes; execution remains gated by live context. */','typedef struct { float p[3]; int area; } PsyzRoutePoint;','typedef struct { int entity, count; float speed; float target[3]; const char *classname; PsyzRoutePoint points[24]; } PsyzLearnedRoute;','static const PsyzLearnedRoute psyz_routes[] = {']
 for r in selected:
  points=','.join('{{'+','.join(f'{v:.4f}f' for v in p['p'])+'},'+str(p['area'])+'}' for p in r['points'])
  lines.append('{%d,%d,%.4ff,{%s},"%s",{%s}},'%(r['entity'],len(r['points']),r['median_speed'],','.join(f'{v:.4f}f' for v in r['target_position']),r['target_class'],points))
 lines.append('};\n#define PSYZ_ROUTE_COUNT (sizeof(psyz_routes)/sizeof(psyz_routes[0]))')
 lines.extend(['typedef struct { float start[3],landing[3],pitch,yaw; int health_cost,start_area,shot_delay; } PsyzLearnedJump;','static const PsyzLearnedJump psyz_jumps[] = {'])
 for r in jumps:
  lines.append('{{%s},{%s},%.4ff,%.4ff,%d,%d,%d},'%(','.join(f'{v:.4f}f' for v in r['start_position']),','.join(f'{v:.4f}f' for v in r['landing_position']),r['shot_viewangles'][0],r['shot_viewangles'][1],max(0,r['health_before']-r['health_after']),locator.area(r['start_position']),r['shot_ms']-r['start_ms']))
 lines.append('};\n#define PSYZ_JUMP_COUNT (sizeof(psyz_jumps)/sizeof(psyz_jumps[0]))')
 (ROOT/'adapter/native/psyz_bloodrun_bank.h').write_text('\n'.join(lines)+'\n',encoding='utf-8')
 print('Selected routes',len(selected),'entities',len(byentity),'successful RJ',len(jumps))
if __name__=='__main__':main()
