"""Export conservative observed opening orders, not claims of optimal play."""
import json
import argparse
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLASSES = dict(rocket='weapon_rocketlauncher', lightning='weapon_lightning',
               railgun='weapon_railgun', shotgun='weapon_shotgun', plasma='weapon_plasmagun',
               grenade='weapon_grenadelauncher', mega='item_health_mega',
               red='item_armor_body', yellow='item_armor_combat')


def select(records, items):
    result = []
    for r in records:
        if (r['status'] != 'observed' or r['start_delay_ms'] > 1500
                or r['observed_ms'] < 5000 or r['observed_health_loss'] > 40
                or len(r['first_three']) < 2):
            continue
        steps = []
        for p in r['first_three']:
            classname = CLASSES.get(p['kind'])
            matches = [e for e in items if e['classname'] == classname
                       and math.dist(e['position'], p['position']) <= 112]
            if not matches:
                break
            e = min(matches, key=lambda e: math.dist(e['position'], p['position']))
            steps.append(dict(classname=classname, position=e['position']))
        if len(steps) < 2:
            continue
        elapsed=max(p.get('elapsed_ms',0) for p in r['first_three'])
        observed_cost=elapsed/1000*4+r['observed_health_loss']*2
        result.append(dict(start=r['start_position'], steps=steps, demo_id=r['demo_id'],
                           observed_cost=observed_cost,elapsed_ms=elapsed,
                           source_sha256=r['source_sha256'], start_delay_ms=r['start_delay_ms'],
                           observed_health_loss=r['observed_health_loss'], live_verified=False))
    return result


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--audit',type=Path,default=ROOT/'docs/training/BLOODRUN_OPENINGS.json')
    args=parser.parse_args()
    audit = json.loads(args.audit.read_text(encoding='utf-8'))
    items = json.loads((ROOT/'out/research_stock_ai/bloodrun_items.json').read_text())
    plans = select(audit['records'], items)
    if not plans:
        raise ValueError('No bounded opening candidates')
    (ROOT/'config/bloodrun_openings.json').write_text(json.dumps(dict(
        map='bloodrun', plans=plans, optimality_verified=False,
        note='Partial observed starts; loss filter includes decay/self damage'), indent=2), encoding='utf-8')
    lines = ['/* Generated candidate orders; start is observed POV, not proven spawn. */',
             'typedef struct { const char *classname; float position[3]; } PsyzOpeningStep;',
             'typedef struct { float start[3]; int count; PsyzOpeningStep steps[3]; float observed_cost; } PsyzOpeningPlan;',
             'static const PsyzOpeningPlan psyz_openings[] = {']
    vector = lambda p: '{'+','.join(f'{v:.4f}f' for v in p)+'}'
    for p in plans:
        steps = ','.join('{"'+s['classname']+'",'+vector(s['position'])+'}' for s in p['steps'])
        lines.append('{'+vector(p['start'])+','+str(len(p['steps']))+',{'+steps+'},'+f'{p["observed_cost"]:.4f}f'+'},')
    lines += ['};', '#define PSYZ_OPENING_COUNT (sizeof(psyz_openings)/sizeof(psyz_openings[0]))']
    (ROOT/'adapter/native/psyz_opening_bank.h').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    print('Opening candidates:', len(plans))


if __name__ == '__main__':
    main()
