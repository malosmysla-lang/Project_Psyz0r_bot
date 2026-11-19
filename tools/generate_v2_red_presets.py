"""Export five real observed RJ trajectories, retaining source attribution.

These are reference trajectories, not inferred key recordings or proof of live
bot execution. The native mask is enabled only after controlled pickup tests.
"""
import argparse
import gzip
import json
import math
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from associate_demo_aas import AasLocator


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--evidence', type=Path, required=True)
    ap.add_argument('--aas', type=Path, required=True)
    args = ap.parse_args()
    root = Path(__file__).resolve().parents[1]
    bank = json.loads((root/'docs/training/V2_RED_CANDIDATES.json').read_text(encoding='utf-8'))
    locator = AasLocator(args.aas)
    plans = []
    for index in [0, 2, 3, 4, 6]:
        candidate = bank['candidates'][index]
        row = dict(candidate['exemplar'])
        assert candidate['kind'] == 'rocketjump' and row['shot_delay_ms'] <= 200 and row['shot_count'] == 1
        heading = math.atan2(row['takeoff_velocity'][1], row['takeoff_velocity'][0])
        row['runup'] = [row['takeoff_position'][0]-140*math.cos(heading),
                        row['takeoff_position'][1]-140*math.sin(heading), row['takeoff_position'][2]]
        row['runup_area'] = locator.area(row['runup'])
        row['takeoff_area'] = locator.area(row['takeoff_position'])
        assert row['runup_area'] > 0 and row['takeoff_area'] > 0
        row['repetitions'] = candidate['successful_observed_pickups']
        row['distinct_demos'] = candidate['distinct_demos']
        with gzip.open(args.evidence/row['demo_sha256']/'red-windows.private.json.gz', 'rt', encoding='utf-8') as f:
            windows = json.load(f)
        window = next(w for w in windows if w['pickup_ms'] == row['pickup_ms'] and w['game_state_number'] == row['game_state_number'])
        points = [p for p in window['points'] if row['takeoff_ms'] <= p['time_ms'] <= row['pickup_ms']]
        row['flight'] = [{'ms':p['time_ms']-row['takeoff_ms'], 'position':p['position'], 'velocity':p['velocity'], 'viewangles':p['viewangles']}
                         for p in points if (p['time_ms']-row['takeoff_ms']) % 50 == 0 or p == points[-1]]
        row['execution_requires_release_mask'] = True
        plans.append(row)
    (root/'docs/training/V2_RED_PRESETS.json').write_text(json.dumps({'map':'bloodrun','presets':plans}, ensure_ascii=False, indent=2), encoding='utf-8')
    def vec(v): return '{'+','.join(f'{x:.5f}f' for x in v)+'}'
    header = ['/* Five observed trajectories. See docs/training/V2_RED_PRESETS.json. */',
              'typedef struct { int ms; float p[3],v[3],view[3]; } PsyzV2FlightPoint;',
              'typedef struct { float start[3],runup[3],velocity[3],shot_view[3]; int area,shot_ms,count; PsyzV2FlightPoint flight[32]; } PsyzV2RedPreset;',
              'static const PsyzV2RedPreset psyz_v2_red_presets[] = {']
    for row in plans:
        assert len(row['flight']) <= 32
        points = ','.join('{'+str(p['ms'])+','+vec(p['position'])+','+vec(p['velocity'])+','+vec(p['viewangles'])+'}' for p in row['flight'])
        header.append('{'+','.join([vec(row['takeoff_position']),vec(row['runup']),vec(row['takeoff_velocity']),vec(row['shot_viewangles']),
                                   str(row['runup_area']),str(row['shot_delay_ms']),str(len(row['flight']))]) + ',{'+points+'}},')
    header += ['};', '#define PSYZ_V2_RED_COUNT 5']
    (root/'adapter/native/psyz_v2_red_presets.h').write_text('\n'.join(header)+'\n', encoding='utf-8')
    print(json.dumps({'presets':len(plans),'observed_pickups':[p['repetitions'] for p in plans]}))


if __name__ == '__main__': main()
