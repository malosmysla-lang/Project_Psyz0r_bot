# 2026-10-12 - All-weapon accuracy proposal, both players

Computed equal player-match arithmetic means and p25-p75 across both sides, with minimum-shot filters. Seven weapons have usable samples; others remain unknown. Proposed all-weapon profile saved disabled/unapproved; existing approved PG/LG profile unchanged. No runtime edits. See docs/ALL_WEAPON_ACCURACY_RU.md.

# 2026-10-12 - Prealpha 0.6.5 deployed to isolated 27961

Grounded combat hold, nearby-item/loadout diagnostics, empty RL/LG/RG pickup priority and approved LG/PG aim-error calibration installed after backup. Debug/Release 13/13; Python99/99; native SHA7c8f96c5f4c156431337ec80611835691b6d8808781350027914bf4ad0cbe017. Full situational weapon policy, red under human pressure and respawn routing remain incomplete. See docs/PREALPHA_0_6_5_RU.md and smoke report.

# 2026-10-12 - First combat patch prepared offline

Approved accuracy targets: PG 10-16% base12; LG 33-41% base37. Added combat hold between shots, grounded jump suppression, nearby-item diagnostics, empty-trinity weapon priority and gated smooth LG/PG angular error (not calibrated match percentages). Debug/Release 13/13; Python99/99; Linux NOPY compiled. Not deployed; full weapon selection and red/spawn followups remain. See docs/COMBAT_PATCH_01_RU.md.

# 2026-10-12 - Three-demo playtest comparison

Preserved and parsed Psyz0r, Xaero and dammit recordings; exported all 100 corpus match-stat files (99 with player stats). Confirmed Psyz0r zero red, 5 Mega, shotgun 50.8% damage; server interval has 9 RL pickups, first +31.025s. Marked 7 deaths <=5s after respawn against dammit. Found firing-button-only gate for route strafe, not a full combat gate. Analysis only, no runtime changes. See docs/PLAYTEST_COMPARISON_20261012_RU.md.

# 2026-10-12 - Prealpha 0.6.4 deployed to isolated 27961

Backed up isolated native/config; installed SHA-verified 0.6.4, enabled both navigation switches. Blood Run Duel, 10min, unlimited frags, 120s overtime; only Psyz0r (stock Sarge skill5 base plus custom native overlay), no Xaero. Warmup smoke: 10 actual pickups; red at 38775ms, 2300ms after failed demo route fell back to AAS at 36475ms. One recovery, no RJ in smoke, integration errors see report. Main service unchanged. See docs/training/PREALPHA_0_6_4_SMOKE.json. New PJ/RJ candidates are not enabled actions.

# 2026-10-12 - Red boost analysis, five-second pickup window

Audited 1,416 red pickup events with 8s context and <=5s damage-to-pickup window: 700 candidate approaches, 729 rocket and 97 plasma coincidences (not unique proven self-damage jumps). Added continuity/teleport exclusions, source SHA provenance and four regression tests; Python 99/99. See docs/RED_BOOST_ANALYSIS_RU.md. No new PJ actions enabled.

# 2026-10-12 - Duel Pracc Room Xaero control commands

Server plugin and Welcome config updated on disk after timestamped backups. `!goduel` arms one practice duel for exactly one human, rejects a running match, and uses the existing one-duel lifecycle; `!leaveme` aliases the existing level-5 bot-removal command. Syntax plus 3 focused mocked cases passed. Main service PID is unchanged; commands are not yet active in the running process and no live gameplay test or restart was performed. See docs/server/DUEL_PRACC_ROOM_STATUS_2026-10-12_RU.md.

# 2026-10-12 - Duel Pracc Room square-glyph follow-up

Read-only server check after a second screenshot: ASCII-only mappool entries and mapguard formatting with standard Quake color escapes; no square exists in the stored `qcdm1` entry. The same glyph appears in separate plugin messages, but its source remains unlocalized. No server changes, runtime actions, or restart. Next diagnostic requires comparing the exact server-emitted message with client rendering and owner authorization for any live test. See docs/server/DUEL_PRACC_ROOM_STATUS_2026-10-12_RU.md.

# 2026-10-12 - Duel Pracc Room audit snapshot

Separate server-only audit snapshot is provisional. Main Quake Live service was active and enabled at inspection; no live changes or restarts were made. The infographic reports 6/18 implemented-or-confirmed, 7/18 partial, and 5/18 not started, based on equal item counts only. The welcome-square source, recent complete match reports, and full prior chat remain unresolved. This audit does not change or represent Psyz0r bot implementation readiness. See docs/server/DUEL_PRACC_ROOM_STATUS_2026-10-12.svg and docs/server/DUEL_PRACC_ROOM_STATUS_2026-10-12_RU.md.

# 2026-10-12 - Prealpha 0.6.4 offline navigation recovery

Separate bounded navigation watchdog and red-route switches; late item registry retry. Audited 1,415 red pickups, added 24 grounded approaches, cut and re-parsed 10 real clips (4 confirmed owner RJ + 6 longjump candidates). MSVC Debug/Release 13/13 each; Python 95/95; Linux NOPY built offline. NOT deployed or live verified. See docs/PREALPHA_0_6_4_RU.md.


# 2026-10-11 - Prealpha 0.6.3 repeated-map trials

Fixed NOPY VM-hook trampoline slot exhaustion across qagame reloads by recycling only successful custom VM hooks. Added guarded isolated trial runner and SHA-checked reports. Final series: 3 Duel + 2 RJ probes, 33 real pickups, 17 strafe command observations, 2 successful RJ, zero integration errors. One full rocket/yellow/Mega opening preserved from preceding 0.6.2 trial; other post-exhaustion trials rejected. MSVC Debug/Release 12/12 CTest; Python 93/93; Linux NOPY built. Experimental RJ sample 1 remains manual-only; probe reset to 0. See docs/PREALPHA_0_6_3_RU.md.


# 2026-10-11 - Prealpha 0.6.2 focused block hardening

Scope frozen to item navigation/selection, strafejump, rocketjump and existing openings. Failed demo approach now retries the same item with stock AAS before abandoning it. Real QL test: railgun collected 2225 ms after fallback; 16 actual pickups, 16 strafe command observations, no RJ in this run. Corrected pickup audits to exclude hook-install diagnostics. MSVC Debug 12/12 and Python 92/92 passed; Linux NOPY built. Status and remaining tests: docs/FOCUSED_BLOCK_STATUS_RU.md. These blocks are NOT fully complete.


# 2026-10-11 - Prealpha 0.6.1 opening overlay

36 observed Blood Run opening orders connected to the native test-only goal selector. Real match phase with VM-reload handling; actual pickup advancement, recovery/death/unavailable/timeout fallback. MSVC Debug 12/12 CTest; Python 92/92; Linux NOPY build. First live order picked yellow and Mega, then aborted unavailable third goal. All 36 variants are not live verified. See docs/PREALPHA_0_6_1_RU.md.



2026-10-11 opening audit: first 30 seconds anchored to UDT match starts; first weapon/three strategic pickups, continuity and missing-start flags. No runtime policy change. See docs/OPENINGS_RU.md. Four focused tests passed.
Prealpha follow-up: normalized native header whitespace; no executable behavior changed.

# 2026-10-11 - Prealpha 0.6: live Blood Run navigation

Native test-only QL adapter now executes item selection, observed demo approaches, bounded strafe jumps and one live-validated rocketjump. 257 approach windows / 22 destinations and 16 owner RJ observations are in the generated bank; only RJ sample 0 is autonomous-enabled after 3 live probe successes. Stock AAS and combat remain. Includes actual Touch_Item pickup evidence, target-stack synchronization, failed-route cooldown, binary pins and isolated 27961-only gating. Main 27960 untouched. See docs/PREALPHA_0_6_RU.md and docs/training/PREALPHA_0_6_VALIDATION.json. Validation: MSVC Debug 12/12 CTest, Python 84/84; Linux NOPY build and real QL observations. Full Mind map and full C++ Behavior integration are NOT complete.

# 11.10.2026 ? ?????? ???? ????????? ? Behavior

???????? verified ExactOpponentStack ? ?????????? ?????/?????/????? ? TTL; ??????? ?????????? ????? ?????? ?? ??????????????, ????? ???????? ? ?????? ????????????? ????. ??????????? ?????? ??????? ???????. MSVC Debug11/11 CTest ??????. docs/EXACT_STACK_IMPLEMENTATION_RU.md. Live HP/armor sensor ? ?????? item timer registry ??? ???????????; ??????? ?? ??????????.

# 11.10.2026 ? ?????? ??????? ???? ????????? ? ???? ?????????

???????? ??????? ?????????? ?????? item timers ? HP/armor ?????????, ??????? ??? ?????????. ??????? ?????? ???????? ????? ???????; ?????? ??????? ????????? ???????????. docs/EXACT_TIMERS_AND_STACK_RU.md ?????? ????????????, ?????, ??????? ??????? ? ??????? ?? ????????/???. ??? ???????? ?????? ???????, ?? ??? ???????????? ???????. SPEC ????????; ???/?????? ?? ??????????.

# 11.10.2026 ? ?????? ??? ?????????? ??????? ???? QL

???????? opt-in read-only native observer ???????0x2c920, ???????????? ???????????27961/mode3, fingerprint ? ???????????? SHA256-???????? ????????????. ???????? ??????? ???????????????? ????????; layout ?? ???????????, ?????????? ?????????. MSVC Debug10/10 ????? CTest ?5 Python-?????? ??????; ??????????? ???????? ?? ????????? checkout. docs/STOCK_GOAL_OBSERVER_RU.md. ???????? Linux ABI/goal identity/pickup ??? ?? ????????????, ???? ? ??????? ?? ??????????.

# 11.10.2026 ? ????????????????? ????? ? ???????? ????? ? AAS

??????? 297 ?????? QL ?? SHA256, ????????? 146 botfiles ? 79 ????????? workshop-??????. ??????? ???????? ?????? Q3/BrainWorks; ???????? ????????? ?? ??????????? ????????? ????????????????. tools/associate_demo_aas.py ?????? 17927 ???????? ?? 125 Blood Run ? AAS:841 ??????????? ???????,590 ??????????? ?????????????? ???????????????????.2392/2392 ?????? ???????? ?????????? ???????.21 Python-???? ?????? (8 ?????). docs/BOT_REUSE_AND_BLOODRUN_PLAN_RU.md ???????? ?????? ???????, ???12 ?????? Mind map, ??????? ????????????????? ? ????????? ??????? goal?mover?pickup ??????. ?????? ?? ????????? ? ??????????; C++ ? ??????? ?? ??????????.

# Аудит систем ботов — 2026-10-10

- В `docs/BOT_SYSTEMS_AUDIT_2026-10-10_RU.md` сопоставлены штатные данные/частично исследованный бинарный AI Quake Live, открытая Q3-родственная botlib архитектура, все семь Workshop PK3-наборов и отдельно ZZZ.
- Ясно разделены декларативные профили персонажей и исполняемая логика движка; собрана таблица функций/наблюдений, которые подтверждены, доступны только в Q3-источнике или пока остаются гипотезой для retail QL.
- Сводная оценка: изученность источников около 70%; пригодность демо/данных для ручной настройки около 35%; готовность полной игровой реализации около 25%. Оценки ориентировочные, критерии приведены в отчёте.
- Следующий кандидат на обсуждение — read-only наблюдение за штатной целью/командой/подбором без перехвата решений. Никакой кодирующий или игровой этап этим не разрешён.
- Изменялись только `README.md`, `CHANGELOG.md`, `PROJECT_STATE.md`, `docs/LOGIC_RECONCILIATION_RU.md` и новый документ аудита. Сборки, тесты, игровые серверы и конфигурации не запускались/не менялись.

# 10.10.2026 — локальная копия штатных файлов QL

Рядом с аналогами сохранён QL_Stock_2026-10-10:297 файлов (146 botfiles,149 AAS,2 бинарника),157061688 байт. CRC/SHA256 проверены. Состав и ограничения — docs/STOCK_BOT_RESEARCH_RU.md. Чужие файлы вне Git; основной сервер не изменён.

# 10.10.2026 — разбор штатного бота и AAS Blood Run

Декомпилирована функция выбора предметной цели qagame (0x2c920), сопоставлена с Q3. Прочитан штатный bloodrun.aas:2393 области/2723 перехода; добавлен tools/read_stock_aas.py с проверками структуры. docs/STOCK_BOT_RESEARCH_RU.md. Бинарники/псевдокод/граф локально в ignored out. Запись целей и игровое подключение не выполнены; основной сервер не изменён.

# 10.10.2026 — база100 демок Blood Run

По команде владельца с demos.quakelive.ru скачаны100 уникальных Duel dm91:191181814 байт,100 фактически bloodrun,2223271 снимок и14840 окон подходов. Введена проверка следования наблюдателя через pm_flags, свободная камера исключена. Старый пакет170 файлов проинвентаризирован;25 стандартных Blood Run разобраны,3087 дополнительных подходов; bloodrun_duel отделён. Архив9207 сохранён отдельно после отказа sanity-check HP и заменён.35 Python-тестов прошли. Реестры/SHA/инструменты в Git; сырые демки/сжатые траектории локально, вне Git. docs/BLOODRUN_CORPUS_RU.md. Это база наблюдений, не подключённое игровое обучение.

# 10.10.2026 — навигационный проход по новой команде владельца

Тест27961 снова запущен по прямой команде изучать карту. Режим3 записывает собственное движение штатного AAS-бота без подмены команд. Первый снимок:370 состояний/73.8с,212 пространственных ячеек/262 перехода; экспериментальный граф и поиск кандидатов, не проверенная live-навигация.5 тестов анализатора прошли. docs/NAVIGATION_EXPLORATION_RU.md. Приоритет — карта и пути, RJ отложены. Основной27960 не изменялся.

# 10.10.2026 — подход к ресурсам и подтверждение подбора

Добавлен ResourceApproach в C++ core: Approach/AwaitPickup/Complete/Replan, проверка собственного события, этажности, контекста и таймаута. Из ZTN извлечено11 наблюдаемых подходов к подборам; физика/геометрия не проверены, исполнение отключено. Документ docs/RESOURCE_APPROACH_MODULE_RU.md. MSVC Debug9/9 групп, Python20 тестов прошли. Сервер не запускался. Live-сенсор/связка маршрута с native остаются следующим этапом.

# 10.10.2026 — тестовый сервер остановлен по команде владельца

Контрольная лаборатория27961 завершена через quit после проверки PID/home/порта. Отсутствие процесса и UDP27961 подтверждено; основной27960 и quakelive.service работают. Лог сохранён на сервере и локально out/control_lab/stopped_control_lab.log. Обратная связь владельца: нет осмысленного ориентирования, выбора оружия и сбора ресурсов. Проверка базовых команд остаётся действительной, но не является готовностью игрового бота. Приоритет локальной разработки — карта/маршрут, оружие и подборы; не запускать новый игровой тест без команды владельца.

# 10.10.2026 — реальное управление на тестовом сервере

Новый отдельный этап по команде владельца: собран native ClientThink_real hook на изолированной копии minqlx NOPY. В игре подтверждены остановка, forward, command angles и обычный jump/landing: 50 отсчётов, docs/CONTROL_LAB_RESULT_RU.md. Координаты/скорости не подменялись. Тест27961 запущен в лабораторном режиме2, основной27960 не изменён. Прежний статус «нет никакого исполнителя» уточнён: базовый путь доказан, общий адаптер/attack/weapon/RJ ещё не готовы. Рокетджамп по демке не заявляется.

# 10.10.2026 — анализ учебной демки ZTN

Сохранена отдельная неизменённая копия демки; добавлены tools/audit_rocketjumps.py, 9 тестов и docs/training/ZTN_solo_01_rocketjumps_RU.md с JSON. 25 меток: 15 кандидатов с повышением, 1 с подбором рейлгана без повышения, 13 неудачных, 2 выстрела исключены, 1 метка без выстрела. Числа относятся к кинематическому анализу, не игровому исполнению. Параметры окон/допусков и ограничения HP явно описаны. Сервер и игровая логика не изменялись.

# Дополнение адаптации10.10.2026 — текст обработан

Создан docs/OPPONENT_ADAPTATION_SPEC_RU.md, исходник сохранён вlogic_archiveсSHA256. Уточненысовокупностьпризнаков/3окна/удержание/уверенность, читаемые привычки противслабого, борьба противсильного, подготовленнаяконтратака100/100и70–110как оценка, позиционная«Крыса», равныеразменыбеззапретафрагов, взглядпозадаче/сюрпризы. Полныйконтрольредокотдельно отобычногострогого; прежниеpressure_escape/tilt/forfeitнеудалены.

Подробностиподстройкивынесеныизспецификациисложностиводинтекст, исходные153IDсохраненыбезповторов. Описаны12QA-ADAPTсценариев/полядиагностики/параметрыбеззначений/нужныедемки. Онине реализованы и не запускались. Вконцевложенияестькомандалокальнойреализациипристаромрежиметолько-текст; задануточняющийвопрос, ответожидается. Код/config/tests/сервернеизменены. GitHuboriginотсутствует.

# Дополнение сложности10.10.2026 — только текст

Создан docs/DIFFICULTY_ADAPTATION_SPEC_RU.md: пять предварительных профилей, адаптация внутри каждого без открытия запрещённых действий, отдельные параметры семи оружий, границы качества движения/решений/контроля. L3:1–2возможныхspawntrap-эпизода, длина серии до2–3отдельно,0допустимо; частота4–5ещё не утверждена. Низкая сложность не технические сбои. Старт3/между картами±1ссогласием сохранены.

Обновлены ссылки и пробелыC13/F07–F09/I01/L01–L12 без дублирования153пунктов. Описаны11QA-сценариев, включая5×4типа соперника; код/конфиги/тесты не менялись и не запускались. Блокер usercmd, sports parser и L11Relaxed не исправлены этим текстом. Сервер не использовался. GitHub origin отсутствует.

# Текстовый аудит10.10.2026 —153 исходных пункта сверены

В docs сохранены исходная PNG A–L, два полученных задания с SHA256/датами, рабочая текстовая схема LOGIC_MAP_RU.md, LOGIC_RECONCILIATION_RU.md, таблица REQUIREMENTS_TRACEABILITY_RU.md (153 исходныхID +11 новых требований; НЕ153 реализованных функций), GAME_BASICS_SPEC_RU.md, GUIDE_AUDIT_2026-10-10_RU.md. Пять руководств прочитаны, включая обе части тайминга. В ходе работы получена папка bot logic (by nekitz0r): полныйguide153/SVG/OPML/PNGv3/PPTX/HTML/архив переписки. Неизменённая копия помещена вdocs/logic_archive/owner_package_2026-10-10, SHA256 проверены;153ID guide совпали сOPML.

Центральная цель обновлена текстом: подстройка внутри1–5, читаемые ошибки и интересные дуэли без искусственной выдачи/спасения/отказа добивать. Отмечены неподключённые counterpush/«Крыса», неполная оценка силы, чрезмерное отключение сбора Relaxed, неутверждённые числа/частоты, временные pressure exits. C1давление/контратака,C2строгий/тотальный контроль,C3честные ошибки/tilt-forfeit иC4привилегии/no-WH перечислены с предложениями без изменения кода.

Блокер: абстрактный GameInterface без retail usercmd реализации, углов/ground и арбитража stockAI; собственное состояние читается исторически подтверждённым probe. P1кандидат — серверный бот, не подключённый клиент. Сейчас только текст, SSH/сборка/игровые тесты не запускались. Test27961 остаётся остановленным по последней подтверждённой проверке09.10. Кодирование/развёртывание требуют команды. Дополнительные пробелы: взаимныеsports repliesK02/K03 отсутствуют; L11не учитывает намеренныйRelaxed отдельным флагом. GitHub origin отсутствует; этап сохраняется локальным коммитом.

# Тест завершён, изолированный экземпляр остановлен — 2026-10-09

Владелец вышел и сообщил о неудовлетворительной игре: нет чата/RJ, слабый сбор предметов/движение, преимущественно перчатка; после 20+ фрагов использовал рейл/шафт. Подробный фактологический отчёт: docs/PLAYTEST_FEEDBACK_2026-10-09_RU.md. Это тест штатного профиля, не новой C++-логики. Подтверждены bot_nochat=1 и только read-only probe plugin, command_sent=false. Логи не содержат структурированной истории Kill/Item; отзыв не подменён измерениями.

Архив console/final console/последнего probe/manifest сохранён на сервере и локально out/playtests/20261009T195453Z, SHA256 копий проверены; сырые логи в Git не включены. По окончании просмотра остановлен только test PID129743, UDP27961 больше не слушает. Основной quakelive.service active, UDP27960 работает. Следующий приоритет — доказанный исполнитель команд и полноценная телеметрия, затем подключение чата/модулей; новых игровых исправлений в этом этапе нет. GitHub origin отсутствует.

# Серверная проверка после перезапуска — 2026-10-09

По отдельной команде владельца разработка приостановлена, проверен доступ по SSH. Последний код 0.5.0, commit bc68587, загружен в отдельный /home/qlserver/psyz0r-bot/releases/bc68587; SHA256 архива 7e6b710b2bd098ea3632fc2e599712ded87c3fde1aca6c32650538df2346bb5e. GCC/C++17: все 6 тестовых программ собраны и прошли. Python: 42 теста, 5 пропущены, остальные прошли; пропуски не считаются проверенными функциями.

Изолированный экземпляр на UDP27961 продолжает работать: bloodrun/FFA, Psyz0r_bot slot0, connection_state=4, свежий probe с own_state_verified=true, command_sent=false. Бот уже присутствует, повторный addbot не отправлялся. Основной quakelive.service active, его конфигурация и штатный бот в этом этапе не изменялись. Подключение: connect 78.17.9.235:27961.

Это проверка профиля и чтения собственного состояния. Live экземпляр использует штатную логику профиля; загруженный C++ core остаётся автономной сборкой без retail usercmd executor. Новый мувмент, состояния поведения, адаптация и событийный чат в игру не подключены. Нельзя считать их проверенными этим матчем. После сообщения владельца об окончании теста остановить только изолированный экземпляр; главный сервер оставить. GitHub origin отсутствует, публикации не было.

# Текущий этап0.5 — 2026-10-09

Подробная добавка движения сохранена в docs/MOVEMENT_REQUIREMENTS_RU.md; русский гайд и аудит — docs/MOVEMENT_LEARNING_GUIDE_RU.md. Изучены доступные тексты injx/Yakumo и Markdown-копии; Delta FAQ robots-blocked, полный текст не заявляется изученным. Работа локальная, тестовый/основной сервер не изменялись. Предыдущее указание убрать тестового бота после сообщения владельца об окончании просмотра сохраняется; такого сообщения пока нет.

В общем C++ core добавлены MovementController (movement.hpp/.cpp + movement.ini) и RoutePredictor (route_prediction.hpp/.cpp + route_prediction.ini). Существующий sandbox передаёт Decision в движение, пишет movement proposals и game_command_sent=false. Контроллер требует verified собственного state/view/geometry/corridor, ограничивает время/поворот, учитывает тихий/быстрый отход, завершение waypoint и replan при ошибках/пропусках/неподтверждённом прыжке. Single/half beat — только локальная схема с externally measured Classic параметрами, не успешная распрыжка QL. Рокет/plasma/circle полноценные манёвры пока отсутствуют. RoutePredictor — ограниченная история только воспринимаемых зон, ≥3 повторения, timing tolerance, TTL/decay; не скрытое слежение и не автоматический перехват.

Расширен существующий tools/extract_movement.py: game-state эпоха, собственные stats/ammo и события выстрела. tools/demo_learning.py экспортирует чат, выделяет окна по #bot/sidecar, не пересекает death/POV/teleport/gap, отмечает остановки с role=null и неизвестные показатели. Реальная bloodrun dm_91:24551 snapshots,489 WeaponFired,один чат совпал по времени с финальным POV snapshot; #bot отсутствует, размеченных эпизодов0,кандидат остановки1. Исходный SHA сохранился. out/demo_learning/bloodrun/episodes.json. Физика в этом запуске заявлена, не измерена; net HP delta не является доказанным selfdamage.

Проверки этапа: MSVC/CMake,6/6 CTest,42/42 Python tests, реальный одно-демковый экспорт. Главный следующий блокер — native usercmd и измеренный результат; затем одиночная размеченная bloodrun пробежка/один RJ с известной физикой. Исполнительные difficulty profiles/проценты точности не включались. GitHub origin отсутствует.

# Предыдущий этап 0.4 — 2026-10-09

По последнему указанию владельца проверен тестовый экземпляр для одного игрового просмотра: процесс активен, status — Psyz0r_bot slot0, bloodrun/FFA27961, probe обновляется, основной service active. Бот пока оставлен для игры; убрать/остановить только изолированный тест после сообщения владельца об окончании. Нового развёртывания/рестарта не было. В docs/MODULES_MOVEMENT_NOTES_RU.md сохранено понимание разделения движения/стрельбы/оружия/контроля/триксов/поведения/чата. Детальная новая добавка по мувменту ещё не получена. Этот этап — документация и проверка состояния, не новые игровые механики.

Новые требования движения/стрельбы/оружия/макроигры сохранены в docs/NEW_REQUIREMENTS_RU.md; раздел 14 и все старые/новые условия объединены в docs/BOT_LOGIC_GUIDE_RU.md с аудитом статусов и границ. Разработка снова локальная, сервер в этом этапе не менялся. pressure_retreat принят как смысловое название pressure_escape без второго автомата.

Реализованы DifficultySession и config/difficulty.json: старт3, оценка полноценной дуэли, предложение±1 в диапазоне1–5, исключение forfeit/намеренного тильта/недостатка данных, явное согласие, применение только на следующей карте. Однократный вопрос встроен в существующий ChatPolicy и cooldown; при leaving вопроса нет, автозапуска/кика нет. Уровень текущего матча фиксирован. Профили исполнения предварительные, execution_enabled=false, accuracy/error=null до согласования. Сохранение уровней между рестартами процесса ещё отсутствует.

C++: прежнее автоматическое назначение FullControl при отставании заменено однократным шансом .15 против сильного в нормальном состоянии; lead_tilt_probability теперь .12 по новому ориентиру владельца. ItemMemory сохраняет подтверждённый точный таймер отдельно от наблюдаемого прогноза при включённой привилегии. Live-получение таймеров/управление/сенсоры не добавлены. Подробные новые модули и таблица ухода описаны как план, не готовы физически.

Проверки: MSVC/CMake, 4/4 CTest, 35/35 Python tests; tools/replay_difficulty.py пишет синтетическую демонстрацию в out/difficulty_trace.jsonl без команд игре. Следующий обязательный барьер — native usercmd исполнение + реальные сенсоры, затем размеченная одиночная пробежка и проверка маршрута/RJ. GitHub origin по-прежнему отсутствует.

# Предыдущий этап 0.3 — 2026-10-09

Сводный отчёт по всем требованиям и готовности сохранён в docs/STATUS_REPORT.md. Исправлена устаревшая запись README о неразвёрнутом пробнике. Текущая граница: чтение собственного состояния подтверждено в QL, политика поведения/чат проверены локально, исполнитель команд нашего ядра ещё отсутствует. Этот этап меняет только документацию; повторные игровые тесты не проводились.

Последняя проверка: выполнен map_restart на тестовом порту 27961; бот остался подключён в slot 0, собственное состояние подтверждено. Основная служба active. Тест всё ещё bloodrun/FFA на штатном AI; управление C++ ядром не заявляется.

Владелец подтвердил подключение и видимость бота. Последующий серверный status содержит только бота; активное присутствие человека ещё не подтверждено серверным снимком. Профиль/собственное состояние работают, управление C++ решениями остаётся следующим обязательным этапом.

Последняя команда владельца разрешила серверные работы: отдельный bloodrun/FFA экземпляр запущен на 78.17.9.235:27961, home /home/qlserver/psyz0r-bot/test-8469e5f. Загружен профиль Psyz0r_bot; player_info подтвердил активный slot 0, probe получает собственное состояние. В игре пока штатный AI с профилем, не наш C++ контроллер. Четыре C++ тестовые программы прошли GCC. Основной сервер и файлы штатного бота сохранены. Детали/остановка в docs/SERVER_STAGE.md. Предыдущее локальное ограничение ниже относится к завершённому этапу до новой команды.

Проверки: MSVC/CMake сборка, 4/4 CTest группы и 23/23 Python tests прошли; журнал C++ реально воспроизведён существующим ChatPolicy, только офлайн.

Работа локальная; сервер не изменялся в этом этапе. Новые реакции/pressure_escape реализованы в ядре и покрыты сценариями, чат подключён к журналу решений офлайн. Live usercmd, LOS/навигация, damage/corpse sensors и транспорт в minqlx не реализованы. Подробности и запуск: docs/EVENT_REACTIONS.md, docs/PRESSURE_ESCAPE.md.

Демки: извлечено по 24551 snapshot из bloodrun/sinister против PsyRoZ, POV nekitz0r. Match-aligned подходы: bloodrun 4 mega/2 red/18 yellow, sinister 6/7/21, всего 58. Совпали с playerStats. Суммы оригиналов сохранены; sinister PS ring потерял восемь событий неизвестного типа. Артефакты out/demo/*_movement.jsonl, *_routes.json/.csv. Следующий приоритет — ручная проверка маршрутов к Меге/арморам и map geometry, не копирование координат без навигации.

Нужно далее: согласовать окончание условий выхода pressure_escape; проверить собственные сенсоры/управление на отдельном сервере после команды владельца; добавить карты/безопасные маршруты и реакцию на отклонённую команду выстрела; определить команды жизненного цикла, сохранив штатного бота. GitHub публикация пока отсутствует, локальный Git сохраняет этап.



﻿# Состояние — 9 октября 2026

Актуальная новая папка рядом с исходной: C:/Users/user/Desktop/Quake SERVER/Project_Psyz0r_bot. Исходная PsyZ0r-bot и её вложенный проект не изменялись. Официальное имя Psyz0r_bot.

## Подтверждено локально

Последнее ограничение владельца: разработка локально, дальнейшая выгрузка и игровые тесты только по отдельной команде. До уточнения по предыдущему разрешению создан изолированный экземпляр /home/qlserver/psyz0r-bot/test-home (порт 27961, собственный профиль с namespaced includes и read-only probe). Теперь он остановлен; папка сохранена. Основная служба не перезапускалась, room_bot.py и server.cfg сверены с исходными SHA-256. Read-only плагин загрузился в тестовом экземпляре, но своего игрового состояния бота и исполнения usercmd ещё не подтвердили. Следующие изменения не загружать автоматически.

Инструкция запуска владельца проверена: run_server_x64.sh — vanilla, run_server_x64_minqlx.sh — с расширением; server.cfg содержит bot_enable=1. quakelive.service уже active, второй экземпляр не запускался. Правильный каталог и ручной запуск остановленного экземпляра записаны в docs/SERVER_STAGE.md.

MIT выбрана владельцем и добавлена в LICENSE. SSH к quake-admin работает. Версия b915d36 размещена отдельно на сервере в /home/qlserver/psyz0r-bot/releases/b915d36-20261009T150921Z; GCC сборка, две C++ группы и 11 тестов чата прошли, четыре Windows-oriented теста на Linux пропущены. Активная служба/конфиг не менялись: текущий bot state показывает human_count=1. RCON status пока без ответа; исполнение игровых команд не проверено. Подробности docs/SERVER_STAGE.md. Отсутствие ответа RCON не считается доказательством отсутствия игроков.

Подготовлена открытая разработка: локальный Git main, CHANGELOG, CONTRIBUTING, AGENTS и GitHub Actions Windows/MSVC + Python. Публикация не выполнена: origin отсутствует, целевой репозиторий и лицензия собственного кода запрошены. Чужие исходники, ресурсы, бинарники и демки исключены из Git; источники и версии сохраняются в references/manifest.json.

Актуальное обновление: реализована автономная политика трёх стилей, накопления урона/наблюдений, предметных целей, давления, расслабления, обоих тильтов и ответных corpse/gauntlet. Сдача: пробная вероятность 0.10, дефицит >=5, own score <=0, серия смертей >=3, длительность 0 до конца матча. Один выбор вероятности за матч; случайные фраги не отменяют состояние. Все действующие настройки core.ini; детали docs/BEHAVIOR_IMPLEMENTATION.md. Две группы CTest и Python-тесты прошли. Серверное исполнение всё ещё отсутствует. Ранние пункты ниже описывают предыдущий этап.

С разрешения пользователя установлены Visual Studio Build Tools 2022 17.14.41, MSVC 19.44.35229, CMake и Windows SDK 10.0.26100.0. После завершения SDK C++17 ядро, sandbox и behavior_tests успешно собраны без предупреждений. CTest проверяет десять условий; восемь Python-тестов чата прошли. Журнал out/build.log.

Пороги sandbox читаются из config/core.ini: проверено, что повышение порога пуша до 95 меняет решение сценария на hold. JSONL журнал проверен, game_command_sent=false. config/behavior.json сохраняет план будущих механик, пока не исполняется.

UDT исходники скачаны в references/uberdemotools; четыре референса скопированы из существующих материалов. URL/commits в references/manifest.json. QuakeLiveInterface повторно скачать не удалось. Чужой код не включён в C++ ядро; licenses сохранены, перед заимствованием нужен отдельный разбор.

tools/extract_one_demo.py проверен на одном dm_91: aerowalk, keFir 20 : @gZ@r 0, один gamestate. Статистика совпала с предыдущим экспортом; SHA-256 оригинала неизменен. Raw mouse/keys не подтверждены.

## Игровой этап открыт

Обязательный прототип с управлением QL ещё не готов. Нет подтверждённого чтения состояния и исполнения пяти действий на отдельном тестовом сервере. Найден retail x86-клиент Quake Live; найденный сервер quake-admin не использован. Запрошен выбор отдельного тестового окружения, ответа пока нет.

WinQLX32: player_state чтение есть, углы взгляда отсутствуют в изученном PlayerState, send_usercmd не найден. SV_ClientThink_ptr только typedef. В Q3 BOTLIB_USER_COMMAND реально вызывает SV_ClientThink, но перенос в retail QL не доказан. Анализ кода и конкретные ограничения в docs/CONTROL_AUDIT.md.

adapter/psyz_state_probe.py — не развёрнутый read-only пробник minqlx выбранного слота, проверен только синтаксис. game_interface.hpp — контракт без исполнителя. Не считать эти файлы рабочим игровым адаптером.

## Продолжение

Получить выбор отдельного тестового сервера. Проверить бинарник/ABI и путь команд штатного серверного бота. Если он недоступен, отдельно исследовать подключённый клиент; не смешивать способы. Испытания: стоящий контроль, движение, взгляд, прыжок, оружие, выстрел — с измерением состояния и остановкой между шагами.

После подтверждения управления расширять накопление стиля, таймеры, счёт, расслабление, оба тильта, corpse/gauntlet и антициклический чат по SPEC.md. Сборка и запуск — README.md. Полный построчный анализ сторонних проектов не заявлен.


## 10.10.2026 — дополнение офлайн-проработки

Контракт docs/OFFLINE_DECISION_CONTRACT_RU.md дополняет основы игры и аудит пяти источников: 24 правила и 16 запланированных сценариев. Это документация, не работающий навык. Следующий программный приоритет — подтвердить исполнение команд и измеримый результат, затем фактические правила и один маршрут/RJ; кодирование и серверные испытания отдельно. Чужие незавершённые изменения сохранены. Локальная публикация только: remote не настроен.


## 10.10.2026 — локальное кодирование предикта разрешено и начато

CombatPredictor включён в ядро: прогноз по видимым отсчётам и математическое упреждение. Проверено MSVC x64 Debug, 7/7 CTest. Это вычислительный модуль, не рабочая стрельба в Quake Live; нет geometry/splash/skill aim и live wiring. Далее геометрическая проверка и контроллер прицела/выстрела, затем связь с RoutePredictor. Точность и серверный этап отдельно согласуются. Подробности docs/COMBAT_PREDICTION_RU.md. GitHub remote отсутствует.


## 10.10.2026 — готовые локальные сборки

Debug и Release сохранены в out/msvc-x64; обе конфигурации прошли 7/7 CTest. Release стенд выдал 3 офлайн-записи, отправки игровых команд нет. Журналы out/offline-build, отчёт docs/OFFLINE_BUILD_2026-10-10_RU.md. Это сборки ядра/стендов, не серверный плагин. Следующим остаётся геометрия/контроллер прицела и подтверждение игрового исполнения. Владелец поручил гибернацию после сохранения.


## 10.10.2026 — геометрический фильтр и подготовка доставки

check_shot_path проверяет conservative SolidBox, радиус и дистанцию; unknown/stale блокируются. MSVC Debug/Release: 8/8 CTest. Это локальная геометрия, не BSP/live trace и не автопушка. VS Code открыт. GitHub malosmysla-lang доступен, репозитория пока не видно; SSH quake-admin в стандартной настройке отсутствует. Требуются URL/создание репозитория и путь к SSH профилю; сервер не менялся.


## 10.10.2026 — публикация GitHub подтверждена

Origin: https://github.com/malosmysla-lang/Project_Psyz0r_bot.git. Push main успешен; удалённый SHA fbd4abb071fd187220bc73ce2f65e7a3bd895b53 подтверждён перед записью этого отчёта. main отслеживает origin/main. Рабочие незакоммиченные материалы сохранены локально. Для сервера ещё нужен действующий SSH-профиль/доступ; загрузка не выполнена.


## 10.10.2026 — локально, GitHub и серверный release

Три места хранения подтверждены: локальный проект; origin GitHub; сервер releases/7c76f18 (архив SHA256 совпал). Linux GCC 11.4: 8/8 C++ программ прошли и sandbox выполнен, Python не запускался. SSH ключ доступен через агент, отсутствие key-файла не блокирует доступ. Основная quakelive.service active, настройки не менялись. Дальше только разработка бота: контроллер наведения и выстрела; live executor остаётся неподтверждённым.


## 10.10.2026 — общий снимок проекта

Собраны ранее незакоммиченные собственные документы и схемы. Текстовые ограничения прежних этапов — история; текущая команда владельца разрешает локальное кодирование, сборки и доставку версий. Runtime каждого модуля по-прежнему оценивается отдельно. Три копии сверяются по HEAD и контрольным суммам, правила docs/SYNC_POLICY_RU.md. Работа только над ботом, серверная служба не изменяется.


## 10.10.2026 — расширены основы дуэли

Исследование docs/DUEL_FOUNDATIONS_RESEARCH_RU.md готово. Подтверждены источники классических ориентиров; runtime использует только проверенные правила конкретного режима. Интервалы respawn→damage/death — кандидаты, а не автоматически spawntrap. Позиция атакующего и причинность spawn проверяются отдельно. Следующий блок основ — DuelContext/макрозадачи; в этом этапе код не добавлен.
