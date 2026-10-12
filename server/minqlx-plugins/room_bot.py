"""One-bot duel lifecycle with persisted state and bounded bot attempts."""
import json
import os
import random
import re
import tempfile
import time

import minqlx

BOT_NAME = "Xaero"
BOT_TEMPLATE = "Xaero"
MANAGED_BOT_NAMES = {"Xaero", "PraccBot"}  # recognize the legacy plugin name during upgrade
BOT_SKILL = 5
BOT_CHAT_INTERVAL = 150  # seconds; only during an active 1v1 with the practice bot
BOT_CHAT_COOLDOWN = 15
OWNER_STEAM_ID = 76561197961758497

BOT_JOIN_GREETINGS = (
    "Hey, welcome! Fancy a duel, or are you still warming up?",
    "How's life treating you? Got time for a quick duel?",
    "Want me to step aside, or should we run a few rounds?",
    "Waiting for another player? You can practice on me meanwhile.",
    "Ready to duel, or should I keep you company in warm-up?",
    "I'm warmed up. How about you? One quick duel?",
    "The room's quiet. Shall we make it a match?",
)

BOT_DUEL_OPENINGS = (
    "^4GL ^7& ^4HF!",
    "^4Good luck ^7& ^4have fun!",
    "^4Good luck in our duel ^7& ^4have fun out there!",
    "^4May your aim be true ^7& ^4your duel be fun!",
    "^4Ready? Good luck ^7& ^4let's have a great duel!",
)

BOT_MATCH_END_LINES = (
    "^7GG! ^4Nice duel — you kept me on my toes.",
    "^7GG WP! ^4That was a fun fight. Well played!",
    "^4You played that duel really well. ^7GG!",
    "^4Great fight! I had to work for every frag. ^7GG WP!",
)

BOT_OPENING_LINES = (
    "Knock, knock? Sneaking and hiding with shaking hands - }:-> Very smart play! }:->",
    "If you want big red watermelons - don't plant cucumbers :-) Sorry 4 SkillZ }:->",
    "Дракон, а ты качаешься что-ли??? Я всё ревно тебя вырублю, если захочешь) Ну если дернешься...",
)

# Ordinary lines are shuffled and never repeated during one duel.
BOT_CHAT_LINES = (
    "What the fuck are you playing, {player}? You're not holding B, you're not holding mid... Oh wait, wrong game.",
    "Welcome to Finland, {player}. The ping is low. The hospital bill isn't.",
    "No matchmaking. No excuses. Just you, me, and the red armor you forgot.",
    "{player}, stop checking corners. This is Quake. Check the ceiling.",
    "{player}, I predicted your movement. All two directions.",
    "You're not low HP. You're one bad decision away from spectating.",
    "I missed on purpose. Needed to feel human for a second.",
    "I respect your strategy. Especially the part where you keep doing it.",
    "You can have the yellow armor. I've already made it red.",
    "Your aim is fine. The wall is definitely dead.",
    "You had the high ground. I had basic geometry.",
    "I don't need wallhacks. Your footsteps have a postcode.",
    "That jump looked expensive. Did it cost you all your health?",
    "Don't panic. There's plenty of time to miss another rail.",
)

# Owner/paid-lesson jokes are intentionally much rarer.
BOT_RARE_CHAT_LINES = (
    "nekitz0r - a living CS 1.6 legend. You know that, right? :-)",
    "Work on your SkillZ at Intel_maps by nekitz0r. You got that, son? {player}, I'm talking to you. }:->",
    "Born in a .cfg file. Raised by nekitz0r. Absolutely no manners.",
    "Looking for the bombsite, {player}? Same. nekitz0r still hasn't installed one.",
    "Intel maps. Questionable decisions. Welcome to the server. }:->",
    "Complaints about my aim? Contact nekitz0r. He'll tell you to practice.",
    "Behind every nekitz0r is a Sensei PsyRoZ wondering where the lesson went wrong.",
    "Sensei PsyRoZ charges $100 per lesson. My rockets deliver free feedback. }:->",
    'I asked PsyRoZ how to improve. He said "$100." Finally, a clear answer.',
    "nekitz0r learned from PsyRoZ. {player}, did you learn from the loading screen?",
    "Somewhere, Sensei PsyRoZ is watching this duel and slowly closing his eyes.",
    "$100 gets you a lesson with PsyRoZ. Running at me with a gauntlet gets you a practical demonstration.",
    "Nice shot, {player}! PsyRoZ offers no refunds for accidental talent. :-)",
    "PsyRoZ taught nekitz0r. I learned from a config file. We had different budgets.",
    "{player}, here's some advice: book a lesson with Sensei PsyRoZ for $100. :-)",
)

BOT_PRAISE_LINES = (
    "Well played. Who taught you that, and are they available?",
    "I had a plan. You appear to have deleted it.",
    "Okay, that was filthy. Respect.",
    "{player}, you're playing better than nekitz0r. Don't tell him I said that. :-)",
    'That\'s Nikolai "Agent" level already, {player}. Respect!',
)
BOT_RAIL_PRAISE = "Nice rail, {player}. I'm uninstalling my eyes."
BOT_RAIL_TAUNT = "That rail went straight into your confidence."
BOT_ROCKET_TAUNTS = (
    "{player}, that rocket was a warning shot. The next five are customer service.",
    "Nice dodge. Wrong rocket, though. }:->",
    "That wasn't a prediction rocket. You were just late.",
    "Stop running! I'm trying to discuss your extended rocket warranty.",
)
BOT_LEAVE_AFTER_DUEL_LINE = "One duel with me, then I'm off. Even bots have a better sleep schedule than nekitz0r."


def _colored_static_text(text):
    text = re.sub(r"nekitz0r", "^4nekitz0r^7", text, flags=re.IGNORECASE)
    for name in ("PsyRoZ", "Cooller", "Cooler", "Nikolai", "Agent"):
        text = re.sub(r"(?<![A-Za-z0-9_]){}(?![A-Za-z0-9_])".format(re.escape(name)),
                      "^3{}^7".format(name), text, flags=re.IGNORECASE)
    colors = {"Intel_maps": "3", "SkillZ": "3", "GG WP": "3", "GG": "3", "WP": "3",
              "$100": "3", "red armor": "1", "rockets": "1", "rocket": "1", "rail": "1"}
    alternatives = "|".join(re.escape(word) for word in sorted(colors, key=len, reverse=True))
    pattern = r"(?<![A-Za-z0-9_^])(?:{})(?![A-Za-z0-9_])".format(alternatives)
    text = re.sub(pattern, lambda match: "^{}{}^7".format(colors[next(
        word for word in colors if word.lower() == match.group(0).lower())], match.group(0)),
        text, flags=re.IGNORECASE)
    return text


def render_bot_line(template, player=None, owner_steam_id=OWNER_STEAM_ID):
    """Insert cleaned owner-aware player color and reset to white at the end."""
    rendered = _colored_static_text(template)
    if player is not None:
        raw_name = getattr(player, "name", None) or getattr(player, "clean_name", "")
        clean_name = re.sub(r"\^[0-9]", "", str(raw_name)).replace("^", "")
        try:
            is_owner = int(player.steam_id) == int(owner_steam_id)
        except (AttributeError, TypeError, ValueError):
            is_owner = False
        rendered = rendered.replace("{player}", "^{}{}^7".format("4" if is_owner else "3", clean_name))
    return "^7{}^7".format(rendered)

def is_bot(player):
    try:
        steam_id = int(player.steam_id)
        # QLDS exposes bots through PlayerInfo as 0x0140000100000000 + client ID;
        # stats events normalize the same bots to SteamID 0. Real SteamIDs use a
        # different prefix, so comparing only to zero misclassifies live bots.
        return steam_id == 0 or (steam_id & 0xFFFFFFFF00000000) == 0x0140000100000000
    except (TypeError, ValueError, AttributeError):
        return False


def is_managed_name(clean_name):
    return clean_name in MANAGED_BOT_NAMES


def transition(state, human_count, completed_duel=False, map_changed=False):
    """Pure state transition; bot actions are performed by the plugin."""
    phase = state.get("phase")
    previous_count = state.get("human_count")
    if human_count == 0:
        # A manual suppression at an already-empty server remains in force.
        # Reset only after people were present and the server becomes empty.
        reset_cycle = previous_count is not None and previous_count > 0
        if reset_cycle or (previous_count is None and not state.get("manual_suppressed")):
            state["phase"] = "empty"
            state["manual_suppressed"] = False
        elif not state.get("manual_suppressed"):
            state["phase"] = "empty"
    elif human_count >= 2:
        state["phase"] = "used"
    elif phase in (None, ""):
        state["phase"] = "used"
    elif phase == "empty":
        state["phase"] = "one_duel"
    elif phase == "one_duel" and (completed_duel or map_changed):
        state["phase"] = "used"
    state["human_count"] = human_count
    return state["phase"]


def mark_startup_bot_kicked(state, human_count):
    """Persist a one-time owner-requested startup removal and suppress respawn."""
    state["phase"] = "suppressed"
    state["manual_suppressed"] = True
    state["human_count"] = human_count
    state["startup_kick_done"] = True
    return state


class room_bot(minqlx.Plugin):
    def __init__(self):
        super().__init__()
        self.set_cvar_once("qlx_roomOwnerSteamID", str(OWNER_STEAM_ID))
        self.set_cvar_once("qlx_roomBotKickOnStartup", "0")
        home = self.get_cvar("fs_homepath", str)
        if not home:
            raise RuntimeError("room_bot requires fs_homepath")
        self._state_dir = os.path.join(home, "stats")
        os.makedirs(self._state_dir, mode=0o700, exist_ok=True)
        self._state_path = os.path.join(self._state_dir, "room_bot_state.json")
        self._state = self._load_state()
        self._startup_kick_pending = (
            self.get_cvar("qlx_roomBotKickOnStartup", str).strip() == "1"
            and not self._state.get("startup_kick_done", False)
        )
        self._attempts = set()
        self._adding = False
        self._tag_waits = 0
        self._chat_generation = 0
        self._match_generation = 0
        self._chat_lines = []
        self._rare_chat_lines = []
        self._praise_lines = []
        self._used_chat_lines = set()
        self._last_chat = 0.0
        self._join_generations = {}
        self._join_greeted = set()
        self._join_greetings = []
        self._duel_openings = []
        self._match_end_lines = []
        self._duel_opening_sent = False
        self._leave_after_duel = False
        self._disconnect_reconcile_generation = 0
        self.add_hook("map", self.handle_map)
        self.add_hook("new_game", self.handle_new_game)
        self.add_hook("game_countdown", self.handle_game_countdown)
        self.add_hook("game_end", self.handle_game_end)
        self.add_hook("death", self.handle_bot_death)
        self.add_hook("player_connect", self.handle_player_connect, priority=minqlx.PRI_HIGH)
        self.add_hook("player_loaded", self.handle_player_loaded, priority=minqlx.PRI_LOWEST)
        self.add_hook("player_disconnect", self.handle_player_disconnect)
        self.add_hook("stats", self.handle_stats)
        self.add_command("botadd", self.cmd_botadd, 5)
        self.add_command("botremove", self.cmd_botremove, 5)
        self.add_command("leaveme", self.cmd_botremove, 5)
        self.add_command("goduel", self.cmd_goduel, 5)
        self.add_command("botcolor", self.cmd_botcolor, 5)
        self._schedule_startup_reconcile()
        if self._startup_kick_pending:
            self._startup_kick_once()

    def _load_state(self):
        try:
            with open(self._state_path, "r", encoding="utf-8") as stream:
                state = json.load(stream)
            if state.get("phase") not in ("empty", "one_duel", "used", "suppressed", "manual"):
                raise ValueError("bad phase")
            return state
        except (OSError, ValueError, TypeError):
            return {"phase": None, "last_map": None, "manual_suppressed": False}

    def _save_state(self):
        os.chmod(self._state_dir, 0o700)
        fd, temporary = tempfile.mkstemp(prefix=".room-bot-", dir=self._state_dir)
        try:
            os.fchmod(fd, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(self._state, stream, separators=(",", ":"), sort_keys=True)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self._state_path)
            os.chmod(self._state_path, 0o600)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def _players(self):
        try:
            return self.players()
        except Exception:
            minqlx.log_exception()
            return []

    def _humans(self, players=None):
        return [p for p in (players if players is not None else self._players()) if not is_bot(p)]

    def _bots(self, players=None):
        return [p for p in (players if players is not None else self._players()) if is_bot(p)]

    def _managed_bots(self, players=None):
        return [p for p in self._bots(players) if is_managed_name(p.clean_name)]

    def _stop_bot_chatter(self):
        self._chat_generation += 1

    @staticmethod
    def _draw_phrase(pool, source):
        if not pool:
            pool.extend(source)
            random.shuffle(pool)
        return pool.pop()

    @minqlx.delay(8)
    def _send_join_greeting(self, steam_id, generation):
        if self._join_generations.get(steam_id) != generation:
            return
        player = None
        for item in self._humans():
            try:
                if int(item.steam_id) == steam_id:
                    player = item
                    break
            except (AttributeError, TypeError, ValueError):
                minqlx.get_logger().warning("room_bot: cannot identify a connected player during Xaero greeting")
        if player is None:
            return
        line = self._draw_phrase(self._join_greetings, BOT_JOIN_GREETINGS)
        try:
            player.tell("^7Xaero^7: {}".format(render_bot_line(line, player)))
        except Exception:
            minqlx.log_exception()

    def handle_game_countdown(self):
        self._chat_generation += 1
        self._match_generation += 1
        self._chat_lines = list(BOT_OPENING_LINES + BOT_CHAT_LINES)
        random.shuffle(self._chat_lines)
        self._rare_chat_lines = list(BOT_RARE_CHAT_LINES)
        random.shuffle(self._rare_chat_lines)
        self._praise_lines = list(BOT_PRAISE_LINES)
        random.shuffle(self._praise_lines)
        self._used_chat_lines = set()
        self._leave_after_duel = False
        humans = self._humans()
        if (not self._duel_opening_sent and len(humans) == 1
                and self._managed_bots()
                and self._state.get("phase") in ("one_duel", "manual")):
            self._duel_opening_sent = True
            line = self._draw_phrase(self._duel_openings, BOT_DUEL_OPENINGS)
            self._say(line, humans[0], force=True)
        self._bot_chatter_tick(self._chat_generation)

    def handle_game_end(self, data):
        self._stop_bot_chatter()
        self._duel_opening_sent = False
        if not isinstance(data, dict) or data.get("ABORTED"):
            return
        humans = self._humans()
        bots = self._managed_bots()
        if len(humans) != 1 or not bots:
            return
        human = humans[0]
        line = self._draw_phrase(self._match_end_lines, BOT_MATCH_END_LINES)
        self._match_generation += 1
        self._send_final_line(self._match_generation, line, human)

    @minqlx.delay(BOT_CHAT_COOLDOWN + 1)
    def _send_final_line(self, generation, line, human):
        if generation != self._match_generation:
            return
        if self._leave_after_duel:
            line += " " + BOT_LEAVE_AFTER_DUEL_LINE
        self._say(line, human, force=True)

    def _say(self, line, player=None, force=False):
        now = time.monotonic()
        if not force and (
            line in self._used_chat_lines or now - self._last_chat < BOT_CHAT_COOLDOWN
        ):
            return False
        self._last_chat = now
        if line in BOT_OPENING_LINES:
            self.msg("^1Xaero: {}^7".format(line))
        else:
            try:
                owner_steam_id = self.get_cvar("qlx_roomOwnerSteamID", int)
            except AttributeError:
                owner_steam_id = OWNER_STEAM_ID
            message = render_bot_line(line, player, owner_steam_id)
            self.msg("^7Xaero^7: {}".format(message))
        self._used_chat_lines.add(line)
        return True

    def cmd_botcolor(self, player, msg, channel):
        """Send a one-time color proof through the normal bot chat renderer."""
        try:
            owner_steam_id = int(self.get_cvar("qlx_roomOwnerSteamID", int))
            is_owner = int(player.steam_id) == owner_steam_id
        except (AttributeError, TypeError, ValueError):
            is_owner = False
        if not is_owner:
            player.tell("This check is owner-only.")
            return minqlx.RET_STOP_ALL
        self._say(
            "{player} | nekitz0r | Intel_maps SkillZ GG WP $100 | rockets rail red armor",
            player,
        )
        return minqlx.RET_STOP_ALL

    @minqlx.delay(BOT_CHAT_INTERVAL)
    def _bot_chatter_tick(self, generation):
        if generation != self._chat_generation:
            return
        try:
            humans = self._humans()
            if self.game.state != "in_progress" or len(humans) != 1 or not self._managed_bots():
                return
            if not self._chat_lines:
                return
            use_rare = bool(self._rare_chat_lines) and random.randrange(6) == 0
            line = self._rare_chat_lines.pop() if use_rare else self._chat_lines.pop()
            self._say(line, humans[0])
            self._bot_chatter_tick(generation)
        except Exception:
            minqlx.log_exception()

    def handle_bot_death(self, victim, killer, data):
        if killer is None:
            return
        try:
            if self.game.state != "in_progress":
                return
        except Exception:
            return
        mod = str(data.get("MOD", "")).upper() if isinstance(data, dict) else ""
        if is_bot(victim) and victim.clean_name == BOT_NAME and not is_bot(killer):
            if "RAILGUN" in mod:
                line = BOT_RAIL_PRAISE
            else:
                if not self._praise_lines:
                    return  # one praise per supplied line per duel; no repeats
                line = self._praise_lines.pop()
            self._say(line, killer)
        elif is_bot(killer) and killer.clean_name == BOT_NAME and not is_bot(victim):
            if "RAILGUN" in mod:
                self._say(BOT_RAIL_TAUNT, victim)
            elif "ROCKET" in mod:
                self._say(random.choice(BOT_ROCKET_TAUNTS), victim)

    def handle_map(self, mapname, factory):
        self._stop_bot_chatter()
        self._duel_opening_sent = False
        self._disconnect_reconcile_generation += 1
        # minqlx appends its credit/link to loading-screen configstrings before
        # dispatching the map hook. Restore the arena's original subtitles.
        for index, attr in ((678, "_map_subtitle1"), (679, "_map_subtitle2")):
            original = getattr(minqlx, attr, None)
            if original is not None:
                minqlx.set_configstring(index, original)
        previous = self._state.get("last_map")
        humans = self._humans()
        phase = transition(self._state, len(humans), map_changed=bool(previous and previous != mapname))
        self._state["last_map"] = mapname
        if phase == "used" and humans:
            self._remove_managed("Map changed; the practice bot will not return this session.")
        self._save_state()
        self._schedule_reconcile()

    def handle_new_game(self):
        self._schedule_reconcile()

    def handle_player_connect(self, player):
        self._disconnect_reconcile_generation += 1
        if not is_bot(player):
            try:
                steam_id = int(player.steam_id)
                self._join_generations[steam_id] = self._join_generations.get(steam_id, 0) + 1
                self._join_greeted.discard(steam_id)
            except (AttributeError, TypeError, ValueError):
                minqlx.get_logger().warning("room_bot: cannot identify joining player for Xaero greeting")
        self._schedule_reconcile()

    def handle_player_loaded(self, player):
        self._disconnect_reconcile_generation += 1
        if not is_bot(player):
            try:
                steam_id = int(player.steam_id)
            except (AttributeError, TypeError, ValueError):
                minqlx.get_logger().warning("room_bot: cannot identify loaded player for Xaero greeting")
            else:
                if steam_id not in self._join_greeted:
                    self._join_greeted.add(steam_id)
                    generation = self._join_generations.get(steam_id, 0)
                    self._send_join_greeting(steam_id, generation)
        self._schedule_reconcile()

    def handle_player_disconnect(self, player, reason):
        if not is_bot(player):
            try:
                steam_id = int(player.steam_id)
                self._join_generations[steam_id] = self._join_generations.get(steam_id, 0) + 1
                self._join_greeted.discard(steam_id)
            except (AttributeError, TypeError, ValueError):
                minqlx.get_logger().warning("room_bot: cannot identify disconnecting player")
        if is_bot(player) and player.clean_name == BOT_NAME:
            self._stop_bot_chatter()
        # An admin's manual kick of the practice bot suppresses re-addition.
        if (is_bot(player) and player.clean_name == BOT_NAME
                and self._state.get("phase") in ("empty", "one_duel")):
            self._state["phase"] = "suppressed"
            self._state["manual_suppressed"] = True
            self._save_state()
        self._schedule_reconcile()
        # QLDS may still include a disconnecting client in players() during the
        # first delayed callback. Retry briefly, then stop; reconnect/map events
        # invalidate the old retry chain. Spectators count as humans too.
        self._disconnect_reconcile_generation += 1
        self._reconcile_after_disconnect(self._disconnect_reconcile_generation, 0)

    def handle_stats(self, event):
        if not isinstance(event, dict) or event.get("TYPE") != "MATCH_REPORT":
            return
        data = event.get("DATA") or {}
        if data.get("GAME_TYPE") == "DUEL" and data.get("ABORTED") is False:
            self._complete_duel()

    @minqlx.delay(0.2)
    def _complete_duel(self):
        if self._state.get("phase") == "one_duel":
            self._stop_bot_chatter()
            self._state["phase"] = "used"
            self._save_state()
            self._leave_after_duel = self._remove_managed()

    @minqlx.delay(0.5)
    def _schedule_reconcile(self):
        self._reconcile()

    @minqlx.delay(5)
    def _schedule_startup_reconcile(self):
        self._reconcile()

    @minqlx.delay(3)
    def _startup_kick_once(self, attempt=0):
        if not self._startup_kick_pending:
            return
        bots = self._managed_bots()
        if bots:
            self._state = mark_startup_bot_kicked(self._state, len(self._humans()))
            self._save_state()
            self._startup_kick_pending = False
            self._remove_managed()
            minqlx.get_logger().info("room_bot: completed the one-time startup Xaero removal")
            return
        if attempt < 15:
            self._startup_kick_once(attempt + 1)
        else:
            self._startup_kick_pending = False
            minqlx.get_logger().warning("room_bot: startup Xaero was not present for the requested one-time removal")

    @minqlx.delay(1)
    def _reconcile_after_disconnect(self, generation, attempt):
        if generation != self._disconnect_reconcile_generation:
            return
        if not self._humans():
            self._reconcile()
            return
        if attempt < 19:
            self._reconcile_after_disconnect(generation, attempt + 1)

    def _reconcile(self):
        players = self._players()
        humans = self._humans(players)
        phase = transition(self._state, len(humans))
        self._save_state()
        if not humans:
            if not self._state.get("manual_suppressed"):
                self._ensure_bot()
            return
        if len(humans) >= 2:
            self._remove_managed("Another player joined; practice bot removed.")
            return
        if phase == "one_duel":
            self._ensure_bot()

    def _ensure_bot(self, force=False):
        if self._adding:
            return
        bots = self._bots()
        managed = self._managed_bots(bots)
        if managed:
            if len(managed) > 1:
                for extra in managed[1:]:
                    extra.kick("Duplicate practice bot")
            return
        # Adopt a sole existing bot only while the server is empty or when
        # there is exactly one human and a pending one-duel session.
        humans = self._humans()
        if len(bots) == 1 and (not humans or self._state.get("phase") in ("one_duel", "manual")):
            try:
                bots[0].name = BOT_NAME
            except Exception:
                minqlx.log_exception()
            return
        if bots:
            return
        mapname = str(self.get_cvar("mapname", str) or "unknown").lower()
        attempt_key = (os.getpid(), mapname)
        if not force and attempt_key in self._attempts:
            return
        self._attempts.add(attempt_key)
        self._adding = True
        self._tag_waits = 0
        minqlx.console_command("addbot {} {} red".format(BOT_TEMPLATE, BOT_SKILL))
        self._tag_added_bot()

    @minqlx.delay(1)
    def _tag_added_bot(self, retries=0):
        bots = self._bots()
        humans = self._humans()
        if len(humans) >= 2:
            for bot in bots:
                bot.kick("Another player joined")
            self._state["phase"] = "used"
            self._save_state()
            self._adding = False
            return
        if bots:
            try:
                bots[0].name = BOT_NAME
                for extra in bots[1:]:
                    extra.kick("Duplicate practice bot")
                self._adding = False
                self._state["phase"] = "empty" if not self._humans() else self._state.get("phase")
                self._save_state()
                self.msg("Practice bot ready.")
                return
            except Exception:
                minqlx.log_exception()
        if retries < 4 and len(humans) <= 1 and not bots:
            self._tag_added_bot(retries + 1)
            return
        self._adding = False
        minqlx.get_logger().warning("room_bot: Xaero skill 5 unavailable on map %s after bounded checks; will wait for the next map/session", self.get_cvar("mapname", str))

    def _remove_managed(self, message=None):
        managed = self._managed_bots()
        if not managed:
            return False
        self._stop_bot_chatter()
        for bot in managed:
            try:
                bot.kick("Practice bot removed")
            except Exception:
                minqlx.log_exception()
        if message:
            self.msg(message)
        return True

    def cmd_botadd(self, player, msg, channel):
        humans = self._humans()
        if len(humans) > 1:
            player.tell("Bot not added; the server has multiple people.")
            return minqlx.RET_STOP_ALL
        bots = self._bots()
        if len(bots) > 1:
            player.tell("Multiple bots already present; remove extras first.")
            return minqlx.RET_STOP_ALL
        if len(bots) == 1:
            if not self._managed_bots(bots):
                try:
                    bots[0].name = BOT_NAME
                except Exception:
                    minqlx.log_exception()
            player.tell("Practice bot is already present.")
            return minqlx.RET_STOP_ALL
        self._state["phase"] = "manual" if humans else "empty"
        self._state["manual_suppressed"] = False
        self._state["human_count"] = len(humans)
        self._save_state()
        self._ensure_bot(force=True)
        player.tell("Practice bot requested.")
        return minqlx.RET_STOP_ALL

    def cmd_botremove(self, player, msg, channel):
        self._state["phase"] = "suppressed"
        self._state["manual_suppressed"] = True
        self._state["human_count"] = len(self._humans())
        self._save_state()
        bots = self._managed_bots()
        if not bots:
            all_bots = self._bots()
            if len(all_bots) == 1:
                bots = all_bots
        for bot in bots:
            try:
                bot.kick("Removed by admin")
            except Exception:
                minqlx.log_exception()
        player.tell("Practice bot removed; auto-add paused until the server empties.")
        return minqlx.RET_STOP_ALL

    def cmd_goduel(self, player, msg, channel):
        humans = self._humans()
        if len(humans) != 1:
            player.tell("A practice duel requires exactly one human player.")
            return minqlx.RET_STOP_ALL
        if self.game.state == "in_progress":
            player.tell("Wait until the current match ends before starting a practice duel.")
            return minqlx.RET_STOP_ALL

        bots = self._bots()
        if len(bots) > 1:
            player.tell("Multiple bots are present; remove extras before starting a practice duel.")
            return minqlx.RET_STOP_ALL
        if bots and not self._managed_bots(bots):
            player.tell("Another bot is already present; an admin must remove it first.")
            return minqlx.RET_STOP_ALL

        self._state["phase"] = "one_duel"
        self._state["manual_suppressed"] = False
        self._state["human_count"] = 1
        self._save_state()
        if bots:
            player.tell("Practice bot is ready; it will leave after this duel.")
        else:
            self._ensure_bot(force=True)
            player.tell("Practice duel requested; the bot will leave after the match.")
        return minqlx.RET_STOP_ALL
