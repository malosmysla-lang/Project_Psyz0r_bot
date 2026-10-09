"""Verified one-demo metadata export; does not claim raw input recovery."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('demo', type=Path)
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parents[1] / 'out/demo')
    args = parser.parse_args()
    demo = args.demo.resolve(strict=True)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    exe = Path(__file__).resolve().parents[1] / 'tools/udt/bin/UDT_json.exe'
    before = hashlib.sha256(demo.read_bytes()).hexdigest()
    run = subprocess.run([str(exe), '-a=gsdm', '-t=1', '-o=' + str(output), str(demo)], capture_output=True, timeout=120)
    (output/'export.log').write_bytes(run.stdout + run.stderr)
    if hashlib.sha256(demo.read_bytes()).hexdigest() != before:
        raise RuntimeError('Original demo changed')
    if run.returncode:
        raise RuntimeError('UDT failed; inspect export.log')
    parsed = json.loads((output/(demo.stem+'.json')).read_text(encoding='utf-8-sig'))
    summary = {'demo': demo.name, 'sha256': before, 'unchanged': True,
               'game_states': len(parsed.get('gameStates', [])),
               'matches': [{k: m.get(k) for k in ('map', 'firstPlaceName', 'firstPlaceScore', 'secondPlaceName', 'secondPlaceScore')}
                           for m in parsed.get('matchStats', [])],
               'raw_mouse_or_keys_verified': False}
    (output/'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=True))

if __name__ == '__main__':
    main()
