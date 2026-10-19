"""One centered connect control; hover swaps its label without changing copied text."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
old='<code id="serverConnectCommand">connect 78.17.9.235:27961</code><button type="button" id="copyServerConnect" class="btn btn-outline-info">Скопировать коннект</button>'
new='<button type="button" id="copyServerConnect" class="connect-copy-control" aria-label="Скопировать Connect: connect 78.17.9.235:27961"><code id="serverConnectCommand">connect 78.17.9.235:27961</code><span class="connect-copy-label" aria-hidden="true">Скопировать Connect</span></button>'
for p in (ROOT/'Аналитика разработки бота/index.html',ROOT/'tools/add_header_connect.py'):
    s=p.read_text(encoding='utf-8');assert old in s,p
    p.write_text(s.replace(old,new),encoding='utf-8')
