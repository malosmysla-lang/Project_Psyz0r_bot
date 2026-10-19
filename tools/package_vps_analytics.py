"""Package only the public website, sanitized seed and read-only web handler."""
from pathlib import Path
import tarfile,hashlib,json
ROOT=Path(__file__).resolve().parents[1]
output=ROOT/'out/share/pracc-vps-site.tar.gz'
with tarfile.open(output,'w:gz') as archive:
    for p in (ROOT/'out/sites-pracc/dist').rglob('*'):
        if p.is_file():archive.add(p,arcname=p.relative_to(ROOT/'out/sites-pracc/dist').as_posix(),recursive=False)
    archive.add(ROOT/'server/telemetry/analytics_web.py',arcname='analytics_web.py')
    archive.add(ROOT/'docs/training/MATCH_LEDGER.json',arcname='match-ledger-seed.json')
print(json.dumps({'archive':str(output),'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'bytes':output.stat().st_size}))
