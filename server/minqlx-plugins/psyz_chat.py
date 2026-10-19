"""Bounded duel chat for the isolated Psyz0r test bot.

It speaks only for one Psyz0r bot plus one human on the isolated test server.
Optional forfeit may remove only that confirmed bot, never a human; it never
spawns a replacement. Stock bot chat remains disabled for a single voice.
"""
import random
import re
import time

import minqlx


BOT_NAMES = {"psyz0r", "psyz0r_bot", "pzyz0r-bot", "pzyz0r_bot"}
COOLDOWN = 12
PERIOD = 180

SPORT_OPEN = (
    "^4GL ^7& ^4HF!",
    "^4Good luck ^7& ^4have fun!",
    "^4Ready? Good luck ^7& ^4let's have a great duel!",
)
SPORT_REPLY = (
    "^4GL HF^7, {player}!",
    "^4Have fun^7, {player}. Let's make it a close one.",
    "^4Good luck!^7 No excuses after the countdown :-)",
)
GG_REPLY = (
    "^7GG WP! ^4Nice duel.",
    "^4Well played! ^7GG.",
    "^7GG! ^4Run it back when you're ready.",
)
END_LINES = (
    "^7GG! ^4Nice duel — you kept me on my toes.",
    "^7GG WP! ^4That was a fun fight. Well played!",
    "^4Great fight! I had to work for every frag. ^7GG WP!",
)
GAUNTLET_LINES = (
    "Put that little knife away, {player} :-)",
    "Okay, gauntlet noted. I'll return it when you're low HP.",
    "You scratched me with the gauntlet. Now it's personal.",
    "Knife again? Fine. My turn :-)",
    "Keep that glove warm. I'll need it :D",
)
HELLO_LINES = ("Hey {player} :) Ready for ZTN?", "Hi :) Red or mega first?", "Yo {player} :) Let's quake!")
TOPIC_LINES = {
    "find": ("Challenge accepted :) Listen for footsteps.", "Hide well. I'll check the items first :)", "See you at the next mega :)"),
    "mood": ("Still warming up :) How about you?", "Rails could be better. Mood is good :D"),
    "spam": ("Easy on the keyboard :) One message at a time.", "I heard you :) Save some energy for the duel."),
    "mega": ("Mega talk? Watch the clock :)", "Health is nice. Getting out alive is nicer :D"),
    "red": ("Red room gets expensive :) ", "Armor first. Excuses later :D"),
    "shaft": ("LG time :) Keep your feet moving.", "A little shaft and a lot of strafing :D"),
}
RETORT_LINES = (
    "Talk less, time the items more, {player}.",
    "Save the rage for the rematch :-)",
    "You type well. Now show me the movement.",
    "Noob? Then stop giving me rail practice :)",
    "Yeah yeah :) Settle it at red.",
    "Fuck off? After the duel :D",
)
SMALLTALK_LINES = ("Still here :) What's your next move?", "Less typing more Quake :)", "Ready for another fight? :D")
PRAISE_LINES = (
    "Well played, {player}. That was clean.",
    "Okay, that was filthy. Respect.",
    "I had a plan. You appear to have deleted it.",
)
RAIL_PRAISE = "Nice rail, {player}. I'm uninstalling my eyes."
RAIL_TAUNT = "That rail went straight into your confidence."
ROCKET_TAUNTS = (
    "Nice dodge. Wrong rocket, though. :-)",
    "That wasn't a prediction rocket. You were just late.",
)
PERIODIC_LINES = (
    "I respect your strategy. Especially the part where you keep doing it.",
    "I don't need wallhacks. Your footsteps have a postcode.",
    "That jump looked expensive. Did it cost you all your health?",
    "No matchmaking. No excuses. Just you, me, and the red armor.",
)


def clean(text):
    return re.sub(r"\^[0-9]", "", str(text)).replace("^", "").strip()


def is_bot(player):
    try:
        sid = int(player.steam_id)
        return sid == 0 or (sid & 0xFFFFFFFF00000000) == 0x0140000100000000
    except (AttributeError, TypeError, ValueError):
        return False


def is_psyz(player):
    return is_bot(player) and clean(getattr(player, "clean_name", "")).lower() in BOT_NAMES


def render(line, player=None):
    name = clean(getattr(player, "name", "")) if player is not None else ""
    # Plain punctuation avoids the square glyphs seen in the game client.
    return (line.replace("{player}", "^3{}^7".format(name or "player"))
            .replace(",", "").replace("—", "-").replace("’", "'"))


def same_player(a, b):
    # minqlx может создать новую Python-обёртку того же клиента для chat hook.
    # Сравниваем Steam ID и слот, а не адрес объекта в памяти.
    if a is None or b is None or is_bot(a) or is_bot(b):
        return False
    try:
        return (int(a.steam_id) == int(b.steam_id) and
                getattr(a, "id", None) == getattr(b, "id", None))
    except (AttributeError, TypeError, ValueError):
        return False


def classify_chat(text):
    normalized = clean(text).lower().replace("ё", "е")
    if normalized.startswith(("#", "!")):
        return None  # Метки демки и команды не становятся случайной беседой.
    words = set(re.findall(r"[a-zа-я0-9]+", normalized))
    compact = "".join(re.findall(r"[a-zа-я0-9]+", normalized))
    if "gg" in words or "wp" in words or "goodgame" in compact or "wellplayed" in compact:
        return "gg"
    if ("gl" in words or "hf" in words or "glhf" in compact or
            {"good", "luck"}.issubset(words) or {"have", "fun"}.issubset(words)):
        return "sport"
    rude = {"idiot", "noob", "n00b", "nub", "trash", "retard", "pizaras", "pidaras", "xyilo", "xyi", "xyй", "хуйло", "пидарас", "нуб", "нубас", "нубяра", "сука", "лох", "тупой", "дебил", "говно", "нахуй", "хуй", "блядь", "блять", "fuck", "shit", "ez", "изи"}
    if words & rude:
        return "retort"
    if any(phrase in compact for phrase in ("найдименя", "findme", "naidimenya", "naydim enya".replace(" ", ""))):
        return "find"
    if "howareyou" in compact or "какдела" in compact or "kakdela" in compact:
        return "mood"
    if words & {"hi", "hello", "hey", "yo", "привет", "здарова", "ку", "здравствуйте"}:
        return "hello"
    for topic, tokens in {"mega": {"mega", "мега", "мегу"}, "red": {"red", "красный", "красном"}, "shaft": {"shaft", "lg", "шафт", "шафтом"}}.items():
        if words & tokens:return topic
    if words & {"thanks", "thx", "спасибо", "lol", "лол", "хаха"}:
        return "banter"
    if words & {"yes", "no", "ok", "okay", "да", "нет", "ага", "ок"}:
        return "followup"
    if "howareyou" in compact or "какдела" in compact:
        return "banter"
    if words & {"bot", "бот", "psyz0r", "psyz"}:
        return "banter"
    return None


class psyz_chat(minqlx.Plugin):
    def __init__(self):
        super().__init__()
        self.generation = 0
        self.last_say = float("-inf")
        self.used = set()
        self.gauntlet_damage = {}
        self.replied = set()
        self.last_reply = float("-inf")
        self.dialog = {}
        self.last_dialog_line = None
        self.forfeit_checked = False
        self.forfeit_selected = False
        self.forfeit_done = False
        self.forfeit_started = 0
        self.bot_score_seen = 0
        self.bot_last_frag = 0
        self.chat_arrivals = []
        self.add_hook("map", self.handle_reset)
        self.add_hook("new_game", self.handle_reset)
        self.add_hook("game_countdown", self.handle_countdown)
        self.add_hook("game_start", self.handle_start)
        self.add_hook("game_end", self.handle_game_end)
        self.add_hook("chat", self.handle_chat)
        self.add_hook("death", self.handle_death)
        self.add_hook("player_disconnect", self.handle_disconnect)
        self.add_command("psychat", self.cmd_test, 5)
        self.add_command("psyz_gauntlet_event", self.cmd_gauntlet_event, 5)

    def players_safe(self):
        try:
            return self.players()
        except Exception:
            minqlx.log_exception()
            return []

    def participants(self):
        # Spectators must not silence the active one-human duel.
        players = [p for p in self.players_safe()
                   if getattr(p, "team", "free") in ("free", "red", "blue")]
        humans = [p for p in players if not is_bot(p)]
        bots = [p for p in players if is_psyz(p)]
        return humans, bots

    def valid_duel(self):
        humans, bots = self.participants()
        return (humans[0] if len(humans) == 1 and len(bots) == 1 else None)

    def handle_reset(self, *args, **kwargs):
        self.generation += 1
        self.used.clear()
        self.gauntlet_damage.clear()
        self.replied.clear()
        self.dialog.clear()
        self.last_reply = float("-inf")
        self.last_dialog_line = None
        self.forfeit_checked = self.forfeit_selected = self.forfeit_done = False
        self.forfeit_started = 0
        self.bot_score_seen = 0
        self.bot_last_frag = 0
        self.chat_arrivals.clear()

    def handle_start(self, *args, **kwargs):
        # One roll per match, not one roll on each low-score frame.
        if self.forfeit_checked:
            return
        self.forfeit_checked = True
        self.forfeit_selected = random.random() < .35
        self.forfeit_started = time.monotonic()
        self.bot_last_frag = self.forfeit_started
        self.watch_forfeit(self.generation)

    def maybe_forfeit(self, now):
        if not self.forfeit_selected or self.forfeit_done or now-self.forfeit_started < 120:
            return False
        try:
            # Test-only lifecycle guard. Autofill would immediately undo leaving.
            if (self.get_cvar("net_port") != "27961" or
                    self.get_cvar("qlx_psyzForfeitEnabled") != "1" or
                    self.get_cvar("bot_minplayers") != "0" or
                    self.game.state != "in_progress"):
                return False
            human = self.valid_duel()
            if human is None:
                return False
            _, bots = self.participants()
            bot = bots[0]
            if bot.score > self.bot_score_seen:
                self.bot_last_frag = now
            self.bot_score_seen = bot.score
            if human.score-bot.score < 15:
                return False
            # A comeback pauses resignation; repeated actual gauntlet damage
            # can also establish that this particular duel is going badly.
            glove = self.gauntlet_damage.get(str(human.steam_id), 0)
            if now-self.bot_last_frag < 90 and glove < 150:
                return False
            # Latch before the action so disconnect/reentrant callbacks cannot retry.
            self.forfeit_done = True
            self.say("GG :) Nothing landed today. Rematch?", human, force=True, topic="forfeit")
            print("PSYZ_FORFEIT gap={} gauntlet_damage={} stalled_seconds={} probability=0.35".format(human.score-bot.score, glove, int(now-self.bot_last_frag)))
            bot.kick("Psyz0r forfeit")
            return True
        except Exception:
            minqlx.log_exception()
            return False

    @minqlx.delay(15)
    def watch_forfeit(self, generation):
        if generation != self.generation or self.forfeit_done:
            return
        self.maybe_forfeit(time.monotonic())
        if generation == self.generation and not self.forfeit_done:
            self.watch_forfeit(generation)

    def say(self, line, player=None, force=False, topic=None):
        now = time.monotonic()
        if not force and (now - self.last_say < COOLDOWN or line in self.used):
            return False
        if topic and topic in self.replied:
            return False
        self.msg("^7Psyz0r^7: {}^7".format(render(line, player)))
        self.last_say = now
        self.used.add(line)
        if topic:
            self.replied.add(topic)
        return True

    def handle_countdown(self):
        self.handle_reset()
        player = self.valid_duel()
        if player:
            self.say(random.choice(SPORT_OPEN), player, force=True, topic="opening")
            self.periodic(self.generation)

    @minqlx.delay(PERIOD)
    def periodic(self, generation):
        if generation != self.generation:
            return
        player = self.valid_duel()
        try:
            active = self.game.state == "in_progress"
        except Exception:
            active = False
        if player and active:
            remaining = [line for line in PERIODIC_LINES if line not in self.used]
            if remaining and random.random() < .35:
                self.say(random.choice(remaining), player)
            self.periodic(generation)

    def handle_chat(self, player, message, channel):
        if not same_player(player, self.valid_duel()):
            return
        kind = classify_chat(message)
        # Detect a burst even when the text is not in the vocabulary. Bot
        # messages never enter this path, so replies cannot start a bot loop.
        now = time.monotonic()
        self.chat_arrivals = [t for t in self.chat_arrivals if now-t < 8]
        self.chat_arrivals.append(now)
        if len(self.chat_arrivals) >= 4 and not clean(message).startswith(("!", "#")):
            kind = "spam"
        if kind is None:
            return
        if kind == "sport":
            self.say(random.choice(SPORT_REPLY), player, force=True, topic="sport_reply")
        elif kind == "gg":
            self.say(random.choice(GG_REPLY), player, force=True, topic="gg_reply")
        else:
            # Ответы игроку отделены от случайных реплик о фрагах. Одна тема
            # не блокируется на весь матч; 4с защищают чат от потока сообщений.
            now = time.monotonic()
            if now-self.last_reply < 4:
                return
            key = str(player.steam_id)
            previous = self.dialog.get(key)
            if kind == "followup":
                if previous is None or now-previous[1] > 45:
                    return
                pool = TOPIC_LINES.get(previous[0], SMALLTALK_LINES)
            else:
                pool = (RETORT_LINES if kind == "retort" else HELLO_LINES if kind == "hello"
                        else TOPIC_LINES.get(kind, SMALLTALK_LINES))
            choices = [line for line in pool if line != self.last_dialog_line]
            line = random.choice(choices or pool)
            if self.say(line, player, force=True):
                self.last_reply = now
                self.last_dialog_line = line
                self.dialog[key] = (kind if kind != "followup" else previous[0], now)

    def cmd_gauntlet_event(self, player, msg, channel):
        # Internal console bridge only: clients cannot forge damage events.
        console_player = player is None or isinstance(player, getattr(minqlx, "RconDummyPlayer", ()))
        if not console_player or str(channel) != "console" or len(msg) != 3:
            return
        if self.get_cvar("net_port") != "27961":
            return
        try:
            client, damage = int(msg[1]), int(msg[2])
        except (ValueError, TypeError):
            return
        human = self.valid_duel()
        if human is None or getattr(human, "id", -1) != client or not 0 < damage <= 1000:
            return
        _, bots = self.participants()
        self.handle_damage(bots[0], human, damage, 0, "MOD_GAUNTLET")

    def handle_damage(self, victim, attacker, damage, dflags, means_of_death):
        if victim is None or attacker is None or not is_psyz(victim) or is_bot(attacker):
            return
        if not same_player(attacker, self.valid_duel()) or "GAUNTLET" not in str(means_of_death).upper():
            return
        key = str(getattr(attacker, "steam_id", ""))
        self.gauntlet_damage[key] = self.gauntlet_damage.get(key, 0) + max(0, int(damage))
        # 50 cumulative damage is the owner's current rule. A death is not required.
        if self.gauntlet_damage[key] >= 50:
            self.say(random.choice(GAUNTLET_LINES), attacker, topic="gauntlet")

    def handle_death(self, victim, killer, data):
        if victim is None or killer is None or self.valid_duel() is None:
            return
        mod = str(data.get("MOD", "")).upper() if isinstance(data, dict) else ""
        if is_psyz(victim) and not is_bot(killer):
            line = (random.choice(GAUNTLET_LINES) if "GAUNTLET" in mod else
                    RAIL_PRAISE if "RAILGUN" in mod else random.choice(PRAISE_LINES))
            self.say(line, killer)
        elif is_psyz(killer) and not is_bot(victim):
            if "RAILGUN" in mod:
                self.say(RAIL_TAUNT, victim)
            elif "ROCKET" in mod:
                self.say(random.choice(ROCKET_TAUNTS), victim)

    def handle_game_end(self, data):
        if isinstance(data, dict) and data.get("ABORTED"):
            return
        player = self.valid_duel()
        if player:
            self.say(random.choice(END_LINES), player, force=True, topic="match_end")
        self.generation += 1

    def handle_disconnect(self, player, reason):
        if player is not None and not is_bot(player):
            self.generation += 1

    def cmd_test(self, player, msg, channel):
        self.say("Chat online. ^4GL HF^7, {player}!", player, force=True)
        return minqlx.RET_STOP_ALL
