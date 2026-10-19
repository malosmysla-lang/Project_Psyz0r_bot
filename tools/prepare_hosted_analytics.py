"""Keep initial hosted HTML light; move portable attachments to static downloads."""
import base64,hashlib,json,mimetypes,re,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];SITE=ROOT/'Аналитика разработки бота'
HOST=ROOT/'out/sites-pracc'
def main():
    manifest=HOST/'.openai/hosting.json'
    config=json.loads(manifest.read_text(encoding='utf-8'))
    config['static']={'directory':'dist'};config['d1']=None;config['r2']=None
    manifest.write_text(json.dumps(config,indent=2),encoding='utf-8')
    dist=HOST/'dist';downloads=dist/'downloads';downloads.mkdir(parents=True,exist_ok=True)
    portable=SITE/'Поделиться/Pracc_Room_Server_BOT.html'
    html=portable.read_text(encoding='utf-8');assets={}
    def extract(m):
        mime=m[1];raw=base64.b64decode(m[2]);digest=hashlib.sha256(raw).hexdigest()
        ext=mimetypes.guess_extension(mime) or '.bin'
        if ext=='.jpe':ext='.jpg'
        filename=digest[:20]+ext
        (downloads/filename).write_bytes(raw);assets[filename]=len(raw)
        return 'downloads/'+filename
    html=re.sub(r'data:([\w.+/-]+);base64,([A-Za-z0-9+/=]+)',extract,html)
    for stale in downloads.iterdir():
        if stale.is_file() and stale.name not in assets:stale.unlink()
    html=html.replace('</header>','<p class="share-downloads"><a class="btn btn-outline-info" href="Pracc_Room_Server_BOT.html" download>Скачать автономный HTML</a> <a class="btn btn-outline-info" href="Pracc_Room_Server_BOT_0_7_9.zip" download>ZIP для пересылки · около 5 МБ</a></p></header>',1)
    (dist/'index.html').write_text(html,encoding='utf-8')
    shutil.copy2(portable,dist/portable.name)
    shutil.copy2(ROOT/'out/share/Pracc_Room_Server_BOT_0_7_9.zip',dist/'Pracc_Room_Server_BOT_0_7_9.zip')
    (HOST/'README.md').write_text('Pracc Room Server BOT. Static analytics demo, no game-server control, credentials or database. Source generated from the local Project_Psyz0r_bot evidence.\n',encoding='utf-8')
    (HOST/'.gitignore').write_text('.sites-runtime/\n*.tar.gz\n',encoding='utf-8')
    assert not re.search(r'<script\b[^>]*src=',html)
    assert (dist/'index.html').stat().st_size<2*1024*1024
    print(json.dumps(dict(initial_html_bytes=(dist/'index.html').stat().st_size,attachments=len(assets),static_directory='dist')))
if __name__=='__main__':main()
