"""Transplant only this stage's edits onto the preserved deployed native source.

The deployed native tree contains inherited opt-in code absent from the clean
project baseline. Refuse ambiguous anchors instead of overwriting those changes.
"""
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import shutil
import subprocess


def transplant(base, updated, deployed):
    before=base.splitlines(keepends=True)
    after=updated.splitlines(keepends=True)
    result=deployed
    operations=[]
    for tag,a,b,c,d in reversed(difflib.SequenceMatcher(None,before,after,autojunk=False).get_opcodes()):
        if tag=='equal':continue
        old=''.join(before[a:b]);new=''.join(after[c:d])
        if old and result.count(old)==1:
            result=result.replace(old,new,1)
        else:
            for size in range(1,min(a,12)+1):
                anchor=''.join(before[a-size:a])
                needle=anchor+old
                if anchor and result.count(needle)==1:
                    result=result.replace(needle,anchor+new,1)
                    break
            else:
                raise RuntimeError(f'Ambiguous native source edit at base lines {a+1}:{b+1}')
        operations.append({'kind':tag,'base_start':a+1,'base_end':b+1})
    return result,operations


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--deployed-source',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args()
    root=Path(__file__).resolve().parents[1]
    shutil.copytree(args.deployed_source,args.output)
    evidence={}
    for name in ['psyz_prealpha.h','psyz_control_lab.h']:
        path='adapter/native/'+name
        base=subprocess.check_output(['git','-C',str(root),'show','1b52d27:'+path]).decode('utf-8')
        updated=(root/path).read_text(encoding='utf-8')
        target=args.output/name
        original=target.read_text(encoding='utf-8')
        result,operations=transplant(base,updated,original)
        target.write_text(result,encoding='utf-8',newline='\n')
        evidence[name]={'before_sha256':hashlib.sha256(original.encode()).hexdigest(),
                        'after_sha256':hashlib.sha256(result.encode()).hexdigest(),'operations':operations}
    (args.output.parent/'NATIVE_OVERLAY.json').write_text(json.dumps(evidence,indent=2),encoding='utf-8')
    print(json.dumps({k:len(v['operations']) for k,v in evidence.items()}))


if __name__=='__main__':main()
