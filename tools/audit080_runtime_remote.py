"""Read-only failure context and active service evidence."""
import subprocess
from pathlib import Path
lines=Path('/home/qlserver/psyz0r-test-server-home/console.log').read_text(errors='replace').splitlines()
for i,line in enumerate(lines):
    if any(x in line.lower() for x in ['segmentation fault','fatal error','server shutdown','exit code']):
        print('\n'.join(lines[max(0,i-3):i+5]))
print(subprocess.check_output(['systemctl','show','psyz0r-test.service','-p','MainPID','-p','NRestarts','-p','ActiveState'],text=True))
