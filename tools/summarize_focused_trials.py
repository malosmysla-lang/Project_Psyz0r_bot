"""Summarize actual trial evidence and surface failed integrations."""
import argparse
import json
from pathlib import Path
from audit_prealpha_log import summarize


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('folder', type=Path)
    ap.add_argument('output', type=Path)
    args = ap.parse_args()
    manifest = json.loads((args.folder/'manifest.json').read_text())
    reports = []
    for record in manifest:
        report = summarize(args.folder/(record['name']+'.log'))
        if report['log_sha256'] != record['log_sha256']:
            raise ValueError('Manifest/log SHA mismatch')
        report.update(record)
        reports.append(report)
    result = dict(trials=reports, totals=dict(
        actual_pickups=sum(r['actual_pickup_count'] for r in reports),
        completed_opening_orders=sum(r['opening_completed_orders'] for r in reports),
        rocketjump_successes=sum(r['rocketjump_successes'] for r in reports),
        strafe_command_observations=sum(len(r['strafe_command_observations']) for r in reports),
        integration_errors=sum(len(r['integration_errors']) for r in reports)),
        note='Probe success is not autonomous selection; empty probes do not verify jumps.')
    args.output.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result['totals']))


if __name__ == '__main__':
    main()
