# Отчёт локальной сборки — 10 октября 2026

По команде владельца выполнена компиляция текущего проекта, включая CombatPredictor. Исходная версия ядра — коммит 96552b8. Незавершённые изменения документации сохранены отдельно и не включены в этот этап.

- CMake / Visual Studio 2022 BuildTools, MSVC x64.
- Debug: успешная сборка, CTest 7/7.
- Release: успешная сборка, CTest 7/7.
- Release psyz0r_sandbox запущен локально с config/core.ini; JSONL разобран, все записи game_command_sent=false.
- Сервер, игровой клиент и сетевое управление ботом не запускались. Эти проверки не подтверждают боевое поведение Quake Live.

## Где результат

В корне Project_Psyz0r_bot:

- out/msvc-x64/Debug/ — отладочные exe и psyz0r_core.lib.
- out/msvc-x64/Release/ — оптимизированные exe и psyz0r_core.lib.
- out/offline-build/ — configure.log, build-Debug.log, build-Release.log, tests-Debug.log, tests-Release.log, sandbox.log и sandbox.jsonl.

psyz0r_sandbox.exe и reaction_sandbox.exe — локальные стенды, не готовый устанавливаемый бот/плагин для сервера. combat_prediction_tests.exe проверяет расчёт упреждения; игровой исполнитель ещё не подключён.

Бинарники и журналы остаются локально в игнорируемом out, в Git включается только отчёт. Удалённый репозиторий не настроен, публикации в GitHub нет.

После сохранения отчёта и коммита по просьбе владельца планируется гибернация Windows. Доступность режима подтверждена powercfg /a; фактический переход нельзя проверить из уже уснувшего процесса.
