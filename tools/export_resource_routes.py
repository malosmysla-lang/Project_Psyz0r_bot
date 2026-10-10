"""Export observed approaches, never mark their geometry or physics as verified."""
import argparse
import json
from pathlib import Path

def export_routes(rows,audit):
    if any(b["time_ms"]<=a["time_ms"] for a,b in zip(rows,rows[1:])): return []
    routes=[]
    for attempt in audit['results']:
        if attempt['status']!='success': continue
        for pickup in attempt.get('pickups',[]):
            if pickup['kind']=='shard': continue
            t=pickup['time_ms']
            samples=[x for x in rows if attempt['start_ms']<=x['time_ms']<=t]
            if not samples: continue
            first=samples[0]
            if any((x['segment'],x['client'],x['game_state_number'])!=(first['segment'],first['client'],first['game_state_number']) or x['pm_type']!=0 for x in samples): continue
            if any(b['time_ms']-a['time_ms']>100 for a,b in zip(samples,samples[1:])): continue
            event=next((e for x in samples[-5:] for e in x['events'] if e['udt_event_id'] in (2,3) and x['time_ms']==t),None)
            if event is None: continue
            routes.append(dict(id=f"ztn-{attempt['shot_ms']}-{pickup['kind']}",map='bloodrun',physics='unknown',physics_verified=False,geometry_verified=False,source_sha256=audit['demo_sha256'],source_kind='observed_solo_approach',requires_airborne_movement=any(x['ground_entity']==1023 for x in samples),start_ms=first['time_ms'],pickup_ms=t,item_kind=pickup['kind'],item_protocol_id=event['parameter'],approach_position=samples[-1]['position'],position_reviewed=False,position_semantics='player_position_at_pickup_not_exact_item_origin',points=[dict(time_ms=x['time_ms'],position=x['position'],viewangles=x['viewangles'],velocity=x['velocity'],weapon_id=x['weapon_id'],on_ground=x['ground_entity']!=1023) for x in samples],ready_for_execution=False))
    return routes

def main():
    ap=argparse.ArgumentParser();ap.add_argument('folder',type=Path);ap.add_argument('output',type=Path);args=ap.parse_args()
    rows=[json.loads(s) for s in (args.folder/'snapshots.jsonl').read_text().splitlines()]
    audit=json.loads((args.folder/'rocketjump_audit.json').read_text())
    if audit['demo']!='nekitz0r_ZTN_solo_01.dm_91': raise ValueError('This exporter is currently scoped to the verified ZTN recording')
    routes=export_routes(rows,audit)
    args.output.write_text(json.dumps(dict(routes=routes,note='Review only; not a traversability mesh or recorded raw inputs'),ensure_ascii=False,indent=2),encoding='utf-8')
    print('Exported observed resource approaches:',len(routes))
if __name__=='__main__': main()
