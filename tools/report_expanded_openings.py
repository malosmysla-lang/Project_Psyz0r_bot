"""Summarize opening observations with counts and explicit evidence limits."""
import json
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def main():
    source=ROOT/'docs/training/BLOODRUN_OPENINGS_EXPANDED_20261019.json'
    data=json.loads(source.read_text(encoding='utf-8'))
    manifest=json.loads((ROOT/'демки для обучения/BloodRun_additional_300_20261019/manifest.json').read_text(encoding='utf-8'))
    analysis=json.loads((ROOT/'out/bloodrun_additional_300_20261019/analysis_index.json').read_text(encoding='utf-8'))
    protocols=Counter(r['filename'].rsplit('.',1)[-1] for r in manifest['records'])
    observed=[r for r in data['records'] if r['status']=='observed']
    confirmed=[r for r in observed if r.get('spawn_candidate')]
    first=Counter(r['first_weapon']['kind'] for r in confirmed if r.get('first_weapon'))
    seq=Counter(tuple(p['kind'] for p in r['first_three']) for r in confirmed)
    lines=['# ZTN: расширенный корпус и дебюты — 19.10.2026','',
        f"Дополнительных уникальных демок: **{len(manifest['records'])}**; объём {sum(r['size'] for r in manifest['records'])/1024**2:.1f} MiB.",
        f'Протоколы: {dict(protocols)}.',
        f"Успешно разобрано новых демок: {sum(r['status']=='parsed' for r in analysis['records'])}/{len(analysis['records'])}.",
        f"Совокупный разбор дебютов: {data['counts']}; достоверных кандидатов стартовой позиции: {len(confirmed)}.",'',
        '## Первая наблюдаемая пушка','', '| Оружие | Примеры |','|---|---:|']
    lines += [f'| {k} | {v} |' for k,v in first.most_common()]
    lines += ['', '## Первые три стратегических подбора', '', '| Последовательность | Примеры |', '|---|---:|']
    lines += [f"| {' → '.join(k)} | {v} |" for k,v in seq.most_common(20)]
    lines += ['', '## Ограничения', '',
        '- Это наблюдаемые решения POV, а не универсальная оптимальная политика для каждого респауна.',
        '- Не переносить частоту маршрута в его полезность: соперник, ранние потери и итог контроля могут быть неизвестны.',
        '- Телепорт/смена POV обрывает непрерывное окно; продолжение не выдаётся за проверенную траекторию.',
        '- Потеря здоровья включает decay/self-damage. Причина каждого урона и ранний фраг пока не атрибутированы.',
        '- Старые протоколы хранятся с происхождением; физика и совместимость с текущим сервером не подтверждены.',
        '- Скачивание и разбор не изменяют код бота автоматически. Новые дебюты не включены в игровое исполнение.']
    (ROOT/'docs/BLOODRUN_300_EXPANSION_20261019_RU.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('\n'.join(lines[:8]))

if __name__=='__main__':main()
