"""Add an explicit practice-server connection block to the existing right header card."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];p=ROOT/'Аналитика разработки бота/index.html'
s=p.read_text(encoding='utf-8')
block='''<div class="server-connect"><div class="connect-topline"><span>ИГРАТЬ С БОТОМ</span><span class="led" aria-hidden="true"></span></div><code id="serverConnectCommand">connect 78.17.9.235:27961</code><button type="button" id="copyServerConnect" class="btn btn-outline-info">Скопировать коннект</button><p id="connectCopyStatus" role="status" aria-live="polite">Вставь команду в консоль Quake Live.</p><p class="connect-note">Играйте и помогайте улучшать бота. Сбор статистики включён; автоматическое обучение пока не реализовано.</p></div>'''
if 'id="serverConnectCommand"' not in s:s=s.replace('<div class="release">','<div class="release">'+block,1)
if 'src="server-connect.js"' not in s:s=s.replace('</body>','<script src="server-connect.js"></script></body>')
p.write_text(s,encoding='utf-8')
