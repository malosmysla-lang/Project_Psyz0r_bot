"""Linux isolated QL test runner: PTY stdin and owner-only UNIX console socket.

Run on the test host. No credentials, no changes to the primary service.
"""
import argparse
import os
from pathlib import Path
import pty
import select
import signal
import socket
import subprocess
import tty

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base', required=True, type=Path)
    parser.add_argument('--home', required=True, type=Path)
    parser.add_argument('--listen', default='127.0.0.1')
    args = parser.parse_args()
    home = args.home.resolve()
    home.mkdir(parents=True, exist_ok=True)
    console_path = home / 'console.sock'
    if console_path.exists():
        raise RuntimeError('Console socket already exists; inspect existing instance')
    master, slave = pty.openpty()
    tty.setraw(slave)
    environment = dict(os.environ)
    environment['LD_LIBRARY_PATH'] = str(args.base / 'linux64')
    environment['LD_PRELOAD'] = str(args.base / 'minqlx.x64.so')
    commands = [str(args.base / 'qzeroded.x64'), '+set', 'fs_basepath', str(args.base),
                '+set', 'fs_homepath', str(home), '+set', 'net_ip', args.listen,
                '+set', 'net_strict', '1', '+set', 'net_port', '27961',
                '+set', 'com_hunkMegs', '192', '+exec', 'psyz_test.cfg',
                '+map', 'bloodrun', 'ffa']
    with (home / 'console.log').open('ab', buffering=0) as log:
        process = subprocess.Popen(commands, cwd=args.base, env=environment,
                                   stdin=slave, stdout=slave, stderr=subprocess.STDOUT,
                                   start_new_session=True)
        os.close(slave)
        (home / 'server.pid').write_text(str(process.pid))
        server = socket.socket(socket.AF_UNIX)
        server.bind(str(console_path))
        os.chmod(console_path, 0o600)
        server.listen(2)
        signal.signal(signal.SIGTERM, lambda *_: process.terminate())
        try:
            while process.poll() is None:
                ready, _, _ = select.select([server, master], [], [], 0.25)
                if master in ready:
                    try:
                        data = os.read(master, 65536)
                    except OSError:
                        break
                    if data:
                        log.write(data)
                if server in ready:
                    connection, _ = server.accept()
                    with connection:
                        connection.settimeout(2)
                        data = connection.recv(4096)
                        if data and len(data) < 4096:
                            os.write(master, data.rstrip(b'\r\n') + b'\n')
                            connection.sendall(b'written to test console; execution not verified\n')
        finally:
            server.close()
            console_path.unlink(missing_ok=True)
            os.close(master)
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
    return process.returncode

if __name__ == '__main__':
    raise SystemExit(main())
