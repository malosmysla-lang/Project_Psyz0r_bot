"""Build a local-only PK3 with namespaced support files, preserving other bots."""
from pathlib import Path
import zipfile

def main():
    root = Path(__file__).resolve().parents[1]
    source = root / 'assets/profile'
    output = root / 'out/zz_psyz0r_bot.pk3'
    output.parent.mkdir(exist_ok=True)
    replacements = {name: 'psyz_support/' + name for name in ('chars.h', 'inv.h', 'fw_items.c', 'fw_weap.c')}
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
        for file in sorted(source.rglob('*')):
            if not file.is_file():
                continue
            path = file.relative_to(source).as_posix()
            if path.startswith('botfiles/') and '/' not in path[len('botfiles/'):]:
                path = 'botfiles/psyz_support/' + file.name
            content = file.read_text(encoding='utf-8')
            for old, new in replacements.items():
                content = content.replace('"' + old + '"', '"' + new + '"')
            archive.writestr(path, content.encode('utf-8'))
    with zipfile.ZipFile(output) as archive:
        assert archive.testzip() is None
        assert all(name.startswith(('botfiles/psyz_support/', 'botfiles/bots/psyz0r_', 'scripts/psyz0r.bot')) for name in archive.namelist())
    print(output)

if __name__ == '__main__':
    main()
