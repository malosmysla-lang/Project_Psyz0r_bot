"""Register stock Xaero only in the isolated test profile, after inspecting assets."""
from pathlib import Path
import shutil,zipfile
BASE=Path('/home/qlserver/psyz0r-test-server')
HOME=Path('/home/qlserver/psyz0r-test-server-home')
profile=HOME/'baseq3/zzz_psyz_profile.pk3'
matches=[]
for file in (BASE/'baseq3').glob('*.pk3'):
    try:
        with zipfile.ZipFile(file) as z:
            for name in z.namelist():
                if 'xaero' in name.lower() and name.lower().endswith('_c.c'):matches.append((file,name))
    except zipfile.BadZipFile:pass
print('XAERO_ASSETS',[(p.name,n) for p,n in matches],flush=True)
if not matches:raise SystemExit('Stock Xaero character not found; do not fabricate a baseline')
with zipfile.ZipFile(profile) as z:entries={n:z.read(n) for n in z.namelist()}
shutil.copy2(profile,profile.with_suffix('.before-074.bak'))
path,name=matches[0]
with zipfile.ZipFile(path) as z:entries[name]=z.read(name)
scripts=entries['scripts/bots.txt'].decode()
if 'name Xaero ' not in scripts:scripts+='\n{ name Xaero model xaero aifile '+name.removeprefix('botfiles/')+' }\n'
entries['scripts/bots.txt']=scripts.encode()
with zipfile.ZipFile(profile.with_suffix('.new'),'w',zipfile.ZIP_DEFLATED) as z:
    for n,data in entries.items():z.writestr(n,data)
profile.with_suffix('.new').replace(profile)
loose=HOME/'baseq3/scripts/bots.txt'
if loose.exists():shutil.copy2(loose,loose.with_suffix('.before-074.bak'))
loose.parent.mkdir(exist_ok=True)
loose.write_text(scripts)
print('XAERO_REGISTERED',flush=True)
