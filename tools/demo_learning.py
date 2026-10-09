"""Read-only demonstration pipeline: UDT snapshots/chat -> reviewable episodes.

No neural training, raw-input claim, inferred HP fill or live game commands.
Chat marker alignment is accepted only for the same recorded POV/client/time domain.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess

try:
    from .extract_movement import extract
except ImportError:
    from extract_movement import extract

LABELS = {'listen', 'hide', 'escape', 'punish mega', 'punish red', 'rocketjump',
          'cycle', 'spawntrap', 'circlejump', 'singlebeat', 'halfbeat',
          'plasmajump', 'plasmaclimb', 'weapon', 'combat_strafe'}


def label_text(text):
    text = re.sub(r'\^[0-9]', '', str(text)).strip().casefold()
    if not text.startswith('#bot '):
        return None
    label = ' '.join(text[5:].split())
    return label if label in LABELS else None


def chat_markers(data):
    result = []
    for event in data.get('chat', []):
        label = label_text(event.get('cleanMessage', event.get('clean message', event.get('message', ''))))
        if label:
            result.append(dict(label=label, time_ms=event.get('serverTime', event.get('server time')),
                               client=event.get('clientNumber', event.get('client number')),
                               game_state_number=event.get('gameStateNumber', event.get('game state number')),
                               clock='demo_server_time', source='udt_chat',
                               before_ms=2000, after_ms=3000))
    return result


def audit_chat_alignment(data, rows, owner_client):
    """Verify exported chat clock/schema on ordinary messages without inventing labels."""
    result = []
    for event in data.get('chat', []):
        client=event.get('clientNumber',event.get('client number'))
        time=event.get('serverTime',event.get('server time'))
        gs=event.get('gameStateNumber',event.get('game state number'))
        if client != owner_client or type(time) is not int:
            continue
        candidates=[r for r in rows if r['client']==client and r.get('game_state_number')==gs and abs(r['time_ms']-time)<=50]
        if not candidates:
            result.append(dict(time_ms=time, client=client, aligned=False));continue
        nearest=min(candidates,key=lambda r:abs(r['time_ms']-time))
        result.append(dict(time_ms=time, client=client, aligned=True,
                           alignment_error_ms=nearest['time_ms']-time, segment=nearest['segment'],
                           normal_movement_state=nearest['pm_type']==0, position=nearest['position'],
                           annotation_label=label_text(event.get('cleanMessage',event.get('message','')))))
    return result


def continuous(a, b):
    return (a['client'] == b['client'] and a['segment'] == b['segment']
            and 0 < b['time_ms'] - a['time_ms'] <= 100
            and a['pm_type'] == b['pm_type'] == 0
            and math.dist(a['position'], b['position']) <= 256)


def metrics(samples):
    first, last = samples[0], samples[-1]
    def loss(field):
        a, b = first.get(field), last.get(field)
        return None if a is None or b is None else a - b
    return dict(duration_ms=last['time_ms']-first['time_ms'],
                observed_path_length=sum(math.dist(a['position'], b['position']) for a, b in zip(samples, samples[1:])),
                start_speed_xy=first['speed_xy'], end_speed_xy=last['speed_xy'],
                max_speed_xy=max(s['speed_xy'] for s in samples),
                net_health_delta_loss=loss('health'), net_armor_delta_loss=loss('armor'),
                self_damage_attribution_verified=False,
                measured_attempt_success=None, expected_landing_error=None,
                note='Net resource deltas may include pickups/enemy damage; not selfdamage measurement')


def build_episodes(rows, markers, *, map_name, physics, source_kind, owner_client, tolerance_ms=50):
    if physics not in ('classic', 'pql') or source_kind not in ('solo', 'combat') or not map_name:
        raise ValueError('Explicit map, physics and solo/combat kind required')
    for r in rows:
        for key in ('position', 'velocity', 'viewangles'):
            if len(r[key]) != 3 or not all(math.isfinite(x) for x in r[key]):
                raise ValueError('Non-finite snapshot vectors')
    chunks, chunk = [], []
    for r in rows:
        if r['client'] != owner_client or r['pm_type'] != 0:
            if chunk:
                chunks.append(chunk); chunk = []
            continue
        if chunk and not continuous(chunk[-1], r):
            chunks.append(chunk); chunk = []
        chunk.append(r)
    if chunk:
        chunks.append(chunk)
    episodes, rejected, stationary = [], [], []
    for marker in markers:
        m = dict(marker)
        label = m.get('label') or label_text(m.get('text', ''))
        if label not in LABELS or m.get('clock') != 'demo_server_time' or m.get('client') != owner_client:
            rejected.append(dict(marker=m, reason='unknown_label_clock_or_sender')); continue
        time = m.get('time_ms')
        if type(time) is not int or not ('segment' in m or 'game_state_number' in m):
            rejected.append(dict(marker=m, reason='missing_time_or_segment')); continue
        before, after = m.get('before_ms', 2000), m.get('after_ms', 3000)
        if (type(before) is not int or type(after) is not int or before < 0 or after < 0
                or before + after <= 0 or before + after > 30000):
            rejected.append(dict(marker=m, reason='invalid_episode_window')); continue
        matches = []
        for c in chunks:
            candidates = [r for r in c if ('segment' not in m or r['segment'] == m['segment'])
                          and ('game_state_number' not in m or r.get('game_state_number') == m['game_state_number'])
                          and abs(r['time_ms']-time) <= tolerance_ms]
            if candidates:
                nearest = min(candidates, key=lambda r: abs(r['time_ms']-time))
                matches.append((c, nearest))
        if len(matches) != 1:
            rejected.append(dict(marker=m, reason='no_unique_continuous_pov_alignment')); continue
        c, aligned = matches[0]
        samples = [r for r in c if time-before <= r['time_ms'] <= time+after]
        if len(samples) < 2:
            rejected.append(dict(marker=m, reason='too_few_samples')); continue
        episodes.append(dict(label=label, marker_source=m.get('source', 'external_sidecar'),
                             map=map_name, physics=physics, source_kind=source_kind,
                             time_ms=time, segment=aligned['segment'], client=owner_client,
                             alignment_error_ms=aligned['time_ms']-time,
                             alignment_basis='same_exported_demo_server_clock_and_pov',
                             position_at_marker=aligned['position'],
                             window_clipped=(samples[0]['time_ms']>time-before+tolerance_ms
                                             or samples[-1]['time_ms']<time+after-tolerance_ms),
                             confidence='label_supplied_needs_owner_review', samples=samples,
                             metrics=metrics(samples), route_geometry_verified=False,
                             control_sequence_reconstructed=False,
                             raw_mouse_or_keys_verified=False))
    for c in chunks:
        start = None
        def finish(end):
            nonlocal start
            if start is not None and c[end]['time_ms']-c[start]['time_ms'] >= 5000:
                stationary.append(dict(start_ms=c[start]['time_ms'], end_ms=c[end]['time_ms'],
                                       client=owner_client, segment=c[start]['segment'], position=c[start]['position'],
                                       role=None, confidence='candidate_needs_owner_review'))
            start = None
        for i, r in enumerate(c):
            # Velocity alone is insufficient: don't merge slowly drifting locations.
            if r['speed_xy'] <= 20 and abs(r['velocity'][2]) <= 20:
                if start is not None and math.dist(c[start]['position'], r['position']) > 24:
                    finish(i-1)
                if start is None:
                    start = i
            elif start is not None:
                finish(i-1)
        if start is not None:
            finish(len(c)-1)
    return dict(map=map_name, physics=physics, source_kind=source_kind, owner_client=owner_client,
                episodes=episodes, rejected_markers=rejected, stationary_positions=stationary,
                raw_mouse_or_keys_verified=False, game_commands_sent=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('demo', type=Path)
    p.add_argument('--map', dest='map_name', required=True)
    p.add_argument('--physics', choices=['classic', 'pql'], required=True)
    p.add_argument('--kind', choices=['solo', 'combat'], required=True)
    p.add_argument('--client', type=int, required=True)
    p.add_argument('--markers', type=Path, help='JSONL sidecar; clock=demo_server_time, client and segment required')
    p.add_argument('--output', type=Path, default=Path('out/demo_learning'))
    args = p.parse_args()
    demo = args.demo.resolve(strict=True)
    root = Path(__file__).resolve().parents[1]
    output = args.output.resolve()
    if (root/'out').resolve() not in output.parents or not 0 <= args.client < 64:
        p.error('Output must be a dedicated subdirectory of project out; client must be 0..63')
    if args.markers and args.markers.resolve().parent == output:
        p.error('Keep original sidecar outside output directory')
    before = hashlib.sha256(demo.read_bytes()).hexdigest()
    output.mkdir(parents=True, exist_ok=True)
    run = subprocess.run([str(root/'tools/udt/bin/UDT_json.exe'), '-a=gm', '-t=1', '-o='+str(output), str(demo)],
                         capture_output=True, timeout=120)
    (output/'udt_export.log').write_bytes(run.stdout + run.stderr)
    if run.returncode:
        raise RuntimeError('UDT chat export failed')
    data = json.loads((output/(demo.stem+'.json')).read_text(encoding='utf-8-sig'))
    recorded_maps={gs.get('configStringValues',{}).get('mapname') for gs in data.get('gameStates',[])} - {None}
    if recorded_maps and recorded_maps != {args.map_name}:
        raise ValueError('Supplied map differs from recorded map; select a single map demo')
    # Physics is explicitly supplied by the recorder, not inferred from the map name.
    summary = extract(demo, output/'snapshots.jsonl', root/'tools/udt/bin/UDT.dll')
    rows = [json.loads(line) for line in (output/'snapshots.jsonl').read_text(encoding='utf-8').splitlines()]
    markers = chat_markers(data)
    if args.markers:
        markers += [dict(json.loads(line), source='external_sidecar') for line in args.markers.read_text(encoding='utf-8-sig').splitlines() if line.strip()]
    result = build_episodes(rows, markers, map_name=args.map_name, physics=args.physics,
                            source_kind=args.kind, owner_client=args.client)
    result.update(demo=demo.name, demo_sha256=before, protocol='dm_91', parser='UDT 1.3.1',
                  physics_verification='supplied_not_measured', chat_messages=len(data.get('chat', [])),
                  source_summary=summary)
    result['chat_alignment_audit']=audit_chat_alignment(data,rows,args.client)
    if hashlib.sha256(demo.read_bytes()).hexdigest() != before:
        raise RuntimeError('Original demo changed')
    (output/'episodes.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(dict(episodes=len(result['episodes']), rejected_markers=len(result['rejected_markers']),
                         stationary_candidates=len(result['stationary_positions']), chat_messages=result['chat_messages'],
                         unchanged=True, game_commands_sent=False)))


if __name__ == '__main__':
    main()
