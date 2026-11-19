"""Mine red-pickup windows from verified demos; never infer raw inputs.

Run each UDT DLL extraction in its own process because its library is global.
Originals, chats and snapshots remain private. Only aggregate evidence is suitable
for source control; candidates do not automatically enable runtime movement.
"""
import argparse
from collections import Counter, deque
from concurrent.futures import ThreadPoolExecutor, as_completed
import gzip
import json
from pathlib import Path
import subprocess
import sys

from audit_red_boosts import analyze_window


def clean(value):
    import re
    return re.sub(r'\^[0-9]', '', value or '').strip().casefold()


def observed_actor(metadata, row, maps=None):
    # Custom snapshot exporter numbers states from 1; UDT_json arrays use 0.
    index = row['game_state_number'] - 1
    states = metadata.get('gameStates', [])
    if not 0 <= index < len(states):
        return None
    maps = maps or {'bloodrun'}
    if '*' not in maps and states[index].get('configStringValues', {}).get('mapname', '').casefold() not in maps:
        return None
    choices = [p for p in states[index].get('players', [])
               if p.get('clientNumber') == row['client'] and
               p.get('startTime', -1) <= row['time_ms'] <= p.get('endTime', float('inf'))]
    names = {clean(p.get('cleanName')) for p in choices}
    return next(iter(names)) if len(names) == 1 else None


def inspect_snapshots(path, metadata, players, maps=None):
    history = deque()
    windows = []
    observed = Counter()
    opener = gzip.open if path.suffix == '.gz' else open
    with opener(path, 'rt', encoding='utf-8') as stream:
        for line in stream:
            row = json.loads(line)
            actor = observed_actor(metadata, row, maps)
            if history:
                last = history[-1]
                if any(last[k] != row[k] for k in ('client', 'segment', 'game_state_number')) or row['time_ms'] <= last['time_ms']:
                    history.clear()
            history.append(row)
            while history and row['time_ms'] - history[0]['time_ms'] > 8000:
                history.popleft()
            if actor:
                observed[actor] += 1
            if actor not in players or not any(p['kind'] == 'red' for p in row['observed_pov_pickups']):
                continue
            window = analyze_window(list(history))
            window['actor'] = actor
            window['game_state_number'] = row['game_state_number']
            config = metadata['gameStates'][row['game_state_number']-1].get('configStringValues', {})
            window['map'] = config.get('mapname')
            window['physics'] = {k:config.get(k) for k in ('g_gravity','timescale','g_factory','g_loadout')}
            window['actor_continuity_verified'] = all(observed_actor(metadata,p,maps)==actor for p in history)
            window['pickup_position'] = row['position']
            window['no_detected_boost_or_discontinuity'] = not window['boosts'] and not window['discontinuities_ms']
            window['raw_controls_verified'] = False
            windows.append(window)
    return windows, observed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--intake', type=Path, required=True)
    ap.add_argument('--dll', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--players', nargs='+', default=['nekitz0r', 'AGENT', 'PsyRoZ'])
    ap.add_argument('--workers', type=int, default=4)
    ap.add_argument('--maps', nargs='+', default=['bloodrun'])
    ap.add_argument('--opponent')
    ap.add_argument('--snapshot-cache', type=Path)
    args = ap.parse_args()
    intake = args.intake.resolve(strict=True)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    players = {clean(p) for p in args.players}
    maps = {m.casefold() for m in args.maps}
    context = {'players':sorted(players), 'maps':sorted(maps), 'opponent':clean(args.opponent)}
    parsed = json.loads((intake/'PARSED_DEMOS.private.json').read_text(encoding='utf-8'))
    manifest = json.loads((intake/'RECORDINGS_MANIFEST.private.json').read_text(encoding='utf-8'))
    originals = {m['sha256']: m for m in manifest}
    selected = []
    for item in parsed:
        if '*' not in maps and not any(s.get('configStringValues', {}).get('mapname', '').lower() in maps
                   for s in item.get('game_states', [])):
            continue
        metadata = json.loads((intake/item['export']).read_text(encoding='utf-8-sig'))
        participants = {clean(p.get('cleanName')) for s in metadata.get('gameStates', [])
                        for p in s.get('players', [])}
        if participants & players and (not args.opponent or clean(args.opponent) in participants):
            selected.append((item, metadata))
    print(json.dumps({'selected_demos':len(selected)}), flush=True)

    def process(pair):
        item, metadata = pair
        digest = item['sha256']
        root = output/digest
        root.mkdir(exist_ok=True)
        demo = intake/originals[digest]['preserved']
        if demo.suffix.casefold() != '.dm_91':
            return {'sha256':digest, 'status':'unsupported_protocol_retained', 'protocol':demo.suffix}
        snapshot = root/'snapshots.jsonl'
        compressed = root/'snapshots.jsonl.gz'
        if args.snapshot_cache:
            cached = args.snapshot_cache/digest/'snapshots.jsonl.gz'
            if cached.is_file():
                compressed = cached.resolve()
        episodes_path = root/'red-windows.private.json.gz'
        if episodes_path.exists() and compressed.exists():
            result = json.loads((root/'summary.private.json').read_text(encoding='utf-8'))
            if result.get('audit_revision') == 3 and result.get('context') == context:
                return result
        if not compressed.exists():
            result = subprocess.run([sys.executable, '-X', 'utf8', str(Path(__file__).with_name('extract_movement.py')),
                                 str(demo), '--dll', str(args.dll.resolve()), '--output', str(snapshot)],
                                capture_output=True, timeout=240)
            (root/'extract.log').write_bytes(result.stdout + result.stderr)
            if result.returncode:
                return {'sha256':digest, 'status':'extract_failed'}
        windows, observed = inspect_snapshots(compressed if compressed.exists() else snapshot, metadata, players, maps)
        for window in windows:
            window['demo_sha256'] = digest
        with gzip.open(episodes_path, 'wt', encoding='utf-8') as stream:
            json.dump(windows, stream)
        if snapshot.exists():
            with snapshot.open('rb') as src, gzip.open(compressed, 'wb', compresslevel=3) as dst:
                import shutil
                shutil.copyfileobj(src, dst)
            # Only this tool's own temporary export is removed; the verified input remains.
            snapshot.unlink()
        summary = {'audit_revision':3, 'context':context, 'sha256':digest, 'status':'parsed', 'red_pickups':len(windows),
                   'actors':dict(Counter(w['actor'] for w in windows)),
                   'observed_pov_snapshots':dict(observed),
                   'boost_sequences':dict(Counter(s['kind'] for w in windows for s in w['sequences'])),
                   'discontinuity_windows':sum(bool(w['discontinuities_ms']) for w in windows)}
        (root/'summary.private.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
        return summary

    reports = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(process, pair):pair[0]['sha256'] for pair in selected}
        for future in as_completed(futures):
            try:
                reports.append(future.result())
            except Exception as exc:
                reports.append({'sha256':futures[future], 'status':'error', 'reason':str(exc)})
            if len(reports) % 10 == 0:
                print(json.dumps({'processed':len(reports), 'of':len(selected)}), flush=True)
    actors = Counter()
    boosts = Counter()
    for report in reports:
        actors.update(report.get('actors', {}))
        boosts.update(report.get('boost_sequences', {}))
    summary = {'selected_demos':len(selected), 'statuses':dict(Counter(r['status'] for r in reports)),
               'red_pickups_by_actor':dict(actors), 'boost_sequences':dict(boosts),
               'discontinuity_windows':sum(r.get('discontinuity_windows',0) for r in reports),
               'self_damage_causality_verified':False, 'runtime_routes_enabled':False,
               'note':'Successful observed pickup; boost/teleport classifications require further validation.'}
    (output/'DEMO_REPORTS.private.json').write_text(json.dumps(reports, indent=2), encoding='utf-8')
    (output/'SUMMARY.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary), flush=True)
    return 0 if all(r['status'] in {'parsed','unsupported_protocol_retained'} for r in reports) else 1


if __name__ == '__main__':
    raise SystemExit(main())
