"""Read-only state by default; optional one-line diagnostic tests the loaded chat."""
import argparse,hashlib,json,re,shutil,socket,subprocess,time
from pathlib import Path
STAGE=Path(__file__).resolve().parent;HOME=Path('/home/qlserver/psyz0r-test-server-home')
def command(text):
    log=HOME/'console.log';offset=log.stat().st_size
    with socket.socket(socket.AF_UNIX) as s:
        s.settimeout(3);s.connect(str(HOME/'console.sock'));s.sendall((text+'\n').encode());s.recv(4096)
    time.sleep(.4)
    with log.open('rb') as f:f.seek(offset);return f.read().decode(errors='replace')
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--test-chat',action='store_true');a=ap.parse_args()
    text=command('net_port')
    if '27961' not in text:raise RuntimeError('Cannot verify isolated console')
    if a.test_chat:
        prefix_text=command('qlx_commandPrefix')
        match=re.search(r'is:"([^"]+)"',prefix_text)
        if not match:raise RuntimeError('Cannot verify minqlx command prefix')
        prefix=re.sub(r'\^[0-9]','',match[1])
        # Этот runtime загружает только psyz_chat: команды !reload здесь нет.
        # Не подменяем работающий модуль на диске под видом горячей загрузки.
        result=command('qlx '+prefix+'psychat')
        if 'Chat online' not in result:raise RuntimeError('No chat diagnostic output: '+result)
        print('CHAT_DIAGNOSTIC_OK',result)
    print(command('status'));print(command('g_gameState'));print(command('qlx_psyzVersion'))
if __name__=='__main__':main()
