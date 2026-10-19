"""Apply the owner-approved mechanical eye and remove the obsolete draft silhouette."""
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/'Аналитика разработки бота'
eye='''<span class="sigil eye-mark"><svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"><defs><radialGradient id="eye-iris"><stop stop-color="#080f24"/><stop offset=".38" stop-color="#101326"/><stop offset=".42" stop-color="#dbfaff"/><stop offset=".55" stop-color="#42e8dc"/><stop offset=".82" stop-color="#218ba5"/><stop offset="1" stop-color="#b18aff"/></radialGradient><linearGradient id="eye-steel" x2="1" y2="1"><stop stop-color="#e0edf5"/><stop offset=".3" stop-color="#68758a"/><stop offset=".6" stop-color="#151d30"/><stop offset="1" stop-color="#8996ae"/></linearGradient></defs><path d="M9 23l-4-5 5-7 7 2M49 13l7-2 5 7-5 6M8 43l-3 5 7 6 7-4M47 51l7 3 6-7-4-5" stroke="#74819a" stroke-width="3"/><circle cx="32" cy="32" r="26" fill="#111a2a" stroke="url(#eye-steel)" stroke-width="5"/><circle cx="32" cy="32" r="21" fill="#dbeaf1" stroke="#273647" stroke-width="2"/><circle cx="32" cy="32" r="15" fill="url(#eye-iris)"/>
'''
# Fine radial iris fibers remain visible in the large source and resolve into texture at icon size.
import math
for i in range(32):
    a=i*math.tau/32
    eye+=f'<path d="M{32+9*math.cos(a):.2f} {32+9*math.sin(a):.2f}L{32+14*math.cos(a):.2f} {32+14*math.sin(a):.2f}" stroke="{["#adf9ff","#38437a","#8976ca"][i%3]}" stroke-width=".6"/>'
eye+='''<ellipse cx="32" cy="32" rx="6" ry="10" fill="#040b15"/><ellipse cx="28" cy="25" rx="3" ry="6" fill="#fff" transform="rotate(22 28 25)"/><circle cx="36" cy="39" r="2" fill="#dffaff"/><path d="M11 23a24 24 0 0 1 39-9M15 52a24 24 0 0 0 36-10" stroke="#42e8dc" stroke-width="2"/><circle cx="12" cy="19" r="2" fill="#b18aff"/><circle cx="52" cy="45" r="2" fill="#42e8dc"/></svg></span>'''
p=SITE/'index.html';s=p.read_text(encoding='utf-8')
s=re.sub(r'<span class="sigil(?: eye-mark)?">.*?</svg></span>',lambda _:eye,s,count=1,flags=re.S)
p.write_text(s,encoding='utf-8')
p=SITE/'bot-mascot.js';s=p.read_text(encoding='utf-8')
s=re.sub(r'  bot.innerHTML = `<svg.*?</svg>`;\n','',s,flags=re.S)
p.write_text(s,encoding='utf-8')
print('Mechanical eye applied; placeholder silhouette removed')
