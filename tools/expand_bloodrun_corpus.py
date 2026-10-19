"""Resume a 300-demo expansion; exclude all existing local demo hashes/IDs."""
import concurrent.futures as cf
import hashlib
import html
import json
import re
import time
from pathlib import Path
import download_bloodrun_corpus as base

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'демки для обучения' / 'BloodRun_additional_300_20261019'

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    base.OUT = OUT
    manifest_path = OUT / 'manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8')) if manifest_path.exists() else {'records': [], 'errors': []}
    ids = {r['archive_id'] for r in manifest['records']}
    hashes = {r['sha256'] for r in manifest['records']}
    for file in ROOT.rglob('*.dm_*'):
        if file.parent == OUT:
            continue
        hashes.add(hashlib.sha256(file.read_bytes()).hexdigest())
        m = re.match(r'(\d+)__', file.name)
        if m:
            ids.add(int(m.group(1)))
    for file in (ROOT / 'демки для обучения').rglob('manifest.json'):
        if file == manifest_path:
            continue
        for record in json.loads(file.read_text(encoding='utf-8')).get('records', []):
            ids.add(record['archive_id'])
            hashes.add(record['sha256'])
    print(f'Existing exclusions: {len(ids)} IDs, {len(hashes)} hashes', flush=True)
    candidates = []
    last_page = 1
    for page in range(1, 200):
        raw = base.fetch(f'https://demos.quakelive.ru/?map=6&page={page}').decode()
        payload = json.loads(html.unescape(re.search(r'data-page="([^"]+)"', raw)[1]))['props']['demos']
        last_page = payload.get('last_page', page)
        for demo in payload['data']:
            if demo['id'] not in ids and demo['map']['short_name'] == 'bloodrun' and demo['type'] == 'Duel' and re.search(r'\.dm_(91|90|73)$', demo['file']):
                candidates.append(demo)
                ids.add(demo['id'])
        print(f'Catalog page {page}/{last_page}: {len(candidates)} new candidates', flush=True)
        if len(candidates) >= 360 or page >= last_page:
            break
        time.sleep(.25)
    for offset in range(0, len(candidates), 3):
        needed = 300 - len(manifest['records'])
        if needed <= 0:
            break
        with cf.ThreadPoolExecutor(max_workers=3) as pool:
            for result in pool.map(base.download, candidates[offset:offset + min(3, needed)]):
                if 'error' in result:
                    manifest['errors'].append(result)
                elif result['sha256'] in hashes:
                    (OUT / result['filename']).unlink()
                    manifest['errors'].append({'archive_id': result['archive_id'], 'error': 'duplicate_sha256_excluded'})
                else:
                    manifest['records'].append(result)
                    hashes.add(result['sha256'])
                manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f'Unique new downloads: {len(manifest["records"])}/300', flush=True)
    print(f'COMPLETE: {len(manifest["records"])} unique new demos; catalog pages={last_page}', flush=True)
    if len(manifest['records']) != 300:
        raise RuntimeError('Archive exhausted or download errors; manifest records actual count')

if __name__ == '__main__':
    main()
