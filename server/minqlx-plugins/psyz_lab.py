"""Private 27962 overnight measurements; no API calls or model-training claims."""
import json
import math
import time
import uuid
from pathlib import Path
import minqlx

VERSION = '0.8.7'
PAIRS = (
    ((('Xaero', 'Lab_Xaero'), ('Psyz0r', 'Psyz0r_bot')), 1, 'xaero_psy_finish'),
    ((('Psyz0r', 'Psyz0r_bot'), ('Xaero', 'Lab_Xaero')), 1, 'psy_xaero_finish'),
    ((('Psyz0r', 'Psyz0r_bot'), ('Psyz0r', 'Psyz0r')), 1, 'psy_mirror_finish'),
    ((('Xaero', 'Lab_Xaero'), ('Psyz0r', 'Psyz0r_bot')), 0, 'stock_control'),
)


def is_bot(player):
    try:
        sid = int(player.steam_id)
        return sid == 0 or (sid & 0xFFFFFFFF00000000) == 0x0140000100000000
    except (AttributeError, TypeError, ValueError):
        return False


class psyz_lab(minqlx.Plugin):
    def __init__(self):
        self.round = 0
        self.generation = 0
        self.run_id = uuid.uuid4().hex[:12]
        self.match_id = None
        self.phase = 'idle'
        self.changed = time.monotonic()
        self.started = self.changed
        self.positions = {}
        self.warned = set()
        self.ended = set()
        self.block = 'not_started'
        self.add_hook('map', self.on_map)
        self.add_hook('game_end', self.on_end)
        self.add_hook('game_start', self.on_start)
        self.add_hook('death', self.on_death)
        self.add_hook('stats', self.on_stats)
        if self.enabled():
            try:
                self.round = int(json.loads(self.state_path.read_text())['next_round'])
            except (OSError, ValueError, KeyError, TypeError):
                pass
        self.on_map()
        self.watchdog()

    @property
    def home(self):
        return Path(self.get_cvar('fs_homepath'))

    @property
    def state_path(self):
        return self.home / 'lab-state087.json'

    def enabled(self):
        return self.get_cvar('net_port') == '27962' and self.get_cvar('qlx_psyzLabEnabled') == '1'

    def humans(self):
        # Unknown identities fail closed: never mistake a spectator for a bot.
        return [p for p in self.players() if not is_bot(p)]

    def save_state(self):
        tmp = self.state_path.with_suffix('.tmp')
        tmp.write_text(json.dumps(dict(next_round=self.round, version=VERSION)), encoding='utf-8')
        tmp.replace(self.state_path)

    def record(self, event, data):
        if not self.enabled():
            return
        try:
            path = self.home / 'lab-events.jsonl'
            # Bound disk use on the small VPS: active log plus three rotations.
            if path.exists() and path.stat().st_size > 48 * 1024 * 1024:
                for i in range(2, 0, -1):
                    source = path.with_name(path.name + '.' + str(i))
                    if source.exists():
                        source.replace(path.with_name(path.name + '.' + str(i + 1)))
                path.replace(path.with_name(path.name + '.1'))
            row = dict(time=time.time(), version=VERSION, run_id=self.run_id,
                       match_id=self.match_id, round=self.round, block=self.block,
                       event=event, data=data)
            with path.open('a', encoding='utf-8') as out:
                out.write(json.dumps(row, default=str) + '\n')
        except OSError:
            minqlx.log_exception()

    def on_map(self, *args):
        if not self.enabled():
            return
        self.generation += 1
        self.phase = 'setup'
        self.changed = time.monotonic()
        self.positions.clear()
        self.warned.clear()
        self.setup(self.generation)

    @minqlx.delay(5)
    def setup(self, generation):
        if not self.enabled() or generation != self.generation:
            return
        if self.humans():
            self.phase = 'paused'
            self.record('paused_for_human', {})
            return
        old_bots = [p for p in self.players() if is_bot(p)]
        if old_bots:
            # Replacing bots inside a running duel produces an engine forfeit.
            # Clear them before a fresh map; never start the next pair in that intermission.
            self.match_id = None
            self.phase = 'resetting'
            self.changed = time.monotonic()
            for p in old_bots:
                p.kick('Lab next controlled pair')
            minqlx.console_command('map bloodrun duel')
            return
        pair, finish, self.block = PAIRS[self.round % len(PAIRS)]
        self.match_id = self.run_id + '-' + str(self.round)
        self.set_cvar('qlx_psyzFinish087', str(finish))
        for model, name in pair:
            minqlx.console_command('addbot {} 5 free 0 {}'.format(model, name))
        self.phase = 'warmup'
        self.changed = self.started = time.monotonic()
        self.record('pair', dict(pair=pair, finish087=finish, automatic_learning=False))
        self.ready(generation)

    @minqlx.delay(4)
    def ready(self, generation):
        if self.enabled() and generation == self.generation and not self.humans():
            minqlx.console_command('allready')
            # Only the real game_start event confirms that allready took effect.
            self.changed = time.monotonic()

    def on_start(self, data):
        if not self.enabled() or self.humans() or not self.match_id:
            return
        # Factory loading can overwrite config limits; set them after the real game start.
        self.set_cvar('timelimit', '5')
        self.set_cvar('fraglimit', '20')
        self.phase = 'playing'
        self.started = self.changed = time.monotonic()
        self.record('game_start', dict(detail=data, timelimit=5, fraglimit=20))

    def on_end(self, data):
        if not self.enabled() or self.humans() or not self.match_id or self.match_id in self.ended:
            return
        # Kicking old warmup bots emits a five-second forfeit. It is not a played duel.
        if isinstance(data, dict) and data.get('GAME_LENGTH') is not None and data['GAME_LENGTH'] < 30:
            self.record('ignored_short_end', dict(result=data))
            self.phase = 'intermission'
            self.changed = time.monotonic()
            self.next_map(self.generation)
            return
        self.ended.add(self.match_id)
        if len(self.ended) > 64:
            self.ended = {self.match_id}
        self.record('game_end', dict(result=data, scores=[dict(name=p.name, score=p.score) for p in self.players()]))
        self.round += 1
        self.save_state()
        self.phase = 'intermission'
        self.changed = time.monotonic()
        self.next_map(self.generation)

    @minqlx.delay(10)
    def next_map(self, generation):
        if self.enabled() and generation == self.generation and not self.humans():
            minqlx.console_command('map bloodrun duel')

    def recover(self, reason):
        # An aborted experiment is never counted as a completed game.
        if not self.enabled() or self.humans():
            return
        self.record('aborted', dict(reason=reason))
        self.round += 1
        self.save_state()
        self.phase = 'recovering'
        self.changed = time.monotonic()
        minqlx.console_command('map bloodrun duel')

    @minqlx.delay(10)
    def watchdog(self):
        if not self.enabled():
            return
        try:
            now = time.monotonic()
            if self.humans():
                if self.phase != 'paused':
                    self.record('paused_for_human', {})
                self.phase = 'paused'
                self.changed = now
            elif self.phase == 'paused':
                self.recover('resume_after_human')
            elif self.phase == 'playing':
                bots = [p for p in self.players() if is_bot(p)]
                if len(bots) != 2 and now - self.started > 30:
                    self.recover('expected_two_bots')
                elif now - self.started > 18 * 60:
                    self.recover('match_wallclock_limit')
                else:
                    self.sample(bots, now)
            elif now - self.changed > 60:
                self.recover('phase_timeout_' + self.phase)
        except Exception:
            minqlx.log_exception()
        finally:
            self.watchdog()

    def sample(self, bots, now):
        rows = []
        for p in bots:
            try:
                pos = tuple(float(v) for v in p.position())
                vel = tuple(float(v) for v in p.velocity())
                speed = math.sqrt(sum(v*v for v in vel[:2]))
                key = int(p.id)
                previous = self.positions.get(key)
                stationary_since = previous[1] if previous and math.dist(pos, previous[0]) < 24 else now
                self.positions[key] = (pos, stationary_since)
                stationary = round(now - stationary_since, 1)
                # Waiting at an item is not automatically a collision stall.
                if stationary >= 20 and key not in self.warned:
                    self.record('stationary_candidate', dict(slot=key, name=p.name, seconds=stationary, position=pos))
                    self.warned.add(key)
                if stationary == 0:
                    self.warned.discard(key)
                rows.append(dict(slot=key, name=p.name, health=p.health, armor=p.armor,
                                 weapon=p.weapon(), score=p.score, position=pos,
                                 speed=round(speed, 2), stationary_seconds=stationary))
            except (AttributeError, TypeError, ValueError):
                continue
        self.record('sample', dict(players=rows, phase=self.phase))

    def on_death(self, victim, killer, data):
        if self.enabled() and not self.humans():
            self.record('death', dict(victim=getattr(victim, 'name', None), killer=getattr(killer, 'name', None), detail=data))

    def on_stats(self, data):
        if self.enabled() and not self.humans() and isinstance(data, dict) and data.get('TYPE') == 'PLAYER_STATS':
            self.record('player_stats', data)
