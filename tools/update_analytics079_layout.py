"""Integrate the reserve-research panel without changing the retained layout."""
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1];SITE=ROOT/'Аналитика разработки бота'
SECTION='''<section id="research079"><div class="section-label">0.7.9 / РАСШИРЕННЫЙ РАЗБОР</div><h2>Победа и преимущество по урону</h2><p id="reserveSummary" class="sub"></p><div class="grid2"><article class="card panel"><h3>Точность двух групп</h3><div id="cohortBars"></div><p class="caption">Среднее по доступным строкам статистики. Группы пересекаются; это не независимые выборки и не достигнутая точность бота.</p></article><article class="card panel"><h3>Разгон после остановки</h3><div id="reserveJumps"></div><p class="caption">Только доступный POV выбранных игроков. Скорость и yaw наблюдаемы; сырые WASD и mouse deltas не подтверждены. Лучший кандидат требует проверки физики.</p><h3>Испытание 0.7.9</h3><p id="trial079Summary" class="caption"></p></article></div><h3>Распределение точности победителей</h3><div id="accuracyHistograms" class="grid3"></div><div class="card tablewrap"><table class="table"><thead><tr><th>Оружие</th><th>Победитель · среднее / N</th><th>Лидер урона · среднее / N</th></tr></thead><tbody id="cohortRows"></tbody></table></div><p class="caption">N — строки match/player с shots &gt; 0. Отсутствующее значение не заменяется нулём. Последний столбец гистограммы включает 100%. GL показан справочно и не меняет настройки спама.</p><p><a href="../docs/PREALPHA_0_7_9_RU.md">Подробный разбор и ограничения ↗</a> · <a href="../docs/training/RESERVE200_RESEARCH_079.json">Полный JSON ↗</a></p></section>'''
def main():
    p=SITE/'index.html';s=p.read_text(encoding='utf-8')
    s=s.replace('<title>Pracc Room Server</title>','<title>Pracc Room Server · BOT</title>')
    s=s.replace('<h1>Pracc Room Server</h1>','<h1>Pracc Room Server <span class="bot-word">BOT</span></h1>')
    s=s.replace('<span>Pracc Room<br>Server</span>','<span>Pracc Room<br>Server <b class="bot-word">BOT</b></span>')
    helmet='<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M5 18V8l3-5h8l3 5v10l-4 3H9zM5 10h14M8 10l1 5h6l1-5M10 18h4"/></svg>'
    s=s.replace('<span class="sigil">P/</span>','<span class="sigil">'+helmet+'</span>')
    if 'id="research079"' not in s:s=s.replace('<section id="tests">',SECTION+'\n<section id="tests">')
    s=s.replace('docs/mindmap_v8/','docs/mindmap_v9/').replace('Psyz0r_bot_mindmap_v8','Psyz0r_bot_mindmap_v9')
    if 'href="#research079"' not in s:s=s.replace('</nav>','<a href="#research079">◈ / Разбор 0.7.9</a></nav>',1)
    if 'src="research079.js"' not in s:s=s.replace('</body>','<script src="research079.js"></script></body>')
    if 'id="versionComparison"' not in s:
        history='<section id="versionComparison"><div class="section-label">VERSION HISTORY / 3 ПРЕДЫДУЩИЕ + ТЕКУЩАЯ</div><h2>Сравнение этапов разработки</h2><div class="toolbar"><label for="versionSelect">Версия</label><select id="versionSelect" class="form-select"><option>0.7.9</option><option>0.7.8</option><option>0.7.7</option><option>0.7.6</option></select><label for="metricSelect">Показатель</label><select id="metricSelect" class="form-select"><option value="demos">Разобранные демки</option><option value="rules">Правила карты</option><option value="cpp">Группы CTest</option></select></div><div class="grid2"><article class="card panel"><div id="versionTrend"></div><p class="caption">Документальные показатели разработки, не процент силы бота. Число правил и тестов не заменяет игровые результаты.</p></article><article class="card panel"><h3 id="versionTitle"></h3><p id="versionNote"></p><div id="versionValues"></div></article></div></section>'
        s=s.replace('<section id="research079">',history+'<section id="research079">')
    if 'src="version-history.js"' not in s:s=s.replace('</body>','<script src="version-history.js"></script></body>')
    if 'id="mindmapApp"' not in s:
        s=s.replace('<div class="toolbar"><input id="search"','<div id="mindmapApp"></div><details class="text-registry"><summary>Полный текстовый реестр · доступный список всех правил</summary><div class="toolbar"><input id="search"',1)
        s=s.replace('<div id="branches" class="branch-grid"></div>','<div id="branches" class="branch-grid"></div></details>',1)
        s=re.sub(r'<div class="card panel map-preview">.*?</div>','',s,count=1,flags=re.S)
    if 'src="mindmap-core.js"' not in s:s=s.replace('</body>','<script src="mindmap-core.js"></script><script src="mindmap.js"></script></body>')
    if 'id="duels"' not in s:
        duels='''<section id="duels"><div class="section-label">MATCH LEDGER / ФАКТИЧЕСКИЕ ДУЭЛИ</div><h2>Матчи бота и прогресс</h2><p id="ledgerSync" class="caption">Встроенный снимок; онлайн-файл проверяется каждые 30с.</p><div class="toolbar"><select id="duelActor" class="form-select" aria-label="Участник"><option value="Psyz0r">Наш Psyz0r</option><option value="Xaero baseline">Базовый Xaero · архив</option></select><select id="duelType" class="form-select" aria-label="Тип соперника"><option value="">Все соперники</option><option value="human">Против человека</option><option value="bot">Против бота</option></select></div><p id="duelCount" class="caption"></p><div class="card tablewrap"><table class="table"><thead><tr><th>Матч / источник</th><th>Версия</th><th>Соперник / карта</th><th>Счёт</th><th>Damage</th><th>RA / MH / YA</th><th>MG</th><th>SG</th><th>RL</th><th>LG</th><th>RG</th><th>PG</th></tr></thead><tbody id="duelRows"></tbody></table></div><p class="caption">Нажми на матч для разбора ниже. — означает отсутствие данных либо отсутствие выстрелов; это не фиктивные 0%. Архивный Xaero определён по имени в демке; skill старых записей не подтверждён.</p><div class="grid2"><article class="card panel"><h3>Динамика разницы счёта</h3><div id="duelTrend"></div><p class="caption">Фраги на 10 минут, до 30 последних матчей выбранного фильтра. Разные соперники и версии не образуют контролируемый эксперимент.</p></article><article class="card panel"><h3>Победы / поражения</h3><div id="duelResultsPie" class="donut-layout"></div><p class="caption">Только завершённые матчи с доступным счётом; ничьи не входят в две доли.</p></article></div><h3 id="duelSelected"></h3><div class="grid2"><article class="card panel"><h3>Стрельба по оружию</h3><div id="duelWeaponBars"></div></article><article class="card panel"><h3>Подборы обеих сторон</h3><div id="duelPickupBars"></div><h3>Структура известного урона бота</h3><div id="duelDamagePie" class="donut-layout"></div><p class="caption">Доли hitscan и снарядов только по известным weapon damage. Для splash/SG счётчики отличаются от hitscan.</p></article></div><article class="card panel"><h3>Учится ли бот?</h3><p id="learningStatus"></p></article></section>'''
        s=s.replace('<section id="versionComparison">',duels+'<section id="versionComparison">')
        s=s.replace('</nav>','<a href="#duels">◈ Матчи бота</a></nav>',1)
    if 'src="duels.js"' not in s:s=s.replace('</body>','<script src="duels.js"></script></body>')
    nav=re.search(r'<nav>.*?</nav>',s,re.S)
    if nav:
        icons=['M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z','M4 7h16M4 12h16M4 17h16','M12 3v18M3 12h18M5 5l14 14M19 5L5 19','M5 4h14v16H5zM8 8h8M8 12h8M8 16h5','M8 3h8v7l-4 4-4-4zM6 21h12M12 14v7','M3 17l5-6 5 3 8-11','M4 5h16M4 12h12M4 19h8','M5 4h14v16H5zM8 8h8M8 12h8','M3 18l5-8 5 4 8-10']
        i=iter(icons)
        content=re.sub(r'(<a href="#[^"]+">)(?:\d{2} / |◈ / )',lambda m:m[1]+'<svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="'+next(i,icons[0])+'"/></svg>',nav.group())
        s=s[:nav.start()]+content+s[nav.end():]
    p.write_text(s,encoding='utf-8')
    # Two accent colors across analytical charts and the editable map.
    palette="['#42e8dc','#b18aff','#42e8dc','#b18aff','#42e8dc','#b18aff','#42e8dc','#b18aff','#42e8dc','#b18aff','#42e8dc','#b18aff','#42e8dc','#b18aff','#42e8dc']"
    for filename,name in [('app.js','colors'),('mindmap-core.js','palette')]:
        path=SITE/filename;code=path.read_text(encoding='utf-8');code=re.sub(r'const '+name+r'=\[[^\]]+\]', 'const '+name+'='+palette,code,count=1);path.write_text(code,encoding='utf-8')
if __name__=='__main__':main()
