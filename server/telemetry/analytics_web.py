"""Read-only static dashboard and sanitized live match endpoint. No game commands."""
import argparse,json,socket,time,threading,datetime
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit,unquote

_status_lock=threading.Lock()
_status_cache=(0,None)
def server_status():
    """Actual QL UDP reply; no RCON, secrets or game commands."""
    global _status_cache
    with _status_lock:
        if time.monotonic()-_status_cache[0]<5:return _status_cache[1]
        status=dict(online=False,checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
        try:
            with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as sock:
                sock.settimeout(.7);sock.sendto(b'\xff\xff\xff\xffgetinfo praccsite',('127.0.0.1',27961))
                data,_=sock.recvfrom(8192)
            if data.startswith(b'\xff\xff\xff\xffinfoResponse\n'):
                parts=data.decode(errors='replace').split('\n',1)[1].strip().split('\\')
                fields=dict(zip(parts[1::2],parts[2::2]))
                if fields.get('challenge')=='praccsite':
                    status.update(online=True,map=fields.get('mapname'),clients=fields.get('clients'),source='udp')
        except (OSError,ValueError):pass
        # Quake Live can suppress getinfo replies locally. The owner-only UNIX
        # console socket proves that the isolated engine runner is alive without
        # sending RCON, changing a cvar, or exposing any command externally.
        if not status['online']:
            try:
                with socket.socket(socket.AF_UNIX) as console:
                    console.settimeout(.7)
                    console.connect('/home/qlserver/psyz0r-test-server-home/console.sock')
                    console.sendall(b'status\n')
                    if console.recv(256):
                        status.update(online=True,source='test_console_socket')
            except OSError:pass
        _status_cache=(time.monotonic(),status);return status

def merged(seed,live):
    rows={r['id']:r for r in seed.get('matches',[])}
    for row in live.get('matches',[]):
        if str(row.get('id','')).startswith('live:') and row.get('bot',{}).get('is_psyz'):
            rows[row['id']]=dict(row,actor='Psyz0r')
    return dict(seed,matches=list(rows.values()),automatic_learning=False,learning_status='not_proven_manual_policy_updates')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);ap.add_argument('--live',required=True);ap.add_argument('--port',type=int,default=80);args=ap.parse_args()
    root=Path(args.root).resolve();live=Path(args.live)
    class Handler(SimpleHTTPRequestHandler):
        def __init__(self,*a,**kw):super().__init__(*a,directory=str(root),**kw)
        def log_message(self,*a):pass
        def list_directory(self,path):self.send_error(404);return None
        def end_headers(self):
            self.send_header('X-Content-Type-Options','nosniff');self.send_header('Referrer-Policy','strict-origin-when-cross-origin');super().end_headers()
        def do_GET(self):
            path=unquote(urlsplit(self.path).path)
            if any(part.startswith('.') or part=='..' for part in path.split('/') if part):self.send_error(404);return
            if path.endswith(('.py','.service','.tar.gz')):self.send_error(404);return
            # Site-project exports were withdrawn by the owner. Bot-only ZIPs allowed.
            if 'Pracc_Room_Server_BOT' in path or 'Analytics_' in path or 'Поделиться' in path:
                self.send_error(404);return
            if path=='/api/server-status.json':
                payload=json.dumps(server_status()).encode()
                self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(payload)));self.end_headers();self.wfile.write(payload);return
            if path=='/api/matches.json':
                try:
                    seed=json.loads((root/'match-ledger-seed.json').read_text(encoding='utf-8'))
                    current=json.loads(live.read_text(encoding='utf-8')) if live.exists() else {'matches':[]}
                    payload=json.dumps(merged(seed,current),ensure_ascii=False).encode()
                except (ValueError,OSError):self.send_error(503);return
                self.send_response(200);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(payload)));self.end_headers();self.wfile.write(payload);return
            return super().do_GET()
    ThreadingHTTPServer(('0.0.0.0',args.port),Handler).serve_forever()
if __name__=='__main__':main()
