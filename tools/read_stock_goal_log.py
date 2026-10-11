"""Decode read-only diagnostic goal records; inferred layout is never executable."""
import argparse
import json
import math
from pathlib import Path
import re
import struct
PATTERN=re.compile(r'PSYZ_STOCK_GOAL sequence=(\d+) state=(\S+) travel_flags=(-?\d+) result=(-?\d+) prefix48=([0-9a-f]{96}) source=stock_ltg layout=unverified(?:\s|$)')

def parse_log(text):
    records=[]
    for m in PATTERN.finditer(text):
        raw=bytes.fromhex(m[5])
        origin=struct.unpack_from('<3f',raw)
        plausible=all(math.isfinite(v) and abs(v)<1_000_000 for v in origin)
        records.append(dict(sequence=int(m[1]),state_token=m[2],travel_flags=int(m[3]),
           result=int(m[4]),raw_prefix_hex=m[5],
           candidate_origin=list(origin) if plausible else None,
           candidate_area=struct.unpack_from('<i',raw,12)[0],
           layout_verified=False,ready_for_execution=False,
           semantics='Q3-compatible prefix hypothesis; state token is not a verified client identity'))
    return records

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    records=parse_log(a.log.read_text(encoding='utf-8',errors='replace'))
    a.output.write_text(json.dumps(dict(records=records,layout_verified=False),indent=2),encoding='utf-8')
    print('Decoded diagnostic records:',len(records),'layout remains unverified')
