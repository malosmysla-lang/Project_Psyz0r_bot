"""Keep blink and page reload as separate, valid interactive controls."""
from pathlib import Path
import re
p=Path(__file__).resolve().parents[1]/'Аналитика разработки бота/index.html'
s=p.read_text(encoding='utf-8')
brand='<div class="brand"><button class="sigil eye-mark" type="button" aria-label="Моргнуть глазом"><img src="assets/mechanical-eye-orb.png" width="80" height="80" alt="" aria-hidden="true"></button><a id="brandHome" class="brand-home" href="#overview">Pracc Room<br>Server <b class="bot-word">BOT</b></a></div>'
s=re.sub(r'<a class="brand" href="#overview">.*?</a>',lambda _:brand,s,count=1,flags=re.S)
p.write_text(s,encoding='utf-8')
