"""Bounded duel chat for the isolated Psyz0r test bot.

This plugin does not spawn, rename or control bots.  It speaks only when one
Psyz0r bot and one human are present on the isolated test server.  Stock bot
chat can remain disabled so the scripted policy is the single voice.
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
)
RETORT_LINES = (
    "Talk less, time the items more, {player}.",
    "Save the rage for the rematch :-)",
    "You type well. Now show me the movement.",
)
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
    return line.replace("{player}", "^3{}^7".format(name or "player"))


def classify_chat(text):
    words = set(re.findall(r"[a-zа-я0-9]+", clean(text).lower()))
    compact = "".join(words)
    if "gg" in words or "wp" in words or "goodgame" in compact or "wellplayed" in compact:
        return "gg"
    if ("gl" in words or "hf" in words or "glhf" in compact or
            {"good", "luck"}.issubset(words) or {"have", "fun"}.issubset(words)):
        return "sport"
    rude = {"idiot", "noob", "bot", "сука", "лох", "тупой", "дебил", "говно"}
    if words & rude:
        return "retort"
    return None


class psyz_chat(minqlx.Plugin):
    def __init__(self):
        super().__init__()
        self.generation = 0
        self.last_say = float("-inf")
        self.used = set()
        self.gauntlet_damage = {}
        self.replied = set()
        self.add_hook("map", self.handle_reset)
        self.add_hook("new_game", self.handle_reset)
        self.add_hook("game_countdown", self.handle_countdown)
        self.add_hook("game_end", self.handle_game_end)
        self.add_hook("chat", self.handle_chat)
        self.add_hook("death", self.handle_death)
        self.add_hook("player_disconnect", self.handle_disconnect)
        self.add_command("psychat", self.cmd_test, 5)

    def players_safe(self):
        try:
            return self.players()
        except Exception:
            minqlx.log_exception()
            return []

    def participants(self):
        players = self.players_safe()
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
        if player is None or is_bot(player) or player is not self.valid_duel():
            return
        kind = classify_chat(message)
        if kind == "sport":
            self.say(random.choice(SPORT_REPLY), player, force=True, topic="sport_reply")
        elif kind == "gg":
            self.say(random.choice(GG_REPLY), player, force=True, topic="gg_reply")
        elif kind == "retort":
            self.say(random.choice(RETORT_LINES), player, topic="retort")

    def handle_damage(self, victim, attacker, damage, dflags, means_of_death):
        if victim is None or attacker is None or not is_psyz(victim) or is_bot(attacker):
            return
        if attacker is not self.valid_duel() or "GAUNTLET" not in str(means_of_death).upper():
            return
        key = str(getattr(attacker, "steam_id", ""))
        self.gauntlet_damage[key] = self.gauntlet_damage.get(key, 0) + max(0, int(damage))
        if self.gauntlet_damage[key] >= 25:
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
