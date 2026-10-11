"""Summarize actual isolated-server observations, without treating intent as success."""
import argparse
import hashlib
import json
import re
from pathlib import Path


def summarize(path):
    data = path.read_bytes()
    lines = data.decode('utf-8', errors='replace').splitlines()
    pickups, jumps, routes, strafes, repaths = [], [], [], [], []
    openings = []
    for line in lines:
        fields = dict(re.findall(r'(\w+)=([^\s]+)', line))
        if line.startswith(('PSYZ_OPENING_BEGIN ', 'PSYZ_OPENING_PLAN ', 'PSYZ_OPENING_PICKUP ', 'PSYZ_OPENING_END ')):
            openings.append(dict(event=line.split()[0], **fields))
        if line.startswith('PSYZ_PICKUP '):
            pickups.append(fields)
        elif line.startswith('PSYZ_RJ_END '):
            fields['success'] = fields.get('higher') == '1' or fields.get('pickup') == '1'
            jumps.append(fields)
        elif line.startswith('PSYZ_DEMO_ROUTE '):
            routes.append(fields)
        elif line.startswith('PSYZ_STRAFE '):
            strafes.append(fields)
        elif line.startswith('PSYZ_REPATH '):
            repaths.append(fields)
    matched = [p for p in pickups if p.get('entity') == p.get('target') and int(p.get('route', '-1')) >= 0]
    return dict(
        log_sha256=hashlib.sha256(data).hexdigest(),
        actual_pickups=pickups,
        actual_pickup_count=len(pickups),
        demo_route_activations=len(routes),
        pickups_with_matching_target_and_active_demo_route=matched,
        strafe_command_observations=strafes,
        rocketjump_results=jumps,
        rocketjump_successes=sum(j['success'] for j in jumps),
        repath_count=len(repaths),
        opening_events=openings,
        opening_actual_pickups=sum(e['event']=='PSYZ_OPENING_PICKUP' for e in openings),
        opening_completed_orders=sum(e['event']=='PSYZ_OPENING_END' and e.get('reason')=='completed_pickups' for e in openings),
        interpretation='Observed events only; route activation is not route completion. Probe execution is not autonomous tactical selection.',
    )


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('log', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--mode', choices=('normal', 'rocketjump_probe', 'combat'), required=True)
    args = parser.parse_args()
    result = summarize(args.log)
    result['mode'] = args.mode
    args.output.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({k: result[k] for k in ('actual_pickup_count', 'demo_route_activations', 'rocketjump_successes', 'repath_count')}))
