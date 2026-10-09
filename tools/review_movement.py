"""Produce a conservative manual review queue from POV snapshots, not training rules."""
import argparse
import csv
from collections import Counter
import json
import math
from pathlib import Path

def review(rows, min_stationary_seconds=1, stationary_speed=20, discontinuity_distance=256):
    candidates, speeds, view_rates, routes = [], [], [], []
    history = []
    previous = None
    stationary_start = None
    def finish_stationary(end):
        nonlocal stationary_start
        if stationary_start and end['time_ms'] - stationary_start['time_ms'] >= min_stationary_seconds * 1000:
            candidates.append(dict(kind='stationary_review', start_ms=stationary_start['time_ms'],
                                   end_ms=end['time_ms'], client=end['client'],
                                   note='Could be deliberate waiting/aiming; not proof of a navigation fault'))
        stationary_start = None
    for row in rows:
        continuous = previous and row['segment'] == previous['segment'] and row['client'] == previous['client']
        dt = (row['time_ms'] - previous['time_ms']) / 1000 if continuous else 0
        continuous = continuous and 0 < dt <= .1
        if not continuous and previous:
            finish_stationary(previous)
            history.clear()
        if continuous and math.dist(row['position'], previous['position']) > discontinuity_distance:
            history.clear()
        if row['pm_type'] == 0:
            history.append(row)
            history = [r for r in history if row['time_ms'] - r['time_ms'] <= 10000]
            for pickup in row.get('observed_pov_pickups', []):
                if pickup['kind'] in ('mega', 'red', 'yellow', 'green'):
                    routes.append(dict(item=pickup['kind'], pickup_time_ms=row['time_ms'],
                                       client=row['client'], segment=row['segment'],
                                       duration_seconds=(row['time_ms'] - history[0]['time_ms']) / 1000,
                                       observed_path_length=sum(math.dist(a['position'], b['position']) for a, b in zip(history, history[1:])),
                                       samples=[dict(time_ms=r['time_ms'], position=r['position'], weapon_id=r['weapon_id']) for r in history],
                                       note='Up to 10 seconds before POV pickup, not a validated route or exact item spawn location'))
        else:
            history.clear()
        if row['pm_type'] == 0:
            speeds.append(row['speed_xy'])
            if row['speed_xy'] < stationary_speed:
                stationary_start = stationary_start or row
            elif previous:
                finish_stationary(previous)
            if continuous and previous['pm_type'] == 0:
                yaw_delta = (row['viewangles'][1] - previous['viewangles'][1] + 180) % 360 - 180
                view_rates.append(abs(yaw_delta) / dt)
                distance = math.dist(row['position'], previous['position'])
                if distance > discontinuity_distance:
                    candidates.append(dict(kind='position_discontinuity', time_ms=row['time_ms'], client=row['client'],
                                           distance=distance, note='Check teleport/respawn/correction; do not imitate as movement'))
                if row['velocity'][2] > 200 and previous['velocity'][2] <= 200:
                    candidates.append(dict(kind='upward_velocity_onset', time_ms=row['time_ms'], client=row['client'],
                                           velocity_z=row['velocity'][2], note='Jump/pad/rocket/damage possible; cause not established'))
                if row['weapon_id'] != previous['weapon_id']:
                    candidates.append(dict(kind='weapon_change', time_ms=row['time_ms'], client=row['client'],
                                           from_id=previous['weapon_id'], to_id=row['weapon_id']))
        elif previous:
            finish_stationary(previous)
        previous = row
    if previous:
        finish_stationary(previous)
    def percentile(values, q):
        values = sorted(values)
        return values[int((len(values) - 1) * q)] if values else None
    return dict(snapshots=len(rows), normal_pm_snapshots=len(speeds),
                speed_xy_median=percentile(speeds, .5), speed_xy_p95=percentile(speeds, .95),
                observed_yaw_degrees_per_second_p95=percentile(view_rates, .95),
                candidates=candidates, item_approaches=routes, raw_mouse_or_keys_verified=False,
                note='Times are demo server times, not necessarily the duel clock. Normal pm_type is a protocol field, not evidence of effort.')

def main():
    p = argparse.ArgumentParser()
    p.add_argument('snapshots', type=Path)
    p.add_argument('--output', type=Path, default=Path('out/demo/movement_review.json'))
    p.add_argument('--stationary-seconds', type=float, default=1)
    p.add_argument('--match-stats', type=Path, help='UDT_json export containing exactly one match')
    args = p.parse_args()
    if (args.output.resolve() == args.snapshots.resolve()
            or args.output.with_suffix('.csv').resolve() == args.snapshots.resolve()
            or (args.match_stats and args.output.resolve() == args.match_stats.resolve())):
        p.error('Output must not replace source snapshots or match stats')
    if args.stationary_seconds <= 0:
        p.error('stationary-seconds must be positive')
    rows = [json.loads(line) for line in args.snapshots.read_text(encoding='utf-8').splitlines()]
    match = None
    if args.match_stats:
        matches = json.loads(args.match_stats.read_text(encoding='utf-8-sig')).get('matchStats', [])
        if len(matches) != 1:
            p.error('Expected one match; select a single game state first')
        match = matches[0]
        if len({r['segment'] for r in rows}) != 1:
            p.error('Match alignment requires a single POV/time segment')
        rows = [r for r in rows if match['startTime'] <= r['time_ms'] <= match['endTime']]
    result = review(rows, args.stationary_seconds)
    if match:
        fields = dict(mega='megaHealthPickups', red='redArmorPickups', yellow='yellowArmorPickups', green='greenArmorPickups')
        observed = Counter(route['item'] for route in result['item_approaches'])
        clients = {row['client'] for row in rows}
        if len(clients) != 1:
            p.error('POV changed within the match')
        player = next((r for r in match['playerStats'] if r['clientNumber'] in clients), None)
        expected = {item: player.get(field) for item, field in fields.items()} if player else {}
        result['match_alignment'] = dict(map=match['map'], start_ms=match['startTime'], end_ms=match['endTime'],
                                        observed_pickups={k: observed[k] for k in fields}, exported_stats_pickups=expected,
                                        totals_match=all(expected.get(k) == observed[k] for k in fields))
        for route in result['item_approaches']:
            route['duel_seconds'] = (route['pickup_time_ms'] - match['startTime']) / 1000
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.resolve() == args.snapshots.resolve():
        p.error('Output must differ from input')
    args.output.write_text(json.dumps(result, indent=2), encoding='utf-8')
    with args.output.with_suffix('.csv').open('w', encoding='utf-8', newline='') as output:
        writer = csv.DictWriter(output, fieldnames=['item', 'pickup_time_ms', 'duel_seconds', 'duration_seconds', 'observed_path_length', 'client'])
        writer.writeheader()
        for route in result['item_approaches']:
            writer.writerow({k: route.get(k) for k in writer.fieldnames})
    print(json.dumps({k: v for k, v in result.items() if k not in ('candidates', 'item_approaches')}))
    print('Review candidates:', len(result['candidates']))
    print('POV item approaches:', len(result['item_approaches']))

if __name__ == '__main__':
    main()
