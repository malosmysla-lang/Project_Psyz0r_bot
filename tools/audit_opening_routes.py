"""Check observed opening destinations and demo-route coverage, not optimality."""
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    plan_path = ROOT / 'config/bloodrun_openings.json'
    route_path = ROOT / 'config/bloodrun_prealpha_bank.json'
    items = json.loads((ROOT / 'out/research_stock_ai/bloodrun_items.json').read_text())
    plans = json.loads(plan_path.read_text())['plans']
    routes = json.loads(route_path.read_text())['routes']
    red = json.loads((ROOT / 'docs/training/BLOODRUN_RED_APPROACHES.json').read_text())
    for r in red['selected_grounded_approaches']:
        target = next(e for e in items if e['classname'] == 'item_armor_body')
        routes.append(dict(target_class='item_armor_body', target_position=target['position'], points=r['points']))
    result = []
    main_guns = {'weapon_lightning', 'weapon_rocketlauncher', 'weapon_railgun'}
    for index, plan in enumerate(plans):
        position = plan['start']
        legs = []
        for step in plan['steps']:
            matching = [r for r in routes if r['target_class'] == step['classname']
                        and math.dist(r['target_position'], step['position']) < 16]
            gap = min((math.dist(position, r['points'][0]['p']) for r in matching), default=None)
            static = any(e['classname'] == step['classname'] and math.dist(e['position'], step['position']) < 16 for e in items)
            legs.append(dict(classname=step['classname'], static_destination_valid=static,
                             nearest_demo_route_start_gap=gap, demo_route_start_in_97_units=gap is not None and gap < 97,
                             stock_aas_fallback_required=gap is None or gap >= 97,
                             straight_distance=math.dist(position, step['position']),
                             height_delta=step['position'][2] - position[2]))
            position = step['position']
        result.append(dict(plan=index, source_sha256=plan['source_sha256'],
                           eligible_main_weapon=any(s['classname'] in main_guns for s in plan['steps']), legs=legs))
    output = dict(plans=len(plans), eligible_plans=sum(p['eligible_main_weapon'] for p in result),
                  invalid_destinations=sum(not l['static_destination_valid'] for p in result for l in p['legs']),
                  demo_covered_legs=sum(l['demo_route_start_in_97_units'] for p in result for l in p['legs']),
                  total_legs=sum(len(p['legs']) for p in result),
                  source_hashes={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in [plan_path, route_path]},
                  records=result, optimality_verified=False,
                  note='Static geometry/route-bank audit only. AAS reachability and live timing must be tested.')
    (ROOT / 'docs/training/OPENING_ROUTE_AUDIT_20261012.json').write_text(json.dumps(output, indent=2))
    print(json.dumps({k: v for k, v in output.items() if k not in ('records', 'source_hashes')}))


if __name__ == '__main__':
    main()
