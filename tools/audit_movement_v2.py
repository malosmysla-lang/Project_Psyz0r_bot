"""Compare recorded circle/strafe starts by observed actor and map."""
import argparse
from collections import defaultdict
import gzip
import json
from pathlib import Path

from analyze_strafe_starts import analyse_rows,angle_delta,summary
from audit_red_v2 import observed_actor


def speed_since_ground_start(sample,time_ms):
    target=time_ms-sample['ground_prestrafe_ms']
    choices=[r for r in sample['view_trace'] if abs(r['elapsed_ms']-target)<=50]
    if not choices:return None
    return min(choices,key=lambda r:abs(r['elapsed_ms']-target))['speed']


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--intake',type=Path,required=True)
    ap.add_argument('--snapshots',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args()
    parsed=json.loads((args.intake/'PARSED_DEMOS.private.json').read_text(encoding='utf-8'))
    metadata={d['sha256']:d for d in parsed}
    wanted={'nekitz0r','agent','psyroz'}
    samples=[];files=list(args.snapshots.glob('*/snapshots.jsonl.gz'))
    for index,path in enumerate(files,1):
        identity=path.parent.name
        info=json.loads((args.intake/metadata[identity]['export']).read_text(encoding='utf-8-sig'))
        groups=defaultdict(list)
        with gzip.open(path,'rt',encoding='utf-8') as stream:
            for line in stream:
                row=json.loads(line);actor=observed_actor(info,row)
                if actor in wanted:
                    groups[(actor,row['game_state_number'],row['segment'],row['client'])].append(row)
        for (actor,state,segment,client),rows in groups.items():
            for sample in analyse_rows(rows,identity):
                trace=sample['view_trace']
                turns=[angle_delta(b['yaw'],a['yaw']) for a,b in zip(trace,trace[1:])]
                sample.update(actor=actor,game_state_number=state,map='bloodrun',
                              net_yaw_turn_deg=round(sum(turns),3),
                              absolute_yaw_travel_deg=round(sum(abs(t) for t in turns),3),
                              live_bot_reproduction_verified=False)
                sample['speed_at_ground_start_2s']=speed_since_ground_start(sample,2000)
                sample['speed_at_ground_start_4s']=speed_since_ground_start(sample,4000)
                samples.append(sample)
        if index%30==0:print(json.dumps({'files':index,'total':len(files),'starts':len(samples)}),flush=True)
    fields=['ground_prestrafe_ms','pre_jump_speed','first_air_max_speed','second_air_max_speed',
            'landing_to_second_takeoff_ms','peak_2s','peak_4s','ground_yaw_sweep_abs_deg',
            'net_yaw_turn_deg','absolute_yaw_travel_deg','speed_at_ground_start_2s','speed_at_ground_start_4s']
    actors={}
    for actor in sorted(wanted):
        rows=[s for s in samples if s['actor']==actor]
        actors[actor]={'qualified_starts':len(rows),'metrics':{k:summary([s[k] for s in rows if s.get(k) is not None and
                       (k not in {'peak_2s','peak_4s'} or s['observed_horizon_ms']>=(2000 if k=='peak_2s' else 4000))]) for k in fields},
                       'coverage_2s_from_ground':sum(s['speed_at_ground_start_2s'] is not None for s in rows),
                       'coverage_4s_from_ground':sum(s['speed_at_ground_start_4s'] is not None for s in rows),
                       'observed_net_turn_at_least_300_degrees':sum(abs(s['net_yaw_turn_deg'])>=300 for s in rows)}
    result={'maps':['bloodrun'],'files_scanned':len(files),'actors':actors,
            'raw_keys_or_mouse_available':False,'live_bot_reproduction_verified':False,
            'time_reference':'speed_at_ground_start uses the observed low-speed start; peak fields use first takeoff and require full coverage',
            'interpretation':'Measured starts filtered for continuity, no firing/damage and a second jump. Camera rotation is not an automatic command prescription.'}
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/'MOVEMENT_REFERENCE.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    with gzip.open(args.output/'MOVEMENT_EPISODES.private.json.gz','wt',encoding='utf-8') as stream:json.dump(samples,stream)
    print(json.dumps(result),flush=True)


if __name__=='__main__':main()
