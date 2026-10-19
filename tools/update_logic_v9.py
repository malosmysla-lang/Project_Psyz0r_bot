"""Preserve every v8 rule and append the 0.7.9 evidence boundaries."""
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ADDITIONS={
 'D':[('PARTIAL','0.7.9 отслеживает реальное перемещение и при target=-1, если штатный AI выдаёт forward/right. Мёртвый бот, свой RJ и неподвижность без цели и команды движения не запускают этот сторож. Сброс цели не равен гарантированному выходу из угла.'),('PARTIAL','PSYZ_NAV 0.7.9 записывает forward/right/up/buttons, цель, маршрут, броню и escape. Скорость ps без изменения координат не доказывает движение. Старые неподвижные эпизоды без команд остаются кандидатами, а не автоматически ошибками навигации.')],
 'H':[('PARTIAL','Оба маршрутных сторожа используют одинаковую границу ожидания: менее 64u до предмета, перепад менее 40u, предмет недоступен и до появления не более 3с. Близость под платформой и уже лежащий предмет ожиданием не считаются; геометрия объёма подбора этим не доказана. В intermission pm_type!=0 надстройка не управляет ботом и не запускает восстановление.')],
 'F':[('DATA','Для дополнительной выборки и общего корпуса отдельно считаются строки победителя и лидера damageGiven. Один игрок не удваивается внутри выбранной группы; ничья по урону отмечается отдельно. Нет обоих damageGiven — лидер неизвестен. Нет shots — точность отсутствует; shots>0 и accuracy=0 — реальный ноль. GL не получает aim-профиль.')],
 'E':[('DATA','В 200 дополнительных оригиналах у доступных POV победителя/лидера урона выделены 37 стартов после остановки, 18 с полными 4с. Лучший наблюдаемый кандидат 617.776 UPS, не проверенный физический эталон. Медиана первого пика 494.553 и второго 575.893 UPS. Сырые WASD/mouse не восстановлены.')],
 'N':[('DATA','Переразобраны 200 SHA-уникальных оригиналов вне прежних top500; это файлы из сохранённого запаса, не 200 новых скачиваний. У всех извлечены snapshots и metadata; 127 итоговых 1v1-записей, в 22 победитель и лидер урона различаются. Для отсутствующих scoreboard/POV сведения не выдумываются.'),('DATA','Реестр матчей включает 7 известных дуэлей Psyz0r и 59 архивных записей Xaero отдельно. Неизвестные старые версии и skill остаются неизвестными. Каждая запись хранит источник, счёт, доступный damage, оружие и подборы; пропуски не превращаются в 0%.')],
 'O':[('PARTIAL','0.7.9 установлена только на 27961 после backup; SHA native проверен, основной PID 27960 сохранён. Профиль Xaero-derived, чат и aim-настройки не менялись. 17 CTest, 138 Python и 5 Linux групп прошли. Пятиминутная диагностика не доказывает силу серии 10-минутных дуэлей.'),('PARTIAL','Read-only ZMQ sidecar отдельно от QL сохраняет MATCH_STARTED/PLAYER_STATS/MATCH_REPORT в файл. MATCH_GUID дедуплицируется, поздние stats ожидаются, два bot STEAM_ID=0 различаются по имени. Приватный буфер и Steam ID не публикуются; реальная первая новая дуэль ещё ожидается.'),('PARTIAL','Локальный watcher забирает только public JSON через SSH и публикует MATCH_LEDGER.json из отдельного проверенного Git worktree. Сайт читает HTTPS-файл раз в 30с; офлайн HTML хранит снимок. Работа синхронизации зависит от включённого ПК, серверный сборщик работает независимо.'),('SPEC','Автоматическое обучение модели не подключено. Оценка прогресса требует хотя бы 10 сопоставимых матчей одной версии/native SHA, карты и соперника длительностью от 5 минут. Рост числа правил и разный счёт против разных соперников не доказывают обучение.')]
}
def main():
    text=(ROOT/'docs/MINDMAP_V8_CONTENT_RECONCILIATION_RU.md').read_text(encoding='utf-8').replace('Mind Map v8','Mind Map v9')
    text='> Этап 0.7.9: подробный отчёт PREALPHA_0_7_9_RU.md; прежние статусы ниже — история своих этапов.\n\n'+text
    for letter,rows in ADDITIONS.items():
        m=re.search(r'^## '+letter+r'\. .*?(?=^## |\Z)',text,re.M|re.S);block=m.group()
        last=max(int(x) for x in re.findall(r'`'+letter+r'(\d+) ',block))
        extra='\n'.join(f'- `{letter}{last+i:02d} {status}` {line}' for i,(status,line) in enumerate(rows,1))
        text=text[:m.start()]+block.rstrip()+'\n'+extra+'\n\n'+text[m.end():]
    text+='\n## Источники 0.7.9\n\nPREALPHA_0_7_9_RU.md; training/RESERVE200_RESEARCH_079.json; training/RESERVE200_079_MANIFEST.json; training/PREALPHA_079_DEPLOYMENT.json.\n'
    (ROOT/'docs/MINDMAP_V9_CONTENT_RECONCILIATION_RU.md').write_text(text,encoding='utf-8')
    generator=(ROOT/'tools/generate_mindmap_v8.py').read_text(encoding='utf-8').replace('v8','v9').replace('V8','V9').replace("'version':8","'version':9")
    generator=generator.replace('v7','v8').replace('V7','V8')
    (ROOT/'tools/generate_mindmap_v9.py').write_text(generator,encoding='utf-8')
    print('Prepared v9; previous v8 rules retained')
if __name__=='__main__':main()
