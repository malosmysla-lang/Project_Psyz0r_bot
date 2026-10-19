"""Read-only static dashboard and sanitized live match endpoint. No game commands."""
import argparse,json
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit,unquote

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
