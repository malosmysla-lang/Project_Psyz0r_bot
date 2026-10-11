"""Run only on the isolated Linux lab; stop trials if a human connects."""
import argparse
import hashlib
import json
import socket
import time
from pathlib import Path

LAB = Path('/home/qlserver/psyz0r-bot/prealpha-20261011')
HOME = LAB/'home'
LOG = HOME/'console.log'


def command(text):
    with socket.socket(socket.AF_UNIX) as s:
        s.settimeout(3)
        s.connect(str(HOME/'console.sock'))
        s.sendall(text.encode()+b'\n')
        s.recv(1024)


def guard():
    pid = int((HOME/'server.pid').read_text())
    cmd = Path(f'/proc/{pid}/cmdline').read_bytes()
    if str(HOME).encode() not in cmd or b'27961' not in cmd:
        raise RuntimeError('Not the isolated server')
    offset = LOG.stat().st_size
    command('status')
    time.sleep(.4)
    with LOG.open('rb') as f:
        f.seek(offset)
        status = f.read().decode(errors='replace')
    if 'map:' not in status:
        raise RuntimeError('No status response')
    for line in status.splitlines():
        p = line.split()
        if len(p) >= 9 and p[0].isdigit() and p[1].lstrip('-').isdigit() and p[2].isdigit():
            if p[-4] != 'bot':
                raise RuntimeError('Human connected; no further trial mutations')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', required=True, type=Path)
    args = ap.parse_args()
    args.output.mkdir(exist_ok=False)
    results = []
    trials = [('duel_1', 0, 40), ('duel_2', 0, 40), ('duel_3', 0, 40),
              ('rocketjump_1', 1, 30), ('rocketjump_2_experimental', 2, 30)]
    try:
        for name, probe, duration in trials:
            guard()
            offset = LOG.stat().st_size
            command('set qlx_psyzRJProbe 0')
            command('kick Trial_baseline')
            command('map bloodrun duel')
            time.sleep(2)
            guard()
            command('set nextmap "map bloodrun duel"')
            if probe:
                command(f'set qlx_psyzRJProbe {probe}')
            else:
                command('addbot Sarge 1 free 0 Trial_baseline')
                command('allready')
            print('TRIAL_STARTED', name, flush=True)
            for _ in range(duration//5):
                time.sleep(5)
                guard()
            with LOG.open('rb') as f:
                f.seek(offset)
                data = f.read()
            (args.output/(name+'.log')).write_bytes(data)
            record = dict(name=name, seconds=duration, probe=probe,
                          log_sha256=hashlib.sha256(data).hexdigest())
            results.append(record)
            (args.output/'manifest.json').write_text(json.dumps(results, indent=2))
            print('TRIAL_FINISHED', name, len(data), flush=True)
    finally:
        # Disable experimental forced actions even if a player arrived.
        command('set qlx_psyzRJProbe 0')
    guard()
    command('kick Trial_baseline')
    command('map bloodrun duel')
    time.sleep(2)
    command('set nextmap "map bloodrun duel"')
    command('status')
    print('READY_FOR_OWNER BloodRun probe=0', flush=True)


if __name__ == '__main__':
    main()
