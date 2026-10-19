"""Build a reproducible aggregate report, without claiming visual demo review."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
rows = []
for file in sorted((ROOT / 'out/review_20261019').glob('*.json')):
    if file.name == 'summary.json':
        continue
    data = json.loads(file.read_text(encoding='utf-8-sig'))
    for match in data.get('matchStats', []):
        for player in match.get('playerStats', []):
            keys = ['cleanName', 'score', 'redArmorPickups', 'yellowArmorPickups',
                    'megaHealthPickups', 'rocketLauncherShots', 'rocketLauncherHits',
                    'rocketLauncherDamage', 'lightningGunAccuracy']
            rows.append(dict(demo=file.stem, map=match.get('map'), duration=match.get('duration'),
                             **{k: player.get(k) for k in keys}))
report = dict(note='Aggregate UDT exports only. Missing fields remain null; maps and partial matches are not equivalent controls.', rows=rows)
path = ROOT / 'docs/training/PLAYTEST_COMPARISON_20261019.json'
path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'{len(rows)} player observations; {len(set(r["demo"] for r in rows))} demos')
