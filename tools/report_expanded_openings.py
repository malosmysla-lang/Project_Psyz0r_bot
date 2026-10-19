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
    confirmed=[r for r in observed if r.get('observed_ms',0)>=1000 and r.get('start_delay_ms',99999)<=2000]
    first=Counter(r['first_weapon']['kind'] for r in confirmed if r.get('first_weapon'))
    seq=Counter(tuple(p['kind'] for p in r['first_three']) for r in confirmed)
    lines=['# ZTN: расширенный корпус и дебюты — 19.10.2026','',
        f"Дополнительных уникальных демок: **{len(manifest['records'])}**; объём {sum(r['size'] for r in manifest['records'])/1024**2:.1f} MiB.",
        f'Протоколы: {dict(protocols)}.',
        f"Успешно разобрано новых демок: {sum(r['status']=='parsed' for r in analysis['records'])}/{len(analysis['records'])}.",
        f"Совокупный разбор дебютов: {data['counts']}; пригодных ранних окон >=1 секунды с задержкой <=2 секунд: {len(confirmed)}.",
        'Одиночный стартовый снимок перед snapshot_gap исключён из выводов. Раннее окно не всегда доказывает точку респауна.','',
        '## Первая наблюдаемая пушка','', '| Оружие | Примеры |','|---|---:|']
    lines += [f'| {k} | {v} |' for k,v in first.most_common()]
    lines += ['', '## Первые три стратегических подбора', '', '| Последовательность | Примеры |', '|---|---:|']
    lines += [f"| {' → '.join(k)} | {v} |" for k,v in seq.most_common(20)]
    lines += ['', '## Варианты по ранней наблюдаемой позиции', '', 'Позиция начала окна не всегда совпадает с респауном.', '', '| Позиция | Примеры | Самый частый порядок (частота) |', '|---|---:|---|']
    import math
    groups=[]
    for record in confirmed:
        group=next((g for g in groups if math.dist(g['position'],record['start_position'])<=64),None)
        if group is None:
            group=dict(position=record['start_position'],records=[]);groups.append(group)
        group['records'].append(record)
    for group in groups:
        variants=Counter(tuple(p['kind'] for p in r['first_three']) for r in group['records'])
        sequence,count=variants.most_common(1)[0]
        position=', '.join(f'{v:.0f}' for v in group['position'])
        label=' → '.join(sequence) or 'нет наблюдаемого подбора'
        lines.append(f"| {position} | {len(group['records'])} | {label} ({count}) |")
    lines += ['', '## Ограничения', '',
        '- Это наблюдаемые решения POV, а не универсальная оптимальная политика для каждого респауна.',
        '- Не переносить частоту маршрута в его полезность: соперник, ранние потери и итог контроля могут быть неизвестны.',
        '- Телепорт/смена POV обрывает непрерывное окно; продолжение не выдаётся за проверенную траекторию.',
        '- Потеря здоровья включает decay/self-damage. Причина каждого урона и ранний фраг пока не атрибутированы.',
        '- Старые протоколы хранятся с происхождением; физика и совместимость с текущим сервером не подтверждены.',
        '- Скачивание и разбор не изменяют код бота автоматически. Новые дебюты не включены в игровое исполнение.']
    (ROOT/'docs/BLOODRUN_300_EXPANSION_20261019_RU.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps(dict(downloads=len(manifest['records']),parsed=sum(r['status']=='parsed' for r in analysis['records']),counts=data['counts'],usable_early_windows=len(confirmed),first_weapons=dict(first)),ensure_ascii=True))

if __name__=='__main__':main()
