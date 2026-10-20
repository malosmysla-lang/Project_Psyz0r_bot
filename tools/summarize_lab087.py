"""Summarize measured matches by GUID; exclude warmup, quits and short setup games."""
import argparse
import csv
from collections import Counter, defaultdict
import datetime
import json
from pathlib import Path
import re


def clean(name):
    return re.sub(r'\^[0-9]', '', str(name))


def summarize(paths):
    events = Counter()
    stats = {}
    ends = {}
    blocks = {}
    stationary = Counter()
    samples = 0
    newest = 0
    current = {}
    malformed = 0
    for path in paths:
        with path.open(encoding='utf-8-sig') as source:
            for line in source:
                try:
                    row = json.loads(line)
                except ValueError:
                    malformed += 1
                    continue
                event = row.get('event')
                events[event] += 1
                data = row.get('data', {})
                newest = max(newest, row.get('time', 0))
                if event == 'game_start':
                    guid = data.get('detail', {}).get('MATCH_GUID')
                    if guid:
                        blocks[guid] = dict(version=row.get('version', 'legacy'), block=row.get('block', 'legacy'), match_id=row.get('match_id'))
                if event == 'game_end':
                    result = data.get('result', {})
                    guid = result.get('MATCH_GUID')
                    if guid:
                        ends[guid] = data
                        blocks.setdefault(guid, dict(version=row.get('version', 'legacy'), block=row.get('block', 'legacy'), match_id=row.get('match_id')))
                elif event == 'player_stats':
                    p = data.get('DATA', {})
                    guid = p.get('MATCH_GUID')
                    if guid and not p.get('WARMUP') and not p.get('QUIT') and not p.get('ABORTED') and p.get('PLAY_TIME', 0) >= 30:
                        # Steam IDs of bots are all zero in stats: name disambiguates mirror seats.
                        stats[(guid, clean(p.get('NAME')))] = p
                elif event == 'stationary_candidate':
                    stationary[clean(data.get('name'))] += 1
                elif event == 'sample':
                    samples += 1
                    current = dict(time=row.get('time'), block=row.get('block'), players=data.get('players', []))
    matches = []
    cohorts = defaultdict(lambda: dict(matches=0, players={}))
    for guid, end in ends.items():
        result = end.get('result', {})
        if result.get('ABORTED') or result.get('GAME_LENGTH', 0) < 30:
            continue
        players = []
        for (g, name), p in stats.items():
            if g != guid:
                continue
            weapons = {}
            for weapon, w in p.get('WEAPONS', {}).items():
                if not (w.get('S') or w.get('DG')):
                    continue
                weapons[weapon] = dict(shots=w.get('S', 0), hits=w.get('H', 0), damage=w.get('DG', 0), kills=w.get('K', 0), accuracy_pct=round(w.get('H', 0)/w['S']*100, 2) if w.get('S', 0)>0 else None)
            pickups = p.get('PICKUPS', {})
            players.append(dict(name=name, score=p.get('SCORE'), kills=p.get('KILLS'), deaths=p.get('DEATHS'),
                damage=p.get('DAMAGE', {}).get('DEALT'), red=pickups.get('RED_ARMOR', 0),
                mega=pickups.get('MEGA_HEALTH', 0), yellow=pickups.get('YELLOW_ARMOR', 0),
                combo_medals=p.get('MEDALS', {}).get('COMBOKILL', 0), weapons=weapons))
        meta = blocks.get(guid, dict(version='legacy', block='legacy'))
        complete_stats = len(players) == 2
        match = dict(guid=guid, **meta, duration=result.get('GAME_LENGTH'), players=players, complete_stats=complete_stats)
        matches.append(match)
        if complete_stats:
            cohort = cohorts[meta['version'] + ':' + meta['block']]
            cohort['matches'] += 1
            for p in players:
                c = cohort['players'].setdefault(p['name'], dict(games=0, kills=0, deaths=0, damage=0, red=0, mega=0, yellow=0, combo_medals=0, weapons={}))
                c['games'] += 1
                for key in ['kills', 'deaths', 'damage', 'red', 'mega', 'yellow', 'combo_medals']:
                    c[key] += p[key] or 0
                for weapon, w in p['weapons'].items():
                    dest = c['weapons'].setdefault(weapon, dict(shots=0, hits=0, damage=0, kills=0))
                    for key in ['shots', 'hits', 'damage', 'kills']:
                        dest[key] += w[key]
    for cohort in cohorts.values():
        for player in cohort['players'].values():
            for weapon in player['weapons'].values():
                weapon['accuracy_pct'] = round(weapon['hits']/weapon['shots']*100, 2) if weapon['shots'] else None
    return dict(generated_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        latest_event_at=datetime.datetime.fromtimestamp(newest, datetime.timezone.utc).isoformat() if newest else None,
        raw_events=dict(events), malformed_lines=malformed, completed_matches=len(matches),
        matches_with_two_final_stats=sum(x['complete_stats'] for x in matches),
        setup_ends_excluded=len(ends)-len(matches), samples=samples, stationary_candidates=dict(stationary),
        current=current, cohorts=dict(cohorts), matches=matches, automatic_learning=False,
        limits=['Stationary samples do not establish collision stalls.',
                'COMBOKILL is the engine medal, not a reconstructed weapon-switch sequence.',
                'Accuracy is weighted by shots; warmup, quits and short setup games are excluded.',
                'Only completed games with two final stats enter cohort aggregates.'])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--home', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    paths = sorted(args.home.glob('lab-events.jsonl*'), reverse=True)
    report = summarize(paths)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    tmp = args.out.with_suffix('.tmp')
    tmp.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    tmp.replace(args.out)
    csv_path = args.out.with_suffix('.csv')
    csv_tmp = csv_path.with_suffix('.tmp')
    with csv_tmp.open('w', encoding='utf-8-sig', newline='') as target:
        columns = ['guid', 'version', 'block', 'duration', 'name', 'score', 'kills', 'deaths', 'damage', 'red', 'mega', 'yellow', 'combo_medals', 'machinegun_pct', 'rocket_pct', 'lightning_pct', 'railgun_pct', 'plasma_pct']
        writer = csv.DictWriter(target, fieldnames=columns)
        writer.writeheader()
        for match in report['matches']:
            for player in match['players']:
                row = {key:match.get(key) for key in ['guid', 'version', 'block', 'duration']}
                row.update({key:player.get(key) for key in ['name', 'score', 'kills', 'deaths', 'damage', 'red', 'mega', 'yellow', 'combo_medals']})
                for key, weapon in [('machinegun_pct', 'MACHINEGUN'), ('rocket_pct', 'ROCKET'), ('lightning_pct', 'LIGHTNING'), ('railgun_pct', 'RAILGUN'), ('plasma_pct', 'PLASMA')]:
                    row[key] = player['weapons'].get(weapon, {}).get('accuracy_pct')
                writer.writerow(row)
    csv_tmp.replace(csv_path)
    print(json.dumps({key:report[key] for key in ['completed_matches', 'matches_with_two_final_stats', 'setup_ends_excluded', 'latest_event_at']}))


if __name__ == '__main__':
    main()
