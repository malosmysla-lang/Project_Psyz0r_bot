"""Deploy the independently gated 0.8.7 finisher to an empty 27961 only."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import socket
import subprocess
import time

BASE = Path('/home/qlserver')
HOME = BASE / 'psyz0r-test-server-home'
STAGE = BASE / 'psyz0r-bot/iteration-087-20261021'


def run(*args):
    return subprocess.check_output(args, text=True).strip()


def command(text):
    log = HOME / 'console.log'
    offset = log.stat().st_size
    with socket.socket(socket.AF_UNIX) as c:
        c.settimeout(2)
        c.connect(str(HOME / 'console.sock'))
        c.sendall(text.encode() + b'\n')
        c.recv(256)
    time.sleep(.5)
    with log.open('rb') as source:
        source.seek(offset)
        return source.read(65536).decode(errors='replace')


def guard():
    status = command('status')
    assert 'map:' in status and 'steamid' in status, 'Cannot verify current roster'
    for line in status.splitlines():
        parts = line.split()
        if len(parts) >= 7 and parts[0].isdigit() and parts[1].lstrip('-').isdigit():
            assert 'bot' in parts, 'Human connected; defer the test deployment'


def main():
    guard()
    primary = run('systemctl', 'show', 'quakelive', '-p', 'MainPID', '--value')
    native = BASE / 'psyz0r-test-server/psyz_test/minqlx_nopy.so'
    cfg = HOME / 'baseq3/psyz_test.cfg'
    backup = BASE / 'backups' / time.strftime('psyz-test087-%Y%m%dT%H%M%SZ', time.gmtime())
    backup.mkdir()
    shutil.copy2(native, backup / native.name)
    shutil.copy2(cfg, backup / cfg.name)
    values = {'qlx_psyzVersion': '0.8.7', 'qlx_psyzFinish087': '1',
              'qlx_psyzPreAlpha': '0', 'qlx_psyzComboLive': '0',
              'qlx_psyzMovementReplay': '0', 'qlx_psyzMovementProbe': '0',
              'bot_nochat': '1', 'bot_minplayers': '0', 'developer': '0'}
    text = cfg.read_text()
    for key, value in values.items():
        text = re.sub(r'^\s*set[as]?\s+' + re.escape(key) + r'\s+.*\n?', '', text, flags=re.M)
        text += '\nset {} "{}"\n'.format(key, value)
    guard()
    command('quit')
    run('sudo', '-n', 'systemctl', 'stop', 'psyz0r-test')
    try:
        shutil.copy2(BASE / 'psyz0r-bot/build-087-20261021/bin/minqlx.x64.so', native)
        cfg.write_text(text)
        (HOME / 'console.sock').unlink(missing_ok=True)
        run('sudo', '-n', 'systemctl', 'start', 'psyz0r-test')
        status = ''
        for attempt in range(24):
            time.sleep(5)
            assert run('systemctl', 'is-active', 'psyz0r-test') == 'active'
            status = command('status')
            if 'Psyz0r_bot' in status and 'bot' in status:
                break
        else:
            raise RuntimeError('Test bot did not become ready within 120 seconds')
        assert run('systemctl', 'show', 'quakelive', '-p', 'MainPID', '--value') == primary
    except Exception:
        run('sudo', '-n', 'systemctl', 'stop', 'psyz0r-test')
        shutil.copy2(backup / native.name, native)
        shutil.copy2(backup / cfg.name, cfg)
        (HOME / 'console.sock').unlink(missing_ok=True)
        run('sudo', '-n', 'systemctl', 'start', 'psyz0r-test')
        raise
    result = dict(version='0.8.7', backup=str(backup), primary_pid=primary,
        test_pid=run('systemctl', 'show', 'psyz0r-test', '-p', 'MainPID', '--value'),
        native_sha256=hashlib.sha256(native.read_bytes()).hexdigest(),
        independent_finisher=True, legacy_navigation=False, roster=status)
    (STAGE / 'deployment087-test.json').write_text(json.dumps(result, indent=2))
    print(json.dumps({k:v for k,v in result.items() if k != 'roster'}))


if __name__ == '__main__':
    main()
