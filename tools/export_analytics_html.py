"""Self-contained local HTML export; JS/CSS and preview images are embedded."""
import base64,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];SITE=ROOT/'Аналитика разработки бота'
def main():
    html=(SITE/'index.html').read_text(encoding='utf-8')
    def style(m):
        return '<style>'+ (SITE/m[1]).read_text(encoding='utf-8')+'</style>'
    html=re.sub(r'<link rel="stylesheet" href="([^"]+)">',style,html)
    def script(m):
        text=(SITE/m[1]).read_text(encoding='utf-8').replace('</script','<\\/script')
        return '<script>'+text+'</script>'
    html=re.sub(r'<script src="([^"]+)"></script>',script,html)
    def picture(m):
        p=(SITE/m[1]).resolve()
        if p.exists() and p.suffix.lower()=='.png':
            return 'src="data:image/png;base64,'+base64.b64encode(p.read_bytes()).decode()+'"'
        return m[0]
    html=re.sub(r'src="([^"]+\.png)"',picture,html)
    output=SITE/'Psyz0r_Analytics_0_7_8.html';output.write_text(html,encoding='utf-8')
    assert '<script src=' not in html and '<link rel="stylesheet"' not in html
    print('Standalone HTML:',output.name,output.stat().st_size,'bytes')
if __name__=='__main__':main()
