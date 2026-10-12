"""Cycle learned jump probes on the isolated 27961 lab and preserve evidence."""
import json
import re
import socket
import time
from pathlib import Path

HOME = Path('/home/qlserver/psyz0r-test-server-home')
LOG = HOME / 'console.log'
OUT = Path('/home/qlserver/psyz0r-bot/jump-probes-072')


def command(value):
    with socket.socket(socket.AF_UNIX) as connection:
        connection.settimeout(3)
        connection.connect(str(HOME / 'console.sock'))
        connection.sendall((value + '\n').encode())
        connection.recv(1024)


def status_without_human():
    offset = LOG.stat().st_size
    command('status')
    time.sleep(.5)
    data = LOG.read_bytes()[offset:].decode(errors='replace')
    players = [line for line in data.splitlines()
               if re.match(r'^\s*\d+\s+-?\d+\s+\d+\s+', line)]
    if not players or any(' bot ' not in f' {line} ' for line in players):
        raise RuntimeError('human connected or status unavailable')


def main():
    OUT.mkdir(exist_ok=True)
    start = LOG.stat().st_size
    results = []
    try:
        for probe in range(2, 18):
            status_without_human()
            command(f'set qlx_psyzRJProbe {probe}')
            begin = LOG.stat().st_size
            for _ in range(4):
                time.sleep(5)
                status_without_human()
            text = LOG.read_bytes()[begin:].decode(errors='replace')
            sample = probe - 1
            results.append(dict(probe=probe, sample=sample,
                begins=len(re.findall(fr'PSYZ_RJ_BEGIN[^\n]*sample={sample}(?:\s|$)', text)),
                successes=len(re.findall(fr'PSYZ_RJ_END[^\n]*sample={sample}[^\n]*(?:higher=1|pickup=1)', text)),
                endings=len(re.findall(fr'PSYZ_RJ_END[^\n]*sample={sample}(?:\s|$)', text))))
            (OUT / 'progress.json').write_text(json.dumps(results, indent=2))
    finally:
        command('set qlx_psyzRJProbe 0')
        (OUT / 'sweep.log').write_bytes(LOG.read_bytes()[start:])
    (OUT / 'complete.json').write_text(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
