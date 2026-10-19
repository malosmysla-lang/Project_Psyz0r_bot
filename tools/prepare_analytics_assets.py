"""Fetch pinned, local-only UI assets and the official offline demo CLI."""
import hashlib,json,urllib.request,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'Аналитика разработки бота';VENDOR=OUT/'vendor'
def fetch(url):
    with urllib.request.urlopen(url,timeout=60) as f:return f.read()
def main():
    VENDOR.mkdir(parents=True,exist_ok=True)
    version='1.6.1'  # Pinned release selected during this implementation.
    rows=[]
    for name,url in [
        ('tabler.min.css',f'https://cdn.jsdelivr.net/npm/@tabler/core@{version}/dist/css/tabler.min.css'),
        ('TABLER_LICENSE.txt','https://raw.githubusercontent.com/tabler/tabler/dev/LICENSE')]:
        data=fetch(url);(VENDOR/name).write_bytes(data);rows.append({'file':name,'url':url,'sha256':hashlib.sha256(data).hexdigest()})
    (VENDOR/'manifest.json').write_text(json.dumps({'tabler_version':version,'assets':rows},indent=2),encoding='utf-8')
    print('Tabler assets pinned:',version,flush=True)
    # The source project's distribution server also hosts the console package.
    url='https://myt.playmorepromode.com/udt/udt_con_1.3.1_x64.zip'
    try:
        data=fetch(url);path=ROOT/'out/recovery-analytics/udt_con_1.3.1_x64.zip';path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
        with zipfile.ZipFile(path) as z:
            for name in z.namelist():
                p=Path(name)
                if p.name.startswith('UDT_') and p.suffix.lower()=='.exe':(ROOT/'tools/udt/bin'/p.name).write_bytes(z.read(name))
        (path.parent/'udt_cli_source.json').write_text(json.dumps({'url':url,'sha256':hashlib.sha256(data).hexdigest()}),encoding='utf-8')
        print('Official UDT CLI restored',flush=True)
    except Exception as e:print('UDT CLI unavailable:',str(e),flush=True)
if __name__=='__main__':main()
