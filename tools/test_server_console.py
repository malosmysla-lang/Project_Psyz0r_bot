"""Linux isolated QL test runner: PTY stdin and owner-only UNIX console socket.

Run on the test host. No credentials, no changes to the primary service.
"""
import argparse
import hashlib
import zipfile
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
    parser.add_argument('--factory', choices=('ffa','duel'), default='duel')
    parser.add_argument('--preload', type=Path)
    parser.add_argument('--stock-goal-observer', action='store_true')
    args = parser.parse_args()
    if args.stock_goal_observer:
        engine=args.base/'qzeroded.x64'
        if hashlib.sha256(engine.read_bytes()).hexdigest()!='6fd0e87811facfd81ea34e10e2f6c486e7d4951dcab3cb2fa7f48dcb164c7b2e':
            parser.error('Pinned QL engine mismatch')
        with zipfile.ZipFile(args.base/'baseq3/bin.pk3') as archive:
            binary=archive.read('qagamex64.so')
        if hashlib.sha256(binary).hexdigest()!='091d568f46a280afbf2deda4a5ba4c8bd5e02ed6d070ef56300b1f47c5f729be':
            parser.error('Pinned qagame mismatch')
    home = args.home.resolve()
    home.mkdir(parents=True, exist_ok=True)
    console_path = home / 'console.sock'
    if console_path.exists():
        raise RuntimeError('Console socket already exists; inspect existing instance')
    master, slave = pty.openpty()
    tty.setraw(slave)
    environment = dict(os.environ)
    environment['LD_LIBRARY_PATH'] = str(args.base / 'linux64')
    environment['LD_PRELOAD'] = str(args.preload.resolve() if args.preload else args.base / 'minqlx.x64.so')
    if args.stock_goal_observer:
        environment['PSYZ_CONTROL_LAB'] = '1'
        environment['PSYZ_STOCK_GOAL_OBSERVER'] = '1'
    commands = [str(args.base / 'qzeroded.x64'), '+set', 'fs_basepath', str(args.base),
                '+set', 'fs_homepath', str(home), '+set', 'net_ip', args.listen,
                '+set', 'net_strict', '1', '+set', 'net_port', '27961',
                '+set', 'zmq_stats_enable', '1',
                '+set', 'com_hunkMegs', '192', '+exec', 'psyz_test.cfg',
                '+map', 'bloodrun', args.factory]
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
                            try:
                                connection.sendall(b'written to test console; execution not verified\n')
                            except (BrokenPipeError, ConnectionResetError):
                                pass  # A disconnected console client must not stop the server.
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
