"""Download a reproducible local Blood Run corpus from the owner's chosen archive."""
import argparse
import concurrent.futures as cf
import hashlib
import html
import json
import re
import struct
import time
import urllib.parse
import urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'демки для обучения'/'BloodRun_100'
def fetch(url):
    req=urllib.request.Request(url,headers={'User-Agent':'Psyz0r-demo-research/1.0'})
    with urllib.request.urlopen(req,timeout=45) as r:
        data=r.read(64*1024*1024+1)
        if len(data)>64*1024*1024:raise ValueError('Unexpectedly large demo')
        return data

def framed(data):
    pos=0;messages=0
    while pos+8<=len(data):
        seq,size=struct.unpack_from('<ii',data,pos);pos+=8
        if seq==-1 and size==-1:return messages>0 and pos==len(data)
        if not 0<=size<=131072 or pos+size>len(data):return False
        pos+=size;messages+=1
    # Some valid QL demos end at EOF instead of an explicit end marker.
    return messages>0 and pos==len(data)

def download(d):
    url='https://files.quakelive.ru/'+urllib.parse.quote(d['file'],safe='')
    filename=str(d['id'])+'__'+re.sub(r'[<>:"/\\|?*\x00-\x1f]','_',d['file'])
    path=OUT/filename
    for attempt in range(3):
        try:
            data=path.read_bytes() if path.exists() else fetch(url)
            if not framed(data):raise ValueError('Invalid demo framing')
            digest=hashlib.sha256(data).hexdigest()
            if not path.exists():
                temp=path.with_suffix(path.suffix+'.part');temp.write_bytes(data);temp.replace(path)
            return dict(archive_id=d['id'],filename=filename,source_url=url,archive_page='https://demos.quakelive.ru/demo?demoId='+str(d['id']),sha256=digest,size=len(data),catalog_map=d['map']['short_name'],type=d['type'],players=[x['nick'] for x in d['players']],pov=d.get('pov'),date=d['date'],framing_verified=True)
        except Exception as e:
            if attempt==2:return dict(archive_id=d['id'],error=str(e))
            time.sleep(1+attempt)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--exclude-id',type=int,action='append',default=[]);args=ap.parse_args()
    OUT.mkdir(parents=True,exist_ok=True);candidates=[];ids=set(args.exclude_id)
    for page in range(1,32):
        raw=fetch('https://demos.quakelive.ru/?map=6&page='+str(page)).decode()
        data=json.loads(html.unescape(re.search(r'data-page="([^"]+)"',raw)[1]))['props']['demos']
        for d in data['data']:
            if d['id'] not in ids and d['map']['short_name']=='bloodrun' and d['type']=='Duel' and d['file'].endswith('.dm_91'):
                candidates.append(d);ids.add(d['id'])
        if len(candidates)>=120:break
        time.sleep(.3)
    manifest=[];hashes=set();errors=[]
    # Fetch 100 initially; extras only if needed to replace failed/duplicate files.
    for batch in [candidates[:100],candidates[100:]]:
        if len(manifest)>=100:break
        needed=100-len(manifest)
        with cf.ThreadPoolExecutor(max_workers=3) as pool:
            for r in pool.map(download,batch[:needed]):
                if 'error' in r:errors.append(r)
                elif r['sha256'] not in hashes:manifest.append(r);hashes.add(r['sha256'])
                else:errors.append(dict(archive_id=r['archive_id'],error='duplicate_sha256'))
                (OUT/'manifest.json').write_text(json.dumps(dict(records=manifest,errors=errors),ensure_ascii=False,indent=2),encoding='utf-8')
                if len(manifest)%10==0:print('Downloaded unique demos:',len(manifest),flush=True)
    print('COMPLETE',len(manifest),'unique demos;',sum(x['size'] for x in manifest),'bytes; errors',len(errors),flush=True)
    if len(manifest)!=100:raise RuntimeError('Corpus incomplete; inspect manifest')
if __name__=='__main__':main()
