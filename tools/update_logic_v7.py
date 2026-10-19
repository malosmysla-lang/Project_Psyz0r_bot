"""Append offline research to v6 without changing the owner's current 0.7.6 playtest."""
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ADDITIONS={
 'D':[('DATA','В новой аналитике смерть, смена POV, разрыв >100мс и скачок позиции >128u обрывают локальные окна. Ресурсные цепочки не склеиваются через недоказанный переход/респаун; teleport-разрывы поэтому дают консервативную неполную выборку.')],
 'E':[('DATA','360° извлекаются как ограниченные по угловой скорости кандидаты: 350–410° net yaw за 0.25–2с, скорость ≥150 UPS, без своего недавнего огня и разрывов. Это не доказательство намерения и не разрешение крутить live-прицел.')],
 'F':[('DATA','Перед выстрелом измеряется непрерывное 250мс окно: yaw-span≤6° и pitch-span≤4° означают held-view candidate. Окна LG перекрываются; долю нельзя выдавать за независимую выборку игроков или точность попаданий.'),('DATA','Банк направлений прицела группируется по ячейке игрока 128×128×64u и оружию, ≥8 выстрелов из ≥3 демок, circular concentration≥0.8. Без BSP/LOS и подтверждения цели это не готовый прострел и не скрытый aim point.')],
 'G':[('LOCAL','Новый чистый C-модуль добивания выбирает оружие только при видимом контакте, известном стеке и подтверждённом hit не старше 900мс. Учитывает боезапас, self-splash, направление сближения и безопасный melee. К usercmd текущего теста не подключён.'),('DATA','Смена пушек в 5с перед POV-фрагом даёт multi-weapon candidate. Не засчитывать это как урон каждой пушкой той же цели; квота 65–70% не должна заставлять лишний switch.')],
 'H':[('LOCAL','Локальный arrival planner считает время выхода по проверенному p90 маршрута и запасу раннего прихода. DEFER = собирать другие ресурсы; HOLD только внутри подтверждённого объёма подбора и при безопасном ожидании. Непроверенный путь не получает выдуманный ETA.'),('DATA','Неподвижность до 2с перед major pickup хранится как dwell candidate с timer_verified=false. Это может быть ожидание или ошибка пути; без глобального item clock не доказывает секундный stopwatch.')],
 'I':[('DATA','Повторяющиеся тройки предметов и переходы хранятся с числом разных демок и median/p90 времени. Частота не доказывает оптимальный дебют; отдельно нужны spawn, урон, противодействие и результат цепочки.')],
 'O':[('SPEC','Пока владелец тестирует 0.7.6, live-бинарник/конфиг не менять. Новые надстройки сохранять локально и в GitHub, на сервер — только версионированную исходную/аналитическую копию отдельно от runtime; следующий бот-v-bot прогон после человеческих игр.')]
}
def main():
    text=(ROOT/'docs/MINDMAP_V6_CONTENT_RECONCILIATION_RU.md').read_text(encoding='utf-8').replace('Mind Map v6','Mind Map v7')
    text=text.replace('Проведено восстановление корпуса и локальная проверка 0.7.6; игровые результаты отдельно описаны в отчёте выпуска.','Текущий игровой тест остаётся на 0.7.6. Здесь добавлены офлайн-исследования и локальные контракты следующего этапа; они не подменяют результаты человеческой дуэли.')
    for letter,rows in ADDITIONS.items():
        match=re.search(r'^## '+letter+r'\. .*?(?=^## |\Z)',text,re.M|re.S);block=match.group()
        last=max(int(x) for x in re.findall(r'`'+letter+r'(\d+) ',block))
        extra='\n'.join(f'- `{letter}{last+i:02d} {status}` {line}' for i,(status,line) in enumerate(rows,1))
        text=text[:match.start()]+block.rstrip()+'\n'+extra+'\n\n'+text[match.end():]
    text+='\n## Источники офлайн-этапа 0.7.7\n\n- [Разбор и ограничения](TACTICAL_RESEARCH_077_RU.md).\n- `training/TACTICAL_PATTERNS_077.json`; источники: 500 восстановленных SHA-256 и UDT POV/obituary metadata.\n- `adapter/native/psyz_combo_policy.h`, `psyz_item_arrival.h`: локальные чистые политики, не подключённые к текущему runtime.\n'
    (ROOT/'docs/MINDMAP_V7_CONTENT_RECONCILIATION_RU.md').write_text(text,encoding='utf-8')
    gen=(ROOT/'tools/generate_mindmap_v6.py').read_text(encoding='utf-8').replace('v6','v7').replace('V6','V7').replace("'version':6","'version':7")
    (ROOT/'tools/generate_mindmap_v7.py').write_text(gen,encoding='utf-8')
    print('Prepared v7; all v6 rules retained')
if __name__=='__main__':main()
