# Коммуникации Xaero — актуальный набор и логика

## Новые реплики, включённые в тестовую версию

### При входе человека

Xaero выбирает одну из семи фраз на каждое подключение реального игрока. Фразы идут без повторов, пока не исчерпается набор, затем порядок перемешивается заново. Сообщение личное, не ботам; отправляется после загрузки игрока с задержкой 8 секунд, чтобы не накладываться на серверное Welcome. Смена карты и начало матча не вызывают повторное приветствие. После отключения повторный вход считается новым подключением.

| Реплика | Смысл |
|---|---|
| `Hey, welcome! Fancy a duel, or are you still warming up?` | Привет! Сыграем дуэль или ты пока разминаешься? |
| `How's life treating you? Got time for a quick duel?` | Как дела, как жизнь? Найдётся время на быструю дуэль? |
| `Want me to step aside, or should we run a few rounds?` | Мне отойти или побегаем пару раундов? |
| `Waiting for another player? You can practice on me meanwhile.` | Ждёшь другого игрока? Пока можешь потренироваться на мне. |
| `Ready to duel, or should I keep you company in warm-up?` | Готов к дуэли или составить компанию на разминке? |
| `I'm warmed up. How about you? One quick duel?` | Я уже размялся. А ты? Сыграем одну быструю дуэль? |
| `The room's quiet. Shall we make it a match?` | В комнате тихо. Может, устроим матч? |

### В начале принятой дуэли с Xaero

На `game_countdown` отправляется ровно одна фраза, только если есть один человек, управляемый бот и ожидаемая дуэль (`one_duel` или `manual`). Обычная PvP-дуэль без Xaero не получает этого сообщения. Набор перемешивается, повторы откладываются до исчерпания. Начало синее (`^4`), амперсанд белый (`^7`), продолжение снова синее (`^4`).

| Реплика | Смысл |
|---|---|
| `^4GL ^7& ^4HF!` | GL & HF! |
| `^4Good luck ^7& ^4have fun!` | Удачи и хорошо провести игру! |
| `^4Good luck in our duel ^7& ^4have fun out there!` | Удачи в нашей дуэли и хорошей игры! |
| `^4May your aim be true ^7& ^4your duel be fun!` | Пусть прицел не подводит, а дуэль будет в удовольствие! |
| `^4Ready? Good luck ^7& ^4let's have a great duel!` | Готов? Удачи, и пусть дуэль получится отличной! |

### После завершённой дуэли с Xaero

После не прерванной игры, только при одном человеке и управляемом Xaero, выбирается одна из четырёх доброжелательных фраз. Она отправляется через 16 секунд и принудительно проходит общий cooldown, чтобы похвала не пропала после последней реплики во время боя. Прерванные матчи и PvP без Xaero исключены.

| Реплика | Смысл |
|---|---|
| `^7GG! ^4Nice duel — you kept me on my toes.` | GG! Хорошая дуэль — ты заставил меня не расслабляться. |
| `^7GG WP! ^4That was a fun fight. Well played!` | GG WP! Было интересно. Отлично сыграно! |
| `^4You played that duel really well. ^7GG!` | Ты отлично сыграл эту дуэль. GG! |
| `^4Great fight! I had to work for every frag. ^7GG WP!` | Отличный бой! За каждый фраг пришлось побороться. GG WP! |

**Пока не включены:** отдельная похвала за rail/LG/rockets и грустная реплика `GG :-(` при разгромном счёте. Владелец ещё не утвердил минимальную выборку/точность и порог разницы фрагов. До согласования не выдаём неподтверждённые оценки статистики и не классифицируем счёт как разгромный.

## Остальные реплики, уже имеющиеся в плагине

Ниже сохранены текущие игровые фразы. Обычная болтовня работает только при активной дуэли один-на-один с управляемым Xaero; интервал — 150 секунд. На каждом цикле выбирается очередная фраза без повтора в рамках матча. Реплика из редкого списка выбирается вместо обычной с вероятностью 1/6. Общий cooldown — 15 секунд.

### Начальные/обычные реплики (включая существующий opener набор)

- `Knock, knock? Sneaking and hiding with shaking hands - }:-> Very smart play! }:->`
- `If you want big red watermelons - don't plant cucumbers :-) Sorry 4 SkillZ }:->`
- `Дракон, а ты качаешься что-ли??? Я всё ревно тебя вырублю, если захочешь) Ну если дернешься...`
- `What the fuck are you playing, {player}? You're not holding B, you're not holding mid... Oh wait, wrong game.`
- `Welcome to Finland, {player}. The ping is low. The hospital bill isn't.`
- `No matchmaking. No excuses. Just you, me, and the red armor you forgot.`
- `{player}, stop checking corners. This is Quake. Check the ceiling.`
- `{player}, I predicted your movement. All two directions.`
- `You're not low HP. You're one bad decision away from spectating.`
- `I missed on purpose. Needed to feel human for a second.`
- `I respect your strategy. Especially the part where you keep doing it.`
- `You can have the yellow armor. I've already made it red.`
- `Your aim is fine. The wall is definitely dead.`
- `You had the high ground. I had basic geometry.`
- `I don't need wallhacks. Your footsteps have a postcode.`
- `That jump looked expensive. Did it cost you all your health?`
- `Don't panic. There's plenty of time to miss another rail.`

### Редкие шутки об администраторе/уроках

- `nekitz0r - a living CS 1.6 legend. You know that, right? :-)`
- `Work on your SkillZ at Intel_maps by nekitz0r. You got that, son? {player}, I'm talking to you. }:->`
- `Born in a .cfg file. Raised by nekitz0r. Absolutely no manners.`
- `Looking for the bombsite, {player}? Same. nekitz0r still hasn't installed one.`
- `Intel maps. Questionable decisions. Welcome to the server. }:->`
- `Complaints about my aim? Contact nekitz0r. He'll tell you to practice.`
- `Behind every nekitz0r is a Sensei PsyRoZ wondering where the lesson went wrong.`
- `Sensei PsyRoZ charges $100 per lesson. My rockets deliver free feedback. }:->`
- `I asked PsyRoZ how to improve. He said "$100." Finally, a clear answer.`
- `nekitz0r learned from PsyRoZ. {player}, did you learn from the loading screen?`
- `Somewhere, Sensei PsyRoZ is watching this duel and slowly closing his eyes.`
- `$100 gets you a lesson with PsyRoZ. Running at me with a gauntlet gets you a practical demonstration.`
- `Nice shot, {player}! PsyRoZ offers no refunds for accidental talent. :-)`
- `PsyRoZ taught nekitz0r. I learned from a config file. We had different budgets.`
- `{player}, here's some advice: book a lesson with Sensei PsyRoZ for $100. :-)`

### Реакции на игровые события

При смерти Xaero от игрока: одна случайная фраза похвалы из этого набора; для railgun используется отдельная фраза.

- `Well played. Who taught you that, and are they available?`
- `I had a plan. You appear to have deleted it.`
- `Okay, that was filthy. Respect.`
- `{player}, you're playing better than nekitz0r. Don't tell him I said that. :-)`
- `That's Nikolai "Agent" level already, {player}. Respect!`
- Railgun: `Nice rail, {player}. I'm uninstalling my eyes.`

При убийстве игрока Xaero отдельные реплики есть только для railgun и rocket:

- Railgun: `That rail went straight into your confidence.`
- Rockets: `{player}, that rocket was a warning shot. The next five are customer service.`
- Rockets: `Nice dodge. Wrong rocket, though. }:->`
- Rockets: `That wasn't a prediction rocket. You were just late.`
- Rockets: `Stop running! I'm trying to discuss your extended rocket warranty.`

Эти игровые kill/death реакции не являются похвалой по проценту попаданий: они привязаны к событию смерти и weapon MOD.

## Проверка и установка

Резервная копия перед изменением: `/home/qlserver/server/minqlx-plugins/room_bot.py.pre-communications-20261012T0132Z`.

Локальные изолированные проверки покрывают личное приветствие с задержкой, фильтр актуального подключения, однократный GL & HF при подходящем countdown и положительную фразу после завершённого матча. Установка на сервер и проверка в игре фиксируются отдельно после безопасного применения на пустом сервере.
