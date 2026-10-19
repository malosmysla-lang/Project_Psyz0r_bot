# 2026-10-19 — prealpha 0.7.8: two fresh duel failures and live fixes

Серверная копия исходников, Git-дельты и evidence (две свежие дуэли + demo0000 + снимки/логи) сверена по SHA-256: /home/qlserver/psyz0r-bot/research-releases/078-20261019T183508Z-b8325fb. Квитанция: docs/training/RELEASE_078_BACKUP.json.

Сохранены и разобраны две свежие демки (1:29, 3:13; у бота RA=1/Mega=4 в каждой), данные сверены с правильной эпохой лога. Убрана остановка при защитном MG-огне, повышены свободные Mega/RA, добавлен независимый motion-watch, управление привязано к имени/bot flag вместо слота 0. Восстановлена боевая база Xaero 5 и отдельная ошибка каждой пушки; диапазоны победителей ±7.5 п.п. Чат RU/EN по идентичности клиента и повторные короткие ответы. Найден demo0000 с GL/plasma и кругом ресурсов. Windows 17/17, Python 121/121, Linux 5/5. Только тест27961, backup четырёх файлов; main PID415921 сохранён. Smoke80с: 17 подборов, RA1, Mega0, LG1, fatal=false; не полная победа и не подтверждение распрыжки. Подробности docs/PREALPHA_0_7_8_RU.md; Mind Map v8 273 правила и standalone HTML.

# 2026-10-19 — 0.7.7 offline tactical research

Проверена отдельная серверная резервная копия исходников/истории/500 отчётов (SHA-256). Новые две политики дополнительно прошли GCC/Linux с -Wall -Wextra -Werror. Уточнено определение preaim: максимальное отклонение от угла выстрела, а не полный диапазон углов. Квитанция: docs/training/RESEARCH_077_BACKUP_RECEIPT.json.

Разобраны 500 демок (0 ошибок): 1938 multi-weapon окон из 3771, 80 кандидатов направления прицела и стратегические цепочки ресурсов. Добавлены локальные combo/arrival политики без замены штатного AI и без live-подключения: 12 и 10 сценариев соответственно. Python 118/118, CTest Debug 17/17. Mind Map v7 сохраняет прежние 252 ID и содержит 262 правила; обновлена панель Tabler Dark и плакат 6000×8001. Во время игр владельца runtime 0.7.6 и cfg не изменяются; на сервер сохраняется только отдельный архив исходников/аналитики. Полный отчёт: docs/TACTICAL_RESEARCH_077_RU.md.

# 2026-10-19 — Prealpha 0.7.6 и аналитика Tabler

Подключены исправления близких застреваний и раннего ухода к RA, обновлены чат и редкий guarded-forfeit. 15/15 C++, 111/111 Python, 3/3 Linux. Smoke 65с: 10 подборов, RA1, 2 шага дебюта, 2 восстановления; LG не проверен огнём. Тест27961 обновлён, основной PID415921 сохранён. Mind Map v6:252 правила, все прежние ID сохранены; локальная Tabler-панель. Свежий разбор500 топовых и265 локальных демок. Подробности: docs/PREALPHA_0_7_6_RU.md.

# 2026-10-19 — восстановление локального проекта

Восстановлены Git-история и серверные исходники 0.7.5; сохранён отдельный снимок 5138 серверных файлов. Восстановлены оригинальные демки и инструменты анализа; профессиональный корпус восстановлен: 900/900, всего с демками владельца 1164 уникальных оригинала. Debug CTest 14/14, Python 105/105, контрольный UDT-разбор завершён. Игровой деплой не выполнялся. Ограничения восстановления и утраченные черновики: docs/RECOVERY_20261019_RU.md.

# 2026-10-19 — Mind Map v5 и LG от ног

Обновлены все графические разделы: 233 правила, сохранены 198 прежних ID; PNG 4K/100 dpi, сводка 4096×2048, полный SVG, OPML, HTML, JSON и SHA-манифест. Добавлены новые требования мести/сильного профиля, результаты 0.7.4, визуальная логика LG и отложенная WEB-панель. Проверки: полнота ID/OPML/SVG/листов, границы карточек, UTF-8, визуальный просмотр. Это выпуск документации, без нового игрового деплоя. См. docs/mindmap_v5/README.md, docs/LG_FOOTWORK_REVIEW_20261019_RU.md и docs/LOGIC_UPDATE_POLICY_RU.md.

# 2026-10-19 — требования владельца и месть перчаткой

Добавлен docs/OWNER_REQUIREMENTS_20261019_RU.md и ссылки в 15 рабочих MD. Зафиксированы сильный тестовый профиль, накопленный урон 50/100/150 без обязательного убийства, ответ в чат, добивание low HP и комбо против MG-респауна. Прежние ветки сохранены через сводку и ссылки на реестры. Это этап документации: код и сервер не изменялись, игровое исполнение новых правил не заявляется.

# 2026-10-19 - Prealpha 0.7.4 ZTN opening/resource/navigation iteration

Added500 new unique top-player ZTN demos and provenance; recomputed924 opening windows, resource-pattern candidates and129 start-jump observations (72 full4s). Native opening bank now48 scored candidates. Fixed reserved-red cooldown bypass and stale watchdog state, added bounded pixel-stall fallback, corrected rightmove/view-yaw sign and first-jump speed gate. Added preliminary recover/anchor/cycle resource weights with explicit evidence limits. Debug/Release14/14, Python105/105; valid short Xaero5 smoke reached25 pickups, one major, two opening steps and observed1:2 before reset. Global opening optimality, full hide-and-seek logic, perfect navigation and human-reference651UPS remain unconfirmed. Agent100 unavailable from the indexed archive. Test27961 updated; primary27960 preserved. Details: docs/PREALPHA_0_7_4_RU.md.

# 2026-10-12 - Prealpha 0.7.2 boost executor and second-cycle red

Generalized the learned jump executor from one rocket shot to weapon-specific impulse sequences. The 16 existing rocket examples retain one RL shot; one repeated three-shot plasma climb to Blood Run Heavy Armor was extracted from pro-demo 10774 and added as forced-probe-only sample 17. Red boost attribution is now limited to 0-3 seconds and groups repeated plasma damage into one sequence. The opening policy now reserves the first second-cycle Heavy Armor by the observed item clock, choosing diagnostic `fight` or `penalty` mode from stack and Trinity readiness. A valid Sarge-1 trial confirmed `penalty` selection and the actual red pickup; another run confirmed RJ sample 0 with +129 height and immediate red pickup. The first 20-second forced sweep confirmed eight additional RJ samples once; plasma started but did not produce a confirmed finish. Debug/Release 14/14 and Python 105/105. Main server unchanged. See docs/PREALPHA_0_7_2_BOOSTS_OPENING_RU.md.

# 2026-10-12 - Prealpha 0.7.1 Psyz0r chat connected

Copied the deployed Xaero room plugin into source for comparison and added a bounded Psyz0r-only test plugin. Sports GL/HF/GG, match start/end, rail/rocket/gauntlet-kill reactions, limited retorts and sparse periodic lines are live on 27961. Rebuilt the same native Psyz0r hooks into full Python minqlx; test runner now enables stats before engine startup. Backup `psyz0r-071-chat-20261012T055235Z`; main PID227498 unchanged. Per-damage gauntlet accumulation and corpse shots still need native sensors. See docs/PREALPHA_0_7_1_CHAT_RU.md.

# 2026-10-12 - Prealpha 0.7.0 route strafe start

Replaced the ineffective speed-only route hop with a stopped-start controller: circle-jump preparation, bounded yaw sweep, first-flight jump release, immediate second takeoff and continued route beats. Calibration comes from 99 non-firing two-jump starts in 100 Blood Run POV demos; raw keys/mouse are explicitly not claimed. Combat and damage gates stay above route movement. Debug/Release 14/14 and Python 101/101. Linux NOPY SHA `976b374c...323f` deployed only to 27961 after backup; main PID 227498 unchanged. Smoke reached 320-322 UPS in sustained route phases without error tokens; stopped-start live branch awaits owner test. See docs/PREALPHA_0_7_0_RU.md.

# 2026-10-12 - Server Xaero communication lines deployed

Updated only dialogue behavior in the live server's minqlx plugin: seven delayed private join greetings, five no-repeat blue/white/blue GL & HF lines for a one-human Xaero duel, and four friendly lines after a completed duel. Psyz0r AI, skills and combat logic were untouched. A backup was made; syntax and mocked behavior checks passed. The confirmed-empty server restarted; minqlx loaded `room_bot`, logged Practice bot ready, and systemd is active at PID 226792. Weapon praise and blowout GG remain disabled until thresholds are agreed. Full inventory: docs/server/XAERO_COMMUNICATIONS_2026-10-12_RU.md.

# 2026-10-12 - Prealpha 0.6.9 item clocks and openings deployed

Owner demo analyzed: bot4-10, red0/mega8/yellow12, LG82/346, one confirmed higher RJ. Found 3s timing horizon and 30s goal hold; connected engine item-clock registry and travel-aware major lookahead/preemption. Fixed Red Armor display versus Heavy Armor botlib query (cold-start goal area1429). Openings latch start, wait for registry, require main-gun candidate and cancel on emergency rather than mere rival stack advantage. Audit36 candidates/100 destinations valid, 32 eligible, 39 demo-covered legs and61 AAS fallbacks. Live: two full LG-Mega-RG orders; final build full Red-RG with actual red pickup at+9.1s. Engine clocks verified armor25s/Mega35s. Debug/Release14/14, Python99/99. Final SHA a29bf4da62c096c2c24bea072ee690ac86c9d900f647c0caca9c3b4502711eda. Only27961 changed. Aim calibration and other opening variants remain. See docs/PREALPHA_0_6_9_RU.md.

# 2026-10-12 - LG-first duel weapon profile

Owner weapon hierarchy applied to retail profile 0.6.7-lg1: LG240 in working horizontal range, RL170 main alternative, RG260 beyond LG range; secondary guns reduced. Adjacent integer fuzzy nodes prevent a broad transition across the medium range. Profile loaded on isolated27961 after backup; native unchanged. Local Behavior aligned with LG-first, far RG/RL and conditional safe shotgun finish. Rail-hit-to-push rule preserved as pending event integration, not claimed live. See docs/WEAPON_PRIORITY_LG1_RU.md.

# 2026-10-12 - Prealpha 0.6.7 loadout preparation deployed

Connected ammunition reserves, missing-weapon preparation and optional forward-push gate; armor damage extends grounded combat, aim targets interpolate across windows. Debug/Release 14/14 and Python99/99. Two isolated 40s duel trials (including map reload): 20 pickups, 11 preparation gates, 3 grounded-jump blocks, 8 aim-profile records, no detected ERROR/load failures. Test27961 Blood Run Duel verified; main PID unchanged. See docs/PREALPHA_0_6_7_RU.md and docs/ADDON_RUNTIME_STATUS_RU.md. Full behavior integration remains incomplete.

# 2026-10-12 - Duel Pracc Room technical-restart warnings deployed

Added red `WARNING` notices 15, 10, 5 and 1 minute before the six-hour restart deadline. The restart still waits for an active duel to finish. Focused tests passed for all thresholds, duplicate suppression and missed-window handling. At the owner's request, the empty main server was restarted to load the plugin; service is active (PID 223006), UDP 27960 is listening, and the deployed file is mode 644 with SHA-256 `b79aac73eb2d54472cdb63a349f80d63fc9a44485352db61fae43c4d342080f8`. The first live countdown is not yet due. See docs/server/DUEL_PRACC_ROOM_STATUS_2026-10-12_RU.md.

# 2026-10-12 - Xaero command update active after scheduled restart

Verified the main service is active after its regular six-hour restart (PID 218143), which occurred after the bot plugin and Welcome config were written. `room_bot` loaded; no import traceback was found. Commands are ready for owner in-game testing. Runtime Welcome cvar and command behavior have not been queried/tested. Logs include a prior skill-5 bot-spawn failure on bloodrunintel. No additional restart was issued. See docs/server/DUEL_PRACC_ROOM_STATUS_2026-10-12_RU.md.

# 2026-10-12 - Xaero end-of-duel praise proposal

Specified required positive post-duel praise, occasional rail/lightning/rocket compliments grounded in reliable accuracy samples, GG/GG WP endings, and a sad-bot line for a blowout. Accuracy sample/percentage and blowout thresholds remain to be agreed. Documentation only; no server or plugin changes. See docs/server/XAERO_JOIN_GREETING_OPTIONS_2026-10-12_RU.md.

# 2026-10-12 - Xaero duel-start greeting copy

Added five proposed duel-start phrases with blue/white/blue `GL & HF` styling, including full-word and playful variants. Specified one line only after an accepted bot duel actually starts, excluding ordinary human-vs-human games. Documentation only; no bot or server changes. See docs/server/XAERO_JOIN_GREETING_OPTIONS_2026-10-12_RU.md.

# 2026-10-12 - Prealpha 0.6.6 deployed on isolated 27961

Own Psyz0r weapon profile, nearby missing trinity pickup override, grounded combat and approved all-weapon aim target inputs connected. Actual accuracy calibration remains incomplete. Debug/Release 14/14; live smoke 33 pickup records, 11 aim profile records, no ERROR strings. Trial opponent removed. See docs/PREALPHA_0_6_6_RU.md.

# 2026-10-12 - Xaero join greeting copy proposal

Drafted seven short, friendly English join lines with Russian meanings, plus proposed one-line-per-human-join selection behavior. Documentation only: no plugin or server changes. See docs/server/XAERO_JOIN_GREETING_OPTIONS_2026-10-12_RU.md.

# 2026-10-12 - Grenade zoning safety policy

C++ one-grenade permission module for Mega from GL platform and upper TP to red. Requires fresh confirmed enemy position, verified fastest approach excluding fast closure, safe demonstrated trajectory and zoning purpose; unknown safety denies. Local only, not wired to game. Debug/Release14/14. Demo-shot candidates mined separately, not asserted tactical proofs. See docs/GRENADE_ZONING_RU.md.

# 2026-10-12 - Owner approved all-weapon accuracy ranges

Authoritative config/accuracy_targets_all.json approved. MG39[37,43], SG30[23,40], GL6[2,9], RL34[28,40], LG36[32,40], RG49[40,58], PG12[10,15]. Runtime calibration incomplete; execution flag remains false. Grenade spam policy awaits owner rules. Existing live angular-error settings unchanged.

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

Added admin commands `!goduel` (one-human, one-duel lifecycle; refuses during an active match) and `!leaveme` (alias of the existing bot removal/suppression handler), and documented both in Welcome. Backed up the live plugin and server.cfg before updating files on disk. The running service was not restarted, so runtime activation and gameplay validation remain pending. Syntax and three focused mocked `!goduel` cases passed. Status and exact changed behavior: docs/server/DUEL_PRACC_ROOM_STATUS_2026-10-12_RU.md.

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


## 2026-10-19 - Analytics site title

Set the dashboard header, sidebar brand, browser title and footer to the owner-approved name: Pracc Room Server. Regenerated the standalone HTML. Validation: node tests/analytics_static_checks.cjs passed. Bot runtime unchanged.


## 2026-10-19 - Seamless fixed analytics backdrop

Moved the decorative gradients to a single fixed viewport layer with no repeat. Page content scrolls over the stationary background; no scroll listeners or continuous animation are needed. Disabled the decorative layer for printing and regenerated the standalone HTML. Static dashboard and standalone-script checks passed.

## 19.10.2026 — Пре-альфа 0.7.9: разбор 200 демок и навигация

Заново извлечены 200 уникальных сохранённых оригиналов вне top500: 200/200, 127 итоговых 1v1-записей, 22 разных победителя/лидера damage, 96 доступных выбранных POV, 37 стартов (18 полных 4с). Общие таблицы победителя и лидера урона раздельные. Новые точности не объявляются достигнутой точностью бота.

Native: motion-watch при stock-командах без item-цели; одинаковое короткое ожидание на одном уровне; поля команд/цели/брони/pmtype в логах; intermission исключён из управления и восстановления. Финальный runtime только 27961, backup+SHA, основной PID 415921 сохранён. Профиль Xaero 5, чат и aim-настройки не заменялись. Первый 5-минутный матч до финального intermission-guard: 4:9 против Xaero 5, RA3/Mega3/YA2 против RA0/Mega4/YA11. Победа и устойчивый контроль не подтверждены. Финальная сборка: 30с разминки, 5 подборов, pmtype-диагностика, fatal нет.

Проверки: 17 CTest, 138 Python, 5 Linux-групп; отдельные offline/portable HTML и математика mindmap. Реальная Android/браузерная визуальная проверка недоступна. Полный отчёт docs/PREALPHA_0_7_9_RU.md.

## 19.10.2026 — Сайт и сбор матчей

Pracc Room Server BOT, два неоновых акцента, более крупный текст, фиксированный фон без стыков, анимированные графики/гистограммы/круговые диаграммы. 284 правила / 15 веток, DOM+SVG mindmap с переносом узлов, масштабом, поиском и сохранением раскладки. Сравнение текущего этапа с 0.7.6/0.7.7/0.7.8; офлайн-этап отмечен явно.

Начальный реестр: 7 матчей Psyz0r и отдельно 59 архивных Xaero. Неизвестные версии/skill/оружейные значения не выдумываются. Автообучения нет; измерение прогресса требует сопоставимых матчей одной версии/native SHA.

Read-only ZMQ-сборщик установлен отдельным user-unit на сервере, без перезапуска QL. Включён qlserver linger для фонового сборщика. Public JSON отделён от приватного буфера; Steam ID не публикуются. Реальная первая новая завершённая дуэль ещё ожидается. Локальный watcher и публикация подготовлены; итоговые квитанции добавляются отдельно. Документы: docs/MATCH_TELEMETRY_RU.md и docs/WEB_ANALYTICS_079_RU.md. Автономный HTML/ZIP собраны для телефона и пересылки; APK не требуется.
## 2026-10-19 — порядок следующих итераций
Зафиксированы основа Xaero 5, ограничения надстроек и приоритет небольших изменений по обратной связи. План сравнения: отдельные сопоставимые серии, одна правка за этап; автоматическое обучение не заявляется. См. docs/NEXT_ITERATION_PRIORITY_RU.md. Runtime не менялся.


## 2026-10-19 — черновая анимация силуэта
Локальный SVG-спортсмен слева от H1: прыжок, ракета к release, вспышка и затухание контура 1300мс. Цикл 12с, reduced-motion, неподвижный фон без повторений. Силуэт ожидает референс владельца; публикация финального визуала после подгонки. Проверены JS syntax и analytics_static_checks; браузерная анимация визуально ещё не проверена. Runtime бота не менялся.


## 2026-10-19 — детальный персонаж и механический глаз
Черновой силуэт заменён детальным спрайтом Doom Marine; одноразовый прыжок и ракета после reload, 20 положений дуги, четыре позы, затухание рамки 1300мс и непрерывный дым после приземления. Угловая иконка — механический SVG-глаз. Пересобраны автономный HTML и ZIP; JS и dashboard checks прошли. Браузерное воспроизведение не проверено: UI поверхности недоступны. Подробности docs/HEADER_MASCOT_RU.md. Игровой runtime не менялся.


## 2026-10-19 — 30 кадров, дым и орб
Новый атлас содержит 30 поз; Canvas показывает фрагменты с индивидуальными границами без искажения пропорций. Добавлены отдача и отдельные рассеивающиеся частицы следа ракеты. Угловая иконка заменена детальным механическим орбом. Пересобраны HTML/ZIP, проверки скриптов и упаковки пройдены. Просмотр PNG выполнен; воспроизведение в браузере здесь не проверено. Игровой runtime не менялся. См. docs/HEADER_MASCOT_RU.md.


## 2026-10-19 — меню, взрыв и запуск персонажа по кнопке
Орб увеличен с 40 до 80px. Боковое меню регулируется мышью и стрелками в диапазоне 240–390px с сохранением ширины; на телефоне ручка скрыта. Заголовок выровнен с персонажем и опущен. Подсветка охватывает строки таблиц. Взрыв дополнен ударным кольцом, 18 осколками и 18 частицами дыма. Персонаж ждёт 1с после загрузки и запускается по клику/Enter/пробел; повтор доступен после завершения сцены. 30 поз прыжка ускорены с 2.4 до 2.0с; скорость ракеты и дыма сохранена. JS syntax и static dashboard/portable checks пройдены. Браузерная визуальная проверка в окружении недоступна. Runtime бота не менялся.


## 2026-10-19 — финальная правка глаза и проверка эффектов
Убраны видимая подпись и hover-подсказка персонажа; доступное имя кнопки сохранено. Механические веки орба проходят 12 положений за 420мс с паузой 6–8с, останавливаются в скрытой вкладке и при reduced-motion. Runtime-проверка сцены подтвердила запуск только по клику, все 30 поз, одну ракету, рассеивающиеся частицы, 18 осколков, удаление ракеты и готовность к повтору. Проверки автономной упаковки пройдены; визуальный просмотр в браузере недоступен. Пересобраны HTML и ZIP. Игровой runtime не менялся.


## 2026-10-20 — плотный шлейф и многослойный взрыв
Усилены факел и ореол ракеты, след заполнен 49 сохраняющимися сегментами с более долгим рассеиванием. Взрыв: 36 остывающих металлических осколков с падением, 8 отдельных огненных всплесков, 28 тяжёлых дымовых частиц и ударное кольцо. Добавлен мягкий блик глаза без изменения текущего дизайна. Runtime-check, JS syntax и проверки автономной упаковки прошли; визуальное воспроизведение в браузере не проверено. Скорость ракеты/прыжка сохранена. Runtime сервера не менялся.


## 2026-10-20 — собственный VPS и финальная струя ракеты
Скрытая полная область клика сохранена, видимая рамка и hover-подсветка персонажа удалены. Факел укорочен 85→44px, колебания уменьшены, добавлено синее ядро, свет смещён на 22px к соплу. Сайт и read-only live API размещены на http://78.17.9.235 с автозапуском и резервным архивом; внешний HTTP200 и API schema1/66 матчей проверены. На IP/домене данные берутся напрямую с VPS каждые30с. Публичный DNS 50515051.com пока NXDOMAIN; локальная запись hosts не означает регистрацию. VPN443 и игровые PID сохранены. Подробности docs/VPS_ANALYTICS_RU.md. Проверки JS/runtime/offline пройдены, браузерное воспроизведение здесь не проверено.


## 2026-10-20 — публичный коннект в шапке
Справа в шапке крупно добавлен connect 78.17.9.235:27961, кнопка копирования с HTTPS Clipboard API и HTTP fallback. Копирование включает всю команду для консоли QL. Статус описывает включённый сбор статистики без ложного заявления об автоматическом обучении. Адрес загрузки демок пока не выбран и не выдумывается. Новая вводная владельца: реализовать программный конвейер обучения; сейчас только сбор данных и ручные обновления правил, автоматическое обучение остаётся отдельной незавершённой задачей. Статические/runtime проверки пройдены; публичная VPS-страница проверена на наличие коннекта. Backup обновлён. Игровые PID429089/426895 сохранены.


## 2026-10-20 — вступительный прыжок при каждом reload
По уточнению владельца восстановлен автоматический одиночный прыжок/выстрел через 1с после загрузки спрайта на каждой новой странице. После вступления повтор по клику. Таймерного цикла нет; флаг не сохраняется между reload. Скрытая вкладка откладывает старт до возвращения; reduced-motion сохраняет неподвижный режим. Runtime-test проверил паузу, один автоматический выстрел, отсутствие самоповтора и повтор по клику. HTML/ZIP пересобраны, static checks пройдены. VPS release20261020-autojump, SHA c22b4868ff50021b9c4fcd85b218389acf6c17ec1d5ba06f5506a6a2795438ec; backup обновлён, игровые процессы не перезапускались.


## 2026-10-20 — ещё ×1.2 к скорости прыжка
Длительность прыжка 2000→1667мс, все 30 поз сохранены. Таймеры полёта, дыма, взрыва и моргания не изменены. Автовступление и повтор по клику сохранены; runtime/static проверки прошли. VPS release20261020-jump-speed, SHA81c828bb026037e0e19474caac5b24a89b1f8e7eff6941cab122dc168e07b4b4, backup обновлён. Игровой runtime не менялся.


## 2026-10-20 — клик по глазу и перезагрузка по бренду
Иконка глаза стала отдельной кнопкой моргания, текст бренда — отдельной ссылкой с reload. Исключены вложенные интерактивные элементы. Веки получили выпуклую светотень, блики, фаску и тень кромки. Автоморгание6–8с сохранено, повторные клики не накладывают сцены. Eye-actions test проверил 12 положений, расписание, защиту от наложения и раздельный reload; mascot/static checks прошли. VPS release20261020-eye-click, SHA61e6e64c392e4e1623da838a4f626f7394aad19010af1caa39e57368ce3cb79f, backup обновлён. Визуальное воспроизведение здесь не проверено, игровые процессы не менялись.


## 2026-10-20 — единый hover-коннект
Команда и копирование объединены в одну кнопку. Connect выровнен по центру; при hover/focus IP скрывается и на том же месте появляется Скопировать Connect. Копируется текст code, а не hover-подпись. HTML/ZIP обновлены, static checks пройдены. VPS release20261020-copy-hover, SHA21d1218943769a71927041aa6f1ab4726d982702dad529e1027689ec54d929ff, backup обновлён; игровой runtime не менялся.


## 2026-10-20 — первая боевая итерация 0.8.0
Разделены бот/сайт. Тренировочный конфиг основан на публичных настройках основного, изоляция сохранена; ProQ/Bot синие, room/Server белые. Psyz_presence возвращает одного Psyz0r на каждой загрузке ZTN. Native0.8.0 подключает подтверждённые LG/RG попадания к combo-policy, ограничивает невыгодный forward и разрешает близкую нужную пушку при восстановлении. Скрытый точный стек из выбора целей убран; combo использует оценку по своему урону. Skill/aim/profile не повышались. Свежие демки4:20 и0:12 сохранены; второй матч — намеренная отдача ресурсов. Из200 файлов1514 окон и808 многопушечных кандидатов, не доказанных цепочек урона. Windows17/17, Linux5групп, Python143/143. 90с smoke: 1brake,0combo-switch, fatalfalse. Комбо загружено, но успешное выполнение ещё не подтверждено. Подробности docs/PREALPHA_0_8_0_RU.md и полное ТЗ docs/OWNER_TASK_20261020_RU.md. Сайт — следующий независимый этап, без перезапуска игровой службы во время тестов.


## 2026-10-20 — UI 0.8.0 and pending 0.8.1
Published viewport charts, weapon illustrations, thinner eyelids and four-release comparison. Diagnosed VM hook-pool exhaustion; fixed and passed 100 allocator reload cycles. 0.8.1 deployment blocked before mutations by human-presence guard. See docs/PREALPHA_0_8_1_PENDING_RU.md.
