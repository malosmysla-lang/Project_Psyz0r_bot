"""Use the detailed generated orb as the sidebar brand icon."""
from pathlib import Path
import re
p=Path(__file__).resolve().parents[1]/'Аналитика разработки бота/index.html'
s=p.read_text(encoding='utf-8')
s=re.sub(r'<span class="sigil eye-mark">.*?</span>', '<span class="sigil eye-mark"><img src="assets/mechanical-eye-orb.png" width="40" height="40" alt="" aria-hidden="true"></span>',s,count=1,flags=re.S)
p.write_text(s,encoding='utf-8')
