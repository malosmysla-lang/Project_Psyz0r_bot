"""Finish reports after the separately running 300-demo extraction completes."""
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
INDEX=ROOT/'out/bloodrun_additional_300_20261019/analysis_index.json'
def main():
    deadline=time.monotonic()+3600
    while time.monotonic()<deadline:
        try:
            rows=json.loads(INDEX.read_text(encoding='utf-8'))['records']
            if len(rows)==300:
                break
        except (OSError,ValueError):
            pass
        time.sleep(5)
    else:
        raise RuntimeError('Extraction did not complete within one hour; no full report claimed')
    subprocess.run([sys.executable,'tools/analyze_openings.py','--corpus','bloodrun_corpus','--corpus','owner_bloodrun_corpus','--corpus','bloodrun_additional_300_20261019','--output','docs/training/BLOODRUN_OPENINGS_EXPANDED_20261019.json'],cwd=ROOT,check=True)
    subprocess.run([sys.executable,'tools/report_expanded_openings.py'],cwd=ROOT,check=True)
    (ROOT/'docs/training/BLOODRUN_300_ANALYSIS_INDEX_20261019.json').write_bytes(INDEX.read_bytes())
    print('EXPANDED OPENING REPORT COMPLETE',flush=True)

if __name__=='__main__':main()
