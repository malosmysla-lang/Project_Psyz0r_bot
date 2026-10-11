"""Restart only the explicitly isolated prealpha instance, never primary QL."""
from pathlib import Path
import socket,subprocess,time
lab=Path('/home/qlserver/psyz0r-bot/prealpha-20261011');home=lab/'home'
def command(text):
    with socket.socket(socket.AF_UNIX) as s:
        s.settimeout(3);s.connect(str(home/'console.sock'));s.sendall(text.encode()+b'\n');s.recv(1024)
if (home/'console.sock').exists():
    pid=int((home/'server.pid').read_text())
    cmd=Path('/proc/'+str(pid)+'/cmdline').read_bytes()
    if str(home).encode() not in cmd or b'27961' not in cmd:
        raise RuntimeError('Refusing to stop a process outside isolated home/port')
    command('quit')
    for _ in range(50):
        if not Path('/proc/'+str(pid)).exists() and not (home/'console.sock').exists():break
        time.sleep(.1)
    if Path('/proc/'+str(pid)).exists():raise RuntimeError('Test instance did not stop')
log=open(lab/'runner.log','ab')
subprocess.Popen(['python3',str(lab/'runner.py'),'--base','/home/qlserver/server','--home',str(home),'--listen','0.0.0.0','--preload',str(lab/'minqlx/bin/minqlx_nopy.so'),'--stock-goal-observer'],stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=True)
time.sleep(5)
command('addbot Xaero 5 free 0 Psyz0r_bot')
time.sleep(2)
print((home/'console.log').read_text(errors='replace')[-8500:])
