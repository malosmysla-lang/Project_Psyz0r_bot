"""One-to-three-second red pickup boost candidates from POV evidence."""
import gzip
import json
import math
from collections import Counter, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAX_PICKUP_DELAY_MS = 3000


def identity(row):
    return tuple(row[k] for k in ('segment', 'game_state_number', 'client'))


def analyze_window(rows):
    """Keep an eight-second approach; accept a boost only <=3s before pickup.

    POV health loss cannot prove damage ownership: opponent fire is ambiguous.
    Require firing, damage and a nearby upward impulse; report that limitation.
    """
    end = rows[-1]
    if not any(p['kind'] == 'red' for p in end['observed_pov_pickups']):
        return None
    valid = all(identity(r) == identity(end) and
                (r['pm_type'] == 0 or (r['pm_type'] == 2 and r.get('pm_flags', 0) & 4096))
                for r in rows)
    contiguous = all(0 < b['time_ms']-a['time_ms'] <= 100
                     for a, b in zip(rows, rows[1:]))
    # Large discontinuities may be teleports or corrections, never a jump proof.
    discontinuities = [b['time_ms'] for a, b in zip(rows, rows[1:])
                       if math.dist(a['position'], b['position']) >
                       max(128, max(math.dist(a['velocity'], [0, 0, 0]),
                                    math.dist(b['velocity'], [0, 0, 0])) *
                           max(0, b['time_ms']-a['time_ms']) / 1000 + 64)]
    boosts = []
    if valid and contiguous:
        shots = [r for r in rows if r['weapon_id'] in (5, 8) and
                 any(e['kind'] == 'weapon_fired' for e in r['events'])]
        for a, b in zip(rows, rows[1:]):
            if not 0 <= end['time_ms']-b['time_ms'] <= MAX_PICKUP_DELAY_MS:
                continue
            if a['health'] is None or b['health'] is None:
                continue
            hp_loss = a['health']-b['health']
            armor_loss = max(0, (a['armor'] or 0)-(b['armor'] or 0))
            if hp_loss <= 1 and armor_loss <= 1:
                continue  # Exclude ordinary one-unit overstack decay.
            nearby_shots = [r for r in shots if abs(r['time_ms']-b['time_ms']) <= 300]
            impulse = [r for prev, r in zip(rows, rows[1:])
                       if abs(r['time_ms']-b['time_ms']) <= 200 and
                       r['ground_entity'] == 1023 and r['velocity'][2] > 200 and
                       r['velocity'][2]-prev['velocity'][2] > 80]
            if not nearby_shots or not impulse:
                continue
            shot = min(nearby_shots, key=lambda r: abs(r['time_ms']-b['time_ms']))
            if any(b['time_ms']-300 <= t <= end['time_ms'] for t in discontinuities):
                continue
            boosts.append(dict(kind='rocketjump_candidate' if shot['weapon_id'] == 5
                               else 'plasmajump_candidate', damage_ms=b['time_ms'],
                               shot_ms=shot['time_ms'], pickup_delay_ms=end['time_ms']-b['time_ms'],
                               hp_loss=hp_loss, armor_loss=armor_loss,
                               shot_position=shot['position'], shot_viewangles=shot['viewangles'],
                               self_damage_verified=False))
    # A plasma climb creates several damage rows.  Preserve those rows as
    # evidence, but also expose one sequence so training does not count every
    # bolt as a separate successful jump.
    sequences=[]
    for kind in ('rocketjump_candidate','plasmajump_candidate'):
        group=sorted((b for b in boosts if b['kind']==kind), key=lambda b:b['shot_ms'])
        while group:
            seq=[group.pop(0)]
            while group and group[0]['shot_ms']-seq[-1]['shot_ms'] <= 150:
                seq.append(group.pop(0))
            sequences.append(dict(kind=kind.replace('_candidate',''),
                first_shot_ms=seq[0]['shot_ms'], last_shot_ms=seq[-1]['shot_ms'],
                shot_count=len(seq), pickup_delay_ms=end['time_ms']-seq[0]['shot_ms'],
                start_position=seq[0]['shot_position'], shot_viewangles=seq[0]['shot_viewangles'],
                total_observed_loss=sum(b['hp_loss']+b['armor_loss'] for b in seq),
                self_damage_verified=False, live_verified=False))
    return dict(pickup_ms=end['time_ms'], client=end['client'], segment=end['segment'],
                category=('boost_candidate' if boosts else 'teleport_or_correction_candidate'
                          if discontinuities else 'unclassified'),
                continuity_verified=valid and contiguous, discontinuities_ms=discontinuities,
                boosts=boosts, sequences=sequences, points=rows, live_verified=False)


def main():
    episodes = []
    for corpus in ('bloodrun_corpus', 'owner_bloodrun_corpus'):
        for file in sorted((ROOT/'out'/corpus).glob('*/snapshots.jsonl.gz')):
            with gzip.open(file.parent/'observed_approaches.json.gz', 'rt', encoding='utf-8') as f:
                source_sha = json.load(f)['source_sha256']
            history = deque()
            with gzip.open(file, 'rt', encoding='utf-8') as stream:
                for line in stream:
                    row = json.loads(line)
                    if history and (identity(row) != identity(history[-1]) or
                                    row['time_ms'] <= history[-1]['time_ms']):
                        history.clear()
                    history.append(row)
                    while history and row['time_ms']-history[0]['time_ms'] > 8000:
                        history.popleft()
                    if any(p['kind'] == 'red' for p in row['observed_pov_pickups']):
                        result = analyze_window(list(history))
                        result.update(demo_id=file.parent.name, corpus=corpus, source_sha256=source_sha)
                        episodes.append(result)
    out = ROOT/'out/red_approaches'; out.mkdir(exist_ok=True)
    with gzip.open(out/'boost_episodes_3s.json.gz', 'wt', encoding='utf-8') as f:
        json.dump(episodes, f)
    summary = dict(window_after_damage_ms=MAX_PICKUP_DELAY_MS, approach_context_ms=8000,
                   total_red_pickups=len(episodes),
                   categories=dict(Counter(e['category'] for e in episodes)),
                   boost_types=dict(Counter(b['kind'] for e in episodes for b in e['boosts'])),
                   sequence_types=dict(Counter(s['kind'] for e in episodes for s in e['sequences'])),
                   candidates=[{k:v for k,v in e.items() if k!='points'}
                               for e in episodes if e['boosts']],
                   note='Damage + shot + upward impulse are candidates; POV damage ownership unknown. '
                        'Teleport/correction crossings excluded after boost. No new movement auto-enabled.')
    (ROOT/'docs/training/BLOODRUN_RED_BOOSTS_3S.json').write_text(
        json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items() if k not in ('candidates','note')}))


if __name__ == '__main__':
    main()
