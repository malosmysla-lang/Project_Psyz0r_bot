import functools
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest


class LabTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.commands = []
        self.jobs = []
        self.people = []
        self.cvars = {'net_port': '27962', 'qlx_psyzLabEnabled': '1', 'fs_homepath': self.temp.name}
        outer = self
        class Base:
            def add_hook(self, *args): pass
            def get_cvar(self, key): return outer.cvars.get(key)
            def set_cvar(self, key, value): outer.cvars[key] = value
            def players(self): return outer.people
        def delay(seconds):
            def decorate(fn):
                @functools.wraps(fn)
                def queued(*args): outer.jobs.append((fn, args))
                return queued
            return decorate
        old = sys.modules.get('minqlx')
        def restore():
            if old is None: sys.modules.pop('minqlx', None)
            else: sys.modules['minqlx'] = old
        self.addCleanup(restore)
        sys.modules['minqlx'] = types.SimpleNamespace(Plugin=Base, delay=delay,
            console_command=self.commands.append, log_exception=lambda: None)
        path = Path(__file__).resolve().parents[1] / 'server/minqlx-plugins/psyz_lab.py'
        spec = importlib.util.spec_from_file_location('lab087_test', path)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def create(self): return self.module.psyz_lab()

    def setup_pair(self, p): p.setup.__wrapped__(p, p.generation)

    def test_primary_is_inert(self):
        self.cvars['net_port'] = '27960'
        p = self.create(); self.setup_pair(p)
        self.assertEqual(self.commands, [])
        self.assertFalse((Path(self.temp.name) / 'lab-events.jsonl').exists())

    def test_two_bots_and_distinct_control_blocks(self):
        p = self.create(); self.setup_pair(p)
        self.assertEqual(len(self.commands), 2)
        self.assertEqual(self.cvars['qlx_psyzFinish087'], '1')
        self.commands.clear(); p.round = 3; self.setup_pair(p)
        self.assertEqual(len(self.commands), 2)
        self.assertEqual(self.cvars['qlx_psyzFinish087'], '0')

    def test_human_pauses_without_any_map_or_kick(self):
        self.people = [types.SimpleNamespace(steam_id=76561197961758497)]
        p = self.create(); self.setup_pair(p)
        self.assertEqual(p.phase, 'paused'); self.assertEqual(self.commands, [])

    def test_round_survives_reload_and_duplicate_end(self):
        p = self.create(); self.setup_pair(p); p.on_end({}); p.on_end({})
        self.assertEqual(p.round, 1)
        other = self.create(); self.assertEqual(other.round, 1)
        records = [json.loads(l) for l in (Path(self.temp.name) / 'lab-events.jsonl').read_text().splitlines()]
        self.assertEqual(sum(r['event'] == 'game_end' for r in records), 1)

    def test_watchdog_recovers_missing_pair_as_abort(self):
        p = self.create(); self.setup_pair(p); self.commands.clear()
        p.phase = 'playing'; p.started -= 40
        p.watchdog.__wrapped__(p)
        self.assertEqual(self.commands, ['map bloodrun duel'])
        self.assertEqual(p.round, 1)
        records = [json.loads(l) for l in (Path(self.temp.name) / 'lab-events.jsonl').read_text().splitlines()]
        self.assertEqual(records[-1]['event'], 'aborted')

    def test_two_bots_have_independent_stationary_windows(self):
        p = self.create()
        def bot(slot, pos):
            return types.SimpleNamespace(id=slot, name='Psy'+str(slot), steam_id=0,
              health=100, armor=50, score=0, position=lambda: pos, velocity=lambda:(0,0,0), weapon=lambda:7)
        p.sample([bot(0,(0,0,0)), bot(1,(50,0,0))],100)
        p.sample([bot(0,(0,0,0)), bot(1,(150,0,0))],125)
        self.assertIn(0,p.warned); self.assertNotIn(1,p.warned)

    def test_ready_waits_for_real_game_start(self):
        p = self.create(); self.setup_pair(p)
        p.ready.__wrapped__(p, p.generation)
        self.assertEqual(p.phase, 'warmup')
        p.on_start({'MATCH_GUID': 'actual-match'})
        self.assertEqual(p.phase, 'playing')
        self.assertEqual(self.cvars['timelimit'], '5')

    def test_existing_bots_are_cleared_before_next_pair(self):
        kicked = []
        self.people = [types.SimpleNamespace(steam_id=0, kick=kicked.append)]
        p = self.create(); self.setup_pair(p)
        self.assertEqual(len(kicked), 1)
        self.assertEqual(self.commands, ['map bloodrun duel'])
        self.assertIsNone(p.match_id)

    def test_short_forfeit_retries_map_without_advancing_or_counting(self):
        p = self.create(); self.setup_pair(p)
        p.on_end({'GAME_LENGTH': 5})
        self.assertEqual(p.round, 0)
        self.assertEqual(p.phase, 'intermission')
        self.assertEqual(p.ended, set())


if __name__ == '__main__': unittest.main()
