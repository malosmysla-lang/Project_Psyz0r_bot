"""Inventory and download available unique ZTN demos of requested players."""
import concurrent.futures as cf
import hashlib,html,json,re,time
from collections import Counter
from pathlib import Path
import download_bloodrun_corpus as base

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'демки для обучения'/'BloodRun_top500_20261019'
ALIASES={'agent':['agent','agentje'],'avek':['avek','av3k'],'cypher':['cypher'],'rapha':['rapha'],
         'cooller':['cooller'],'evil':['evil'],'k1llsen':['k1llsen','killsen'],
         'toxjq':['toxjq','toxic'],'strenx':['strenx'],'clawz':['clawz']}
def names(d):
    result=[]
    for player in d['players']:
        nick=re.sub(r'\^[0-9]','',player['nick']).lower()
        for name,aliases in ALIASES.items():
            if any(re.search(r'(?<![a-z])'+re.escape(a)+r'(?![a-z])',nick) for a in aliases):result.append(name)
    return sorted(set(result))
def page(n):
    raw=base.fetch(f'https://demos.quakelive.ru/?map=6&page={n}').decode()
    return json.loads(html.unescape(re.search(r'data-page="([^"]+)"',raw)[1]))['props']['demos']
def main():
    OUT.mkdir(parents=True,exist_ok=True);base.OUT=OUT
    catalog_path=OUT/'catalog.json'
    if catalog_path.exists():catalog=json.loads(catalog_path.read_text(encoding='utf-8'))
    else:
        first=page(1);catalog=list(first['data'])
        with cf.ThreadPoolExecutor(max_workers=3) as pool:
            for n,payload in enumerate(pool.map(page,range(2,first['last_page']+1)),2):
                catalog+=payload['data'];print('Catalog page',n,flush=True)
        catalog_path.write_text(json.dumps(catalog,ensure_ascii=False,indent=2),encoding='utf-8')
    existing_ids=set();hashes=set()
    for file in ROOT.rglob('*.dm_*'):
        if file.parent==OUT:continue
        hashes.add(hashlib.sha256(file.read_bytes()).hexdigest())
        match=re.match(r'(\d+)__',file.name)
        if match:existing_ids.add(int(match[1]))
    selected=[d for d in catalog if d['map']['short_name'].lower()=='bloodrun' and d['type']=='Duel' and re.search(r'\.dm_(91|90|73)$',d['file']) and names(d)]
    selected.sort(key=lambda d:('agent' not in names(d),-d['id']))
    manifest_path=OUT/'manifest.json'
    manifest=json.loads(manifest_path.read_text(encoding='utf-8')) if manifest_path.exists() else {'records':[],'errors':[]}
    known={r['archive_id'] for r in manifest['records']};hashes.update(r['sha256'] for r in manifest['records'])
    counts=Counter(name for d in selected for name in names(d))
    candidates=[d for d in selected if d['id'] not in existing_ids|known]
    inventory=dict(catalog_records=len(catalog),matching_by_name=dict(counts),new_candidates=len(candidates),requested_total=500,requested_agent=100,alias_matching='Explicit names; not verified player identity')
    (ROOT/'docs/training/ZTN_TOP_PLAYER_AVAILABILITY_20261019.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(inventory),flush=True)
    for offset in range(0,len(candidates),3):
        if len(manifest['records'])>=500:break
        batch=candidates[offset:offset+min(3,500-len(manifest['records']))]
        with cf.ThreadPoolExecutor(max_workers=3) as pool:
            for demo,result in zip(batch,pool.map(base.download,batch)):
                if 'error' in result:manifest['errors'].append(result)
                elif result['sha256'] in hashes:
                    (OUT/result['filename']).unlink();manifest['errors'].append(dict(archive_id=result['archive_id'],error='duplicate_sha256'))
                else:
                    result['requested_players']=names(demo);manifest['records'].append(result);hashes.add(result['sha256'])
            manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
        print('Downloaded',len(manifest['records']),'of requested 500',flush=True)
    (ROOT/'docs/training/ZTN_TOP500_MANIFEST_20261019.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print('FINISHED available unique downloads',len(manifest['records']),flush=True)
if __name__=='__main__':main()
