"""Audit true match-start POV windows; observations are not executable policies."""
import gzip
import json
import math
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEAPONS = {'rocket', 'lightning', 'railgun', 'shotgun', 'plasma', 'grenade'}
STRATEGIC = WEAPONS | {'mega', 'red', 'yellow', 'green'}


def opening(rows, routes, start, state):
    window = [r for r in rows if r['game_state_number'] == state
              and start <= r['time_ms'] <= start + 30000]
    if not window or window[0]['time_ms'] - start > 250:
        return {'status': 'excluded', 'reason': 'start_not_observed'}
    first = window[0]
    active = lambda r: r['pm_type'] == 0 or (r['pm_type'] == 2 and r.get('pm_flags', 0) & 4096)
    # Restart snapshots may still show the warmup POV at the exact start tick.
    # Keep the delay explicit; never pretend that the eventual POV is the spawn.
    initial = first
    transitions = [i for i, r in enumerate(window) if r['time_ms'] <= start + 2000
                   and active(r) and r.get('health', 0) > 0
                   and (i == 0 or (r['segment'] != window[i-1]['segment']
                        and (not active(window[i-1]) or r['time_ms']-window[i-1]['time_ms'] > 100)))]
    if transitions:
        index = transitions[-1]
        window = window[index:]
        first = window[0]
    if not active(first) or not first.get('health') or first['health'] <= 0:
        return {'status': 'excluded', 'reason': 'no_alive_player_at_start'}
    end_reason = 'complete'
    observed = [first]
    for r in window[1:]:
        if r['client'] != first['client'] or r['segment'] != first['segment'] or not active(r):
            end_reason = 'pov_discontinuity'
            break
        if r['time_ms'] - observed[-1]['time_ms'] > 100:
            end_reason = 'snapshot_gap'
            break
        if math.dist(r['position'], observed[-1]['position']) > 256:
            end_reason = 'teleport_or_respawn'
            break
        observed.append(r)
        if r.get('health') is not None and r['health'] <= 0:
            end_reason = 'death_observed'
            break
    last = observed[-1]['time_ms']
    if end_reason == 'complete' and last < start + 29900:
        end_reason = 'recording_ended'
    pickups = sorted([dict(kind=r['kind'], elapsed_ms=r['pickup_ms']-start,
                           position=r['points'][-1]['p']) for r in routes
                      if r['kind'] in STRATEGIC and r['client'] == first['client']
                      and r['segment'] == first['segment']
                      and start <= r['pickup_ms'] <= last], key=lambda p: p['elapsed_ms'])
    loss = sum(max(0, a['health']-b['health']) for a, b in zip(observed, observed[1:])
               if a.get('health') is not None and b.get('health') is not None)
    return dict(status='observed', completion=end_reason, client=first['client'],
                start_delay_ms=first['time_ms']-start,
                spawn_candidate=first is initial and first['time_ms']-start <= 100,
                start_position=first['position'], observed_ms=last-first['time_ms'],
                first_weapon=next((p for p in pickups if p['kind'] in WEAPONS), None),
                first_three=pickups[:3], pickups=pickups, observed_health_loss=loss,
                damage_attribution='unknown_includes_decay_and_self_damage',
                early_frag='not_exported', control_outcome='unknown_without_opponent_observations',
                path=[dict(elapsed_ms=r['time_ms']-start, position=r['position'])
                      for i, r in enumerate(observed) if i % 20 == 0],
                live_verified=False)


def main():
    records = []
    for corpus in ('bloodrun_corpus', 'owner_bloodrun_corpus'):
        for folder in sorted((ROOT/'out'/corpus).iterdir()):
            if not folder.is_dir() or not (folder/'snapshots.jsonl.gz').exists():
                continue
            metadata = next((p for p in folder.glob('*.json')
                             if p.name not in ('snapshots.summary.json',)), None)
            if metadata is None:
                continue
            data = json.loads(metadata.read_text(encoding='utf-8-sig'))
            with gzip.open(folder/'snapshots.jsonl.gz', 'rt', encoding='utf-8') as f:
                rows = [json.loads(line) for line in f]
            with gzip.open(folder/'observed_approaches.json.gz', 'rt', encoding='utf-8') as f:
                approaches = json.load(f)
            for state, gs in enumerate(data.get('gameStates', []), 1):
                if gs.get('configStringValues', {}).get('mapname') != 'bloodrun':
                    continue
                for match in gs.get('matches', []):
                    start = match['startTime']
                    result = opening(rows, approaches['routes'], start, state)
                    result.update(source_sha256=approaches['source_sha256'], corpus=corpus,
                                  demo_id=folder.name, game_state=state, match_start_ms=start)
                    records.append(result)
    groups = []
    for r in records:
        if r['status'] != 'observed' or not r['spawn_candidate']:
            continue
        group = next((g for g in groups if math.dist(g['spawn_position'], r['start_position']) <= 64), None)
        if group is None:
            group = dict(spawn_position=r['start_position'], examples=[])
            groups.append(group)
        group['examples'].append(r)
    summaries = []
    for g in groups:
        counts = Counter(tuple(p['kind'] for p in r['first_three']) for r in g['examples'])
        summaries.append(dict(spawn_position=g['spawn_position'], examples=len(g['examples']),
                              variants=[dict(sequence=list(k), observations=v) for k, v in counts.most_common()]))
    output = dict(map='bloodrun', window_ms=30000, records=records, spawn_groups=summaries,
                  counts=dict(total=len(records), observed=sum(r['status']=='observed' for r in records),
                              complete=sum(r.get('completion')=='complete' for r in records)),
                  limitations=['Not all possible openings are covered', 'No early-frag attribution',
                               'Pickup coordinates are player positions', 'No policy enabled by this audit'])
    target = ROOT/'docs/training/BLOODRUN_OPENINGS.json'
    target.write_text(json.dumps(output, indent=2), encoding='utf-8')
    print(json.dumps(dict(counts=output['counts'], spawn_groups=len(groups))))


if __name__ == '__main__':
    main()
