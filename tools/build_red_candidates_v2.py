"""Build reviewable takeoff/shot envelopes, not blindly enabled replay routes."""
import argparse
from collections import Counter, defaultdict
import gzip
import json
import math
from pathlib import Path
from statistics import median


def takeoff_window(window, sequence):
    shot=sequence['first_shot_ms']
    points=window['points']
    grounded=[p for p in points if shot-1000<=p['time_ms']<=shot and p['ground_entity']!=1023]
    if not grounded:
        return None
    start=grounded[-1]
    if start.get('health') is None or start.get('armor') is None:
        return None
    # These are the recorded takeoff state and shot state, deliberately separate.
    return {'takeoff_ms':start['time_ms'],'takeoff_position':start['position'],
            'takeoff_velocity':start['velocity'],'takeoff_viewangles':start['viewangles'],
            'takeoff_speed_xy':math.hypot(*start['velocity'][:2]),
            'shot_delay_ms':shot-start['time_ms'],'shot_position':sequence['start_position'],
            'shot_viewangles':sequence['shot_viewangles'],
            'shot_count':sequence['shot_count'],
            'shot_span_ms':sequence['last_shot_ms']-shot,
            'pickup_delay_ms':window['pickup_ms']-start['time_ms'],
            'pickup_position':window['pickup_position'],
            'height_to_pickup':window['pickup_position'][2]-start['position'][2],
            'health_before':start['health'],'armor_before':start['armor']}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('evidence',type=Path)
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args()
    groups=defaultdict(list)
    rejected=Counter()
    consumed=set()
    for file in sorted(args.evidence.glob('*/red-windows.private.json.gz')):
        with gzip.open(file,'rt',encoding='utf-8') as stream:
            windows=json.load(stream)
        for window in windows:
            if not window.get('actor_continuity_verified'):
                rejected['unverified_actor_continuity']+=1
                continue
            if not window['continuity_verified']:
                rejected['discontinuous_window']+=1
                continue
            for sequence in window['sequences']:
                launch=takeoff_window(window,sequence)
                if launch is None:
                    rejected['no_observed_takeoff']+=1
                    continue
                # The Red platform is above this launch. A shot on top followed
                # by a nearby pickup is not a learned climb onto that platform.
                if launch['height_to_pickup']<64:
                    rejected['no_platform_ascent']+=1
                    continue
                key=(sequence['kind'],tuple(round(v/64) for v in launch['takeoff_position']))
                identity=(window['demo_sha256'],window['client'],window['pickup_ms'],key)
                if identity in consumed:
                    continue
                consumed.add(identity)
                groups[key].append(dict(launch,actor=window['actor'],demo_sha256=window['demo_sha256'],
                                        pickup_ms=window['pickup_ms'],game_state_number=window['game_state_number']))
    candidates=[]
    def medvec(rows,key):return [round(median(row[key][i] for row in rows),4) for i in range(3)]
    for (kind,grid),rows in groups.items():
        # Keep a real observed exemplar: independently averaging angles and
        # positions would manufacture a route that no recorded player executed.
        center=medvec(rows,'takeoff_position')
        exemplar=min(rows,key=lambda row:math.dist(row['takeoff_position'],center))
        candidates.append({'kind':kind,'takeoff_grid':grid,'successful_observed_pickups':len(rows),
                           'distinct_demos':len({row['demo_sha256'] for row in rows}),
                           'actors':dict(Counter(row['actor'] for row in rows)),
                           'repetition_band':20 if len(rows)>=20 else 15 if len(rows)>=15 else 10 if len(rows)>=10 else 0,
                           'exemplar':exemplar,
                           'observed_ranges':{key:[min(row[key] for row in rows),max(row[key] for row in rows)]
                                              for key in ('takeoff_speed_xy','shot_delay_ms','pickup_delay_ms')},
                           'self_damage_causality_verified':False,'collision_geometry_verified':False,
                           'live_bot_pickup_verified':False,'automatic_execution_enabled':False})
    candidates.sort(key=lambda row:(-row['distinct_demos'],-row['successful_observed_pickups'],row['kind']))
    report={'version':'V2.0.0-red_rj_instruction','map':'bloodrun','candidates':candidates,
            'rejected':dict(rejected),'note':'Successful recorded pickups with candidate boost signatures. No success denominator or runtime acceptance is implied.'}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'clusters':len(candidates),'repeated_10plus':sum(c['successful_observed_pickups']>=10 for c in candidates),
                      'kinds':dict(Counter(c['kind'] for c in candidates)),'rejected':dict(rejected)}))


if __name__=='__main__':
    main()
