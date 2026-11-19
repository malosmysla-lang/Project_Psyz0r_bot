"""Map one observed owner camera turn to a bounded full-turn template."""
import argparse
import gzip
import json
from pathlib import Path

def main():
    ap=argparse.ArgumentParser();ap.add_argument('episodes',type=Path);args=ap.parse_args()
    with gzip.open(args.episodes,'rt',encoding='utf-8') as f:episodes=json.load(f)
    sample=next(s for s in episodes if s['actor']=='nekitz0r' and s['source']=='8ca10a0ddcc95de7c47950a3bf5cad791c92e41dc6926e0a6af810be9a4aea87')
    trace=[p for p in sample['view_trace'] if 2400<=p['elapsed_ms']<=3350]
    yaw=[0.0]
    for a,b in zip(trace,trace[1:]):yaw.append(yaw[-1]+((b['yaw']-a['yaw']+180)%360-180))
    assert abs(yaw[-1])>=359.9 and len(trace)==39
    scale=360/abs(yaw[-1]);values=[round(v*scale,5) for v in yaw]
    report={'source_demo_sha256':sample['source'],'actor':'nekitz0r','first_takeoff_ms':sample['first_takeoff_ms'],
            'source_window_after_takeoff_ms':[2400,3350],'observed_net_yaw_degrees':yaw[-1],
            'duration_ms':950,'template_yaw_offsets_degrees':values,'raw_keys_recorded':False,
            'adaptation':'Relative POV yaw is scaled to exactly one full turn; world wish movement is preserved, interrupted by combat.'}
    root=Path(__file__).resolve().parents[1]
    (root/'docs/training/V2_SPIN_REFERENCE.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    (root/'adapter/native/psyz_v2_spin_reference.h').write_text(
        '/* Adapted owner POV turn, provenance: V2_SPIN_REFERENCE.json. */\nstatic const float psyz_v2_spin_yaw[39] = {'+
        ','.join(f'{v:.5f}f' for v in values)+'};\n',encoding='utf-8')
    print(json.dumps({'source_net_turn':yaw[-1],'template_net_turn':values[-1],'duration_ms':950}))

if __name__=='__main__':main()
