# 2026-10-12 - Prealpha 0.6.4 deployed to isolated 27961

Backed up isolated native/config; installed SHA-verified 0.6.4, enabled both navigation switches. Blood Run Duel, 10min, unlimited frags, 120s overtime; only Psyz0r (stock Sarge skill5 base plus custom native overlay), no Xaero. Warmup smoke: 10 actual pickups; red at 38775ms, 2300ms after failed demo route fell back to AAS at 36475ms. One recovery, no RJ in smoke, integration errors see report. Main service unchanged. See docs/training/PREALPHA_0_6_4_SMOKE.json. New PJ/RJ candidates are not enabled actions.

# 2026-10-12 - Red boost analysis, five-second pickup window

Audited 1,416 red pickup events with 8s context and <=5s damage-to-pickup window: 700 candidate approaches, 729 rocket and 97 plasma coincidences (not unique proven self-damage jumps). Added continuity/teleport exclusions, source SHA provenance and four regression tests; Python 99/99. See docs/RED_BOOST_ANALYSIS_RU.md. No new PJ actions enabled.

# 2026-10-12 - Duel Pracc Room square-glyph follow-up

Read-only check of the owner’s new screenshot: the mappool file and mapguard output source contain ASCII map names, with standard Quake color escapes; `qcdm1` is not stored with a square. This adds evidence for a display/runtime-path issue but does not localize it. No server changes or restart. See docs/server/DUEL_PRACC_ROOM_STATUS_2026-10-12_RU.md.

# 2026-10-12 - Duel Pracc Room audit snapshot

Added a provisional, read-only status infographic and Russian evidence summary for the separate Duel server. No server configuration, bot source, or runtime was changed. Counts are explicit item counts, not weighted readiness; match-report freshness and the welcome-square source remain unresolved. See docs/server/DUEL_PRACC_ROOM_STATUS_2026-10-12.svg and docs/server/DUEL_PRACC_ROOM_STATUS_2026-10-12_RU.md. Remaining chat history is still awaited.

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

- Добавлен [подробный аудит stock Quake Live, Q3-родственной botlib архитектуры, Workshop-наборов и доступных функций](docs/BOT_SYSTEMS_AUDIT_2026-10-10_RU.md).
- Разделены исследовательская изученность (~70%), пригодность демо/данных для ручной настройки (~35%) и готовность полного игрового контура (~25%); описана методика этих оценок.
- Код, игровые файлы, конфигурации и серверы не изменялись; сборки и игровые испытания не запускались.

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

# 10.10.2026 — текстовая адаптация к сопернику

- Сохранён исходник дополнениясSHA256, добавлен единыйOPPONENT_ADAPTATION_SPEC_RU.md иобновленысвязи с153IDбезновыхдублирующихтребований.
- Уточненыоценкасилы/стиля, привычкинаэпизоды, контратакаи«Крыса», читаемыеразмены, взгляд/памятьбезслежения; смыслразделениястрогого/тотальногоконтроля.
- Описаны12проверок, диагностикаиподбордемок. Кодированиеуточняетсяиз-законцевойкомандывовложенииприпрежнемтекстовомрежиме; runtime/config/tests/серверне менялись.

# 10.10.2026 — уточнение сложности и внутренней адаптации

- Объединено последнее дополнение владельца сC13/F07–F09/I01/L01–L12: отдельная текстовая DIFFICULTY_ADAPTATION_SPEC_RU.md, без дублирования требований.
- Зафиксированы пределы навыков/отдельные weapon параметры, предварительная градация1–5, независимые лимиты эпизодов/длиныspawntrap и отсутствие квоты.
- Добавлен план11проверок, включая адаптацию5×4и запретыlvl1. Новых тестов/процентов/config/runtime не добавлено; сервер не запускался.

# 10.10.2026 — документация и сверка P0

- Сохранены исходная схема A–L и задания с датами/SHA256; добавлены рабочая текстовая карта и таблица74 временных требований сохранена как история. Затем получен полный пакет: основная таблица содержит153 оригинальныхID и11новых требований, OPML/guide совпадают.
- Последняя центральная цель включена в README/SPEC/гайд; отмечены расхождения Relaxed, слабого/сильного proxy, counterpush/«Крыса», частот и исполнительных профилей.
- Описаны основы игры/фактический overtime и whitelist приседания; конфликтыC1–C4 предложены к сверке, поведение не изменено. Выявлены отсутствующиеsports repliesK02/K03 и неполная защитаL11 от оценки понамеренномуRelaxed.
- Изучены5 текстовых руководств, обе части Memento_Mori; подготовлены карточки с источниками/границами/проверками без переноса исторических чисел.
- Проверка этапа: ссылки/пути/SHA256/таблица/git diff; код, конфиги, сборки и сервер не изменялись. GitHub origin отсутствует.

# Завершение просмотра профиля — 2026-10-09

- Зафиксирован неудовлетворительный отзыв владельца в docs/PLAYTEST_FEEDBACK_2026-10-09_RU.md с отделением наблюдений от измерений.
- Сохранены и проверены по SHA256 серверные логи и последний probe; зафиксирован недостаток истории боевых событий.
- Подтверждены bot_nochat=1, отсутствие интеграции собственного чата и C++ executor. Позднее усиление рейла/шафта не считается проверкой адаптации.
- Остановлен только изолированный тест27961; основной сервер27960 остался active. Изменений игровых механик нет.

# Проверка тестового сервера — 2026-10-09

- По команде владельца загружен отдельный release bc68587 (0.5.0), проверены SHA256, GCC-сборка и 6 C++ тестов; Python 42 теста, 5 skipped.
- Подтверждены работающий основной сервис и присутствие Psyz0r_bot на изолированном bloodrun/FFA27961; свежий собственный state, command_sent=false. Повторное приглашение не требуется.
- Файлы основного сервера не изменялись. Исполнитель новой C++-логики в QL отсутствует; игровая проверка относится к профилю. Разработка приостановлена на время просмотра.

# 0.5.0 — 2026-10-09, локальный этап

- Отдельный MovementController в общем C++ core: прохождение waypoint, короткий command lifetime, rate-limited yaw, quiet/fast escape, блокирование неизвестных state/geometry/physics, replan при отсутствии прогресса и неподтверждённом отрыве. Связан с существующим Behavior в sandbox; команды игре не отправляются.
- Локальная Classic single/half beat схема и расчёт wish direction без назначения Q3 чисел текущему QL. Прогноз воспринимаемых зон по повторениям/темпу с ограниченной историей, TTL и снижением уверенности.
- Расширен UDT snapshot exporter собственными HP/armor/ammo/событиями; новый demo_learning связывает #bot/sidecar с POV и server-time, режет окна по discontinuities, оставляет роли остановок неизвестными. Исходные демки сохранены.
- Проверен экспорт одной существующей bloodrun dm_91:24551 snapshots,489 WeaponFired,один совпавший по часам финальный чат,нет #bot,один кандидат остановки. Ни selfdamage, ни физический успех манёвров не заявляются.
- Русский гайд MOVEMENT_LEARNING_GUIDE_RU.md, исходное ТЗ сохранено отдельно. MSVC сборка,6 CTest групп и42 Python tests прошли. usercmd/LOS/RJ/plasma/circle и полная навигация остаются незавершёнными. Серверные изменения не выполнялись; GitHub origin отсутствует.

# 0.4.0 — 2026-10-09, локальный этап

- По отдельной команде владельца проверено присутствие профиля на тестовом27961 для одного просмотра; он оставлен до сообщения об окончании, основной сервер сохранён. Добавлен docs/MODULES_MOVEMENT_NOTES_RU.md: существующие файлы, будущие модули, связи и критерии настоящего исполнения. Новая подробная добавка по движению ещё ожидается. Проверка документации — git diff --check; код не менялся.

- Аудит и единый docs/BOT_LOGIC_GUIDE_RU.md: все правила, пять уровней, причины адаптации, приоритеты, метки одиночных демонстраций, ограничения и план движения/стрельбы/оружия/макроигры. Новое ТЗ сохранено отдельно; серверные испытания вновь требуют команды владельца.
- DifficultySession интегрирован в существующий ChatPolicy: старт3, однократный вопрос о реванше, ±1 после надёжного результата, применение только после явного согласия на следующей карте, отмена при отказе/уходе/таймауте. gg не является согласием. Forfeit/намеренный тильт не снижают уровень как оценка слабости игрока.
- config/difficulty.json содержит пять выключенных исполнительных профилей; проценты точности и ошибки наведения не применяются до согласования. Реальные HP/урон/физика не меняются.
- C++: редкий FullControl с одним eligible trial вместо автоматического режима при отставании; новый ориентир lead tilt; точные таймеры имеют отдельный источник/разрешение, без раскрытия скрытой живой позиции.
- Добавлены локальные проверки и replay; MSVC сборка, 4 CTest группы и 35 Python tests прошли. Игровое управление новой логикой и развёртывание в этом этапе не выполнялись. GitHub публикация пока отсутствует.

# 0.3 — 2026-10-09, локальный этап

- Добавлен полный отчёт docs/STATUS_REPORT.md: требования, проверенные локальные/серверные результаты, ограничения и последовательность дальнейшей работы. README исправлен по подтверждённому развёртыванию read-only пробника; игровое управление C++ ядром не заявляется. Проверка этого документального этапа — git diff --check.

- По запросу владельца перезапущена карта изолированного теста; Psyz0r_bot подтверждён в игре и пробнике, дубликат не создан, основная служба продолжает работать.

- Сохранено подтверждение владельца о входе и видимости профиля; отдельно отмечено, что последующий status показывает только бота и не доказывает непрерывного подключения человека/работы C++ управления.

- По новой команде владельца подготовлен и запущен отдельный QL test instance 27961, загружен профиль Psyz0r_bot и подтверждено собственное состояние активного слота. Основной сервер/штатный бот сохранены; это пока профиль на штатном AI, не исполнение C++ политики.
- Исправлены PTY console runner и проверка подключения target slot перед player_state. GCC-проверки четырёх C++ групп прошли; UDP путь подтверждён getchallenge, вход клиента ещё проверяется.

- Реакции по соперникам: подтверждённый Gauntlet damage, безопасная попытка добивания, завершение именно Gauntlet kill; три отдельных corpse episodes и односекундный ответ.
- Связь C++ ReactionTrace → существующая Python chat policy, локальный replay и диагностика. Cooldown 20, weapon/item .1/120, Gauntlet .7/30; периодический спам отключён.
- pressure_escape: накопленное давление, восстановление, безопасные предметы/укрытия, подтверждение одиночного rail и отход, отсутствие одновременного forfeit. Выход пока по временным настраиваемым условиям.
- UDT snapshot extraction + ручная очередь подходов к предметам: 58 подходов в двух демках, числа подборов совпали с matchStats, оригиналы неизменны. Мышь/клавиши и готовая навигация не заявляются.
- MSVC сборка, 4 CTest группы и 23 Python tests прошли; проверена офлайн-связь C++ → чат. Добавлены C++ и Python проверки; игровой запуск/загрузка не выполнялись. GitHub origin всё ещё отсутствует.



# История изменений

## 0.2.0 — локальный этап, 2026-10-09

- По последнему указанию владельца дальнейшая разработка локальная, серверные выгрузки/игровые тесты только по отдельной команде. Изолированный экземпляр, созданный по прежнему разрешению, остановлен; подготовленная папка сохранена. Основной room_bot.py и server.cfg не изменены.

- Уточнена инструкция запуска владельца: штатный run_server_x64.sh не загружает minqlx; текущая служба использует minqlx-скрипт, bot_enable уже включён. Инструкция сохранена без изменения работающего процесса.

- Проверен SSH к серверу владельца; создан отдельный версионный каталог и выполнена Linux/GCC сборка и офлайн-проверки. Активный игровой сервер не изменён; детали docs/SERVER_STAGE.md.

- Владелец выбрал MIT для собственного кода; добавлен LICENSE. Разрешён SSH-доступ к серверу quake-admin для тестирования.

- Добавлены накопление наблюдений и урона, переключение трёх стилей, давление по счёту и предметные цели.
- Реализованы расслабление, потеря преимущества в тильте и независимая сдача через поведение с настраиваемыми условиями, шансом и сроком.
- Добавлены ответные цели перчатки и добивания видимого трупа, память воспринимаемых подборов.
- Чат принимает mood из C++ журнала и ограничивает ответную грубость, дубликаты и циклы.
- Настройки загружаются из core.ini с проверкой значений; настроены CMake/MSVC и локальные тесты.
- Подготовлены GitHub Actions и правила ведения открытой разработки. CI на GitHub пока не запускался.

Проверено локально: сборка MSVC, две группы CTest, 15 Python-тестов. Игровое управление и человеческое движение ещё не подтверждены.

## Предыдущие этапы — восстановлены по рабочим материалам

- Собраны концепция, реплики и референсы; выполнен анализ структуры bot profiles и ресурсов.
- Выполнен экспорт статистики демок; отдельно проверена одна dm_91 с сохранением SHA-256 оригинала.
- Создан отдельный C++ проект рядом с исходной папкой; установлены Build Tools, подготовлены SPEC и журнал решений.

Эти записи описывают выполненную работу. Отдельных Git-коммитов прошлых состояний до создания репозитория не было; история не реконструируется искусственно.


## 10.10.2026 — локальный контракт решений

Добавлен docs/OFFLINE_DECISION_CONTRACT_RU.md: 24 карточки, 16 сценариев будущей приёмки, приоритеты конфликтов, границы данных и последовательность реализации. Документационный этап: исходники, конфиги, сборки и сервер не менялись. Сценарии не запускались. GitHub remote отсутствует.


## 10.10.2026 — первый C++ модуль боевого предикта

По новой команде владельца начато локальное кодирование. Добавлен CombatPredictor: видимые наблюдения, линейный прогноз, перехват прямолинейным снарядом, задержка запуска, эвристическая уверенность и fresh-LOS hitscan. Добавлены тесты и docs/COMBAT_PREDICTION_RU.md. MSVC Debug: 7/7 CTest прошли. Автовыстрел/игровой исполнитель не подключены, сервер не менялся.


## 10.10.2026 — офлайн-сборка Debug и Release

Собраны MSVC x64 Debug/Release, CTest 7/7 в каждой конфигурации. Release sandbox: 3 JSONL записи, все game_command_sent=false. Отчёт docs/OFFLINE_BUILD_2026-10-10_RU.md; бинарники/логи только в out. Сервер не запускался, GitHub remote отсутствует.


## 10.10.2026 — проверка геометрии снаряда

Добавлены shot_geometry и 16 проверок, включая связь с CombatPredictor. Debug/Release: 8/8 CTest. Документ docs/SHOT_GEOMETRY_RU.md. Подтверждён GitHub аккаунт, но origin/SSH профиль требуют настройки владельца; публикация и загрузка не выполнены.


## 10.10.2026 — GitHub подключён

Настроен origin https://github.com/malosmysla-lang/Project_Psyz0r_bot.git; main опубликована с существующей историей (21 коммит до этой записи). Проверка шаблонов секретов не дала совпадений. Незакоммиченные изменения не опубликованы. Серверная загрузка остаётся отдельным незавершённым пунктом.


## 10.10.2026 — серверная автономная копия бота

SSH через существующий агент работает. Release 7c76f18 загружен с SHA256-проверкой; GCC: 8/8 C++ тестовых программ прошли, sandbox выполнен. Предупреждения старых тестов Event зафиксированы. Отчёт docs/SERVER_RELEASE_2026-10-10_RU.md. Основная игра не менялась; переработка сервера отложена, работа только над ботом.


## 10.10.2026 — полная синхронизация отслеживаемого проекта

Включены оставшиеся требования адаптации, таблицы связей, настройки редактора и исходная папка схем владельца. Проверка SHA256 manifest: 0 расхождений. Добавлен docs/SYNC_POLICY_RU.md: полный git archive, server commit marker и Git bundle; секреты/сторонние загрузки/демки остаются вне публичного исходника.


## 10.10.2026 — смысл и правила дуэли

Изучены четыре источника без технического разбора мувмента/стрельбы. Добавлена DUEL_FOUNDATIONS_RESEARCH_RU.md: правила,25/35/5, философия владельца отдельно от статистики, стратегические оси и критерии демо-прогонки. Обновлена связь с GAME_BASICS. Код и серверная игра не менялись.
