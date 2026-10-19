"""Generate a Xaero-5-derived test character from installed assets; never publish assets."""
import hashlib,json,re,zipfile
from pathlib import Path
STAGE=Path(__file__).resolve().parent
HOME=Path('/home/qlserver/psyz0r-test-server-home')
BASE=Path('/home/qlserver/psyz0r-test-server')

def main():
    original=HOME/'baseq3/zzz_psyz_profile.pk3'
    with zipfile.ZipFile(original) as z:entries={n:z.read(n) for n in z.namelist()}
    source=None;source_file=None
    for f in (BASE/'baseq3').glob('*.pk3'):
        with zipfile.ZipFile(f) as z:
            if 'botfiles/bots/xaero_c.c' in z.namelist():
                source=z.read('botfiles/bots/xaero_c.c').decode();source_file=f;break
    if source is None:raise RuntimeError('Installed Xaero source missing')
    match=re.search(r'\bskill\s+5\s*\{([^}]+)\}',source,re.S)
    if not match:raise RuntimeError('Xaero skill 5 not found')
    values=dict(re.findall(r'(CHARACTERISTIC_\w+)\s+("[^"]*"|[-.\w]+)',match[1]))
    required={'CHARACTERISTIC_ATTACK_SKILL','CHARACTERISTIC_AIM_SKILL','CHARACTERISTIC_VIEW_FACTOR','CHARACTERISTIC_ITEMWEIGHTS'}
    if not required<=values.keys():raise RuntimeError('Incomplete stock character')
    old=entries['botfiles/bots/psyz_c.c'].decode()
    changes={
      'CHARACTERISTIC_NAME':'"Psyz0r"',
      'CHARACTERISTIC_WEAPONWEIGHTS':'"bots/psyz_w.c"',
      'CHARACTERISTIC_REACTIONTIME':'.12',
      'CHARACTERISTIC_CROUCHER':'0',
      'CHARACTERISTIC_JUMPER':'.25',
      'CHARACTERISTIC_WEAPONJUMPING':'0',
    }
    # Наведение и предикт наследуют Xaero 5. Реальные human accuracy задаются
    # отдельным наблюдаемым aim-профилем, не уроном и не фиктивными попаданиями.
    for key,value in changes.items():values[key]=value
    text='#include "chars.h"\nskill 5 {\n'+''.join(f'{k} {v}\n' for k,v in values.items())+'}\n'
    entries['botfiles/bots/psyz_c.c']=text.encode()
    output=STAGE/'zzz_psyz_profile.pk3'
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
        for name,data in entries.items():z.writestr(name,data)
    previous=dict(re.findall(r'(CHARACTERISTIC_\w+)\s+("[^"]*"|[-.\w]+)',old))
    report=dict(stock_source=str(source_file),stock_character_sha256=hashlib.sha256(source.encode()).hexdigest(),profile_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),changes={k:dict(old=previous.get(k),new=v) for k,v in values.items() if previous.get(k)!=v},gameplay_accuracy_calibrated=False)
    (STAGE/'profile_report.json').write_text(json.dumps(report,indent=2))
    print('PROFILE_READY',report['profile_sha256'])
if __name__=='__main__':main()
