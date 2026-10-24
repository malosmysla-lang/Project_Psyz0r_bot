"""Build reviewable annotation windows from existing read-only POV exports.

Crucial ownership rule: 'Good move Psyz0r' describes the BOT, whereas the
exported POV can belong to the human. Never train the human trajectory as
positive bot behaviour merely because the timestamps coincide.
No raw key reconstruction, live writes or autonomous-learning claim.
"""
import argparse,bisect,json,math,re
from pathlib import Path

def window(rows, marker):
    candidates=[r for r in rows if r.get('game_state_number')==marker['state']
                and marker['time']-2000<=r['time_ms']<=marker['time']+1000]
    if not candidates:return {'aligned':False,'reason':'no_same_state_pov_window'}
    nearest=min(candidates,key=lambda r:abs(r['time_ms']-marker['time']))
    if abs(nearest['time_ms']-marker['time'])>50:return {'aligned':False,'reason':'clock_gap'}
    # Death, teleport, POV switch and packet gaps must not become a learned turn.
    continuous=all(a['client']==b['client'] and a['segment']==b['segment'] and
        0<b['time_ms']-a['time_ms']<=100 and a['pm_type']==b['pm_type']==0 and
        math.dist(a['position'],b['position'])<=256 for a,b in zip(candidates,candidates[1:]))
    text=re.sub(r'\^[0-9]','',marker['text']).casefold()
    subject='bot' if re.search(r'psyz|xaero|\bbot\b',text) else 'unspecified'
    label='negative' if re.search(r'bad|stuck|застр|плох',text) else 'positive' if re.search(r'good|хорош',text) else 'unclassified'
    return {'aligned':True,'continuous':continuous,'annotation_subject':subject,'label':label,
        'pov_client':nearest['client'],'alignment_error_ms':nearest['time_ms']-marker['time'],
        'start_ms':candidates[0]['time_ms'],'end_ms':candidates[-1]['time_ms'],
        'start_position':candidates[0]['position'],'end_position':candidates[-1]['position'],
        'peak_speed_xy':max(r['speed_xy'] for r in candidates),
        'pov_path_length':sum(math.dist(a['position'],b['position']) for a,b in zip(candidates,candidates[1:])),
        'eligible_for_automatic_positive_imitation':False,
        'reason':'annotation_actor_is_not_verified_pov_actor','raw_keys_verified':False}

def build(manifest,base):
    output=[]
    for demo in manifest:
        path=Path(demo['snapshotsFile'].replace('\\','/'))
        if not path.is_absolute():path=base/path
        rows=[json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
        for marker in demo.get('annotations',[]):
            output.append({'demo_sha256':demo['sha256'],'demo':demo['file'],'marker':marker,**window(rows,marker)})
    return {'windows':output,'aligned':sum(x.get('aligned',False) for x in output),
            'automatic_positive_training_examples':0,'game_commands_sent':False}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('manifest',type=Path);p.add_argument('--base',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();result=build(json.loads(args.manifest.read_text(encoding='utf-8')),args.base)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'windows':len(result['windows']),'aligned':result['aligned'],'automatic_positive_training_examples':0}))
