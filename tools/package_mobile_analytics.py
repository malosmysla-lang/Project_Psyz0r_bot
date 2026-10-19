"""Portable HTML + optional ZIP. No Android SDK, installation or network needed."""
import base64,hashlib,json,mimetypes,re,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];SITE=ROOT/'Аналитика разработки бота'
OUT=ROOT/'out/share'
def main():
    data=json.loads((SITE/'data.json').read_text(encoding='utf-8'))
    portable=dict(data)
    # Shared UI needs the release, not admin backup paths or raw console output.
    portable['deployment']={'version':data.get('deployment',{}).get('version','0.7.9')}
    if 'trial079' in portable:
        portable['trial079']={k:v for k,v in portable['trial079'].items() if k not in ('scores','ready_status')}
    html=(SITE/'Pracc_Room_Server_Analytics.html').read_text(encoding='utf-8')
    original='window.PSYZ_ANALYTICS = '+json.dumps(data,ensure_ascii=False)+';\n'
    assert original in html
    html=html.replace(original,'window.PSYZ_ANALYTICS = '+json.dumps(portable,ensure_ascii=False)+';\n',1)
    # Local documentation links become downloadable embedded attachments.
    # Only existing explicit links inside the project can be packaged.
    embedded={}
    def embed(path):
        if path not in embedded:
            mime=mimetypes.guess_type(path.name)[0] or 'application/octet-stream'
            embedded[path]='data:'+mime+';base64,'+base64.b64encode(path.read_bytes()).decode()
        return embedded[path]
    modules={}
    for module in data['modules']:
        path=(ROOT/module['source']).resolve()
        if not path.is_relative_to(ROOT) or not path.is_file():raise ValueError('Unsafe module source')
        modules[module['source']]=embed(path)
    html=html.replace('href="../${encodeURI(x.source)}"','href="${window.PSYZ_ATTACHMENTS[x.source]}" download')
    def attachment(m):
        href=m[1]
        if href=='${window.PSYZ_ATTACHMENTS[x.source]}':return m[0]
        if href.startswith(('#','http:','https:','data:','mailto:')):return m[0]
        path=(SITE/href).resolve()
        if not path.is_relative_to(ROOT) or not path.is_file():raise ValueError('Missing/unsafe portable link: '+href)
        if path.stat().st_size>12*1024*1024:raise ValueError('Unexpectedly large attachment: '+path.name)
        return 'href="'+embed(path)+'" download="'+path.name+'"'
    html=re.sub(r'href="([^"]+)"',attachment,html)
    html=html.replace('<script>','<script>window.PSYZ_ATTACHMENTS = '+json.dumps(modules,ensure_ascii=False)+';</script><script>',1)
    assert not re.search(r'<script\b[^>]*\bsrc=',html)
    assert not re.search(r'<link\b[^>]*rel="stylesheet"',html)
    for src in re.findall(r'\bsrc="([^"]+)"',html):
        assert src.startswith('data:'),src
    # Keep the third-party CSS license with this self-contained distribution.
    license_path=SITE/'vendor/LICENSE'
    if not license_path.exists():
        choices=list((SITE/'vendor').glob('*LICENSE*'))
        license_path=choices[0] if choices else None
    license_text=license_path.read_text(encoding='utf-8') if license_path else ''
    own_license=(ROOT/'LICENSE').read_text(encoding='utf-8')
    html=html.replace('</body>','<footer class="bottom" style="margin:20px">Автономное демо · данные встроены · исходники по ссылкам скачиваются как вложения. Без связи с игровым сервером.</footer></body>')
    if license_text:html+='\n<!-- Tabler license\n'+license_text.replace('--','—')+'\n-->\n'
    html+='\n<!-- Project license\n'+own_license.replace('--','—')+'\n-->\n'
    share=SITE/'Поделиться';share.mkdir(exist_ok=True)
    target=share/'Pracc_Room_Server_BOT.html';target.write_text(html,encoding='utf-8')
    instructions='''Pracc Room Server BOT — автономное демо 0.7.9

Откройте Pracc_Room_Server_BOT.html в браузере Chrome/Firefox на Android
или в браузере компьютера. Интернет и установка APK не требуются.
Если мессенджер показывает только текст или предпросмотр: сохраните файл
на телефон и выберите «Открыть с помощью» → браузер. Просмотрщик файлов
может не исполнять JavaScript; в таком случае используйте браузер.

Анимации, таблицы, фильтры, гистограммы и переключатель четырёх версий
встроены в HTML. JSON — отдельная выгрузка данных, не приложение.
Ссылки на исходные документы скачивают встроенные вложения.
Данные — снимок, автоматической связи с сервером нет.
Для самой простой пересылки достаточно одного HTML-файла.
Android-устройство в этом этапе физически не проверялось.
'''
    (share/'README.txt').write_text(instructions,encoding='utf-8')
    OUT.mkdir(parents=True,exist_ok=True)
    package=OUT/'Pracc_Room_Server_BOT_0_7_9.zip'
    with zipfile.ZipFile(package,'w',zipfile.ZIP_DEFLATED) as z:
        z.write(target,target.name);z.writestr('README.txt',instructions)
        z.writestr('analytics.json',json.dumps(portable,ensure_ascii=False,indent=2))
        if license_text:z.writestr('TABLER_LICENSE.txt',license_text)
        z.writestr('PROJECT_LICENSE.txt',own_license)
    with zipfile.ZipFile(package) as z:assert z.testzip() is None
    receipt=dict(version='0.7.9',html_bytes=target.stat().st_size,html_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
        zip_bytes=package.stat().st_size,zip_sha256=hashlib.sha256(package.read_bytes()).hexdigest(),embedded_project_attachments=len(embedded),
        external_assets_required=False,android_device_tested=False)
    (share/'manifest.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    print(json.dumps(receipt))
if __name__=='__main__':main()
