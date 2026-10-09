import json
from pathlib import Path
import random
import subprocess
import tempfile
import unittest
from runtime.chat import ChatPolicy

class EventChatTests(unittest.TestCase):
    def policy(self):
        p = ChatPolicy(rng=random.Random(1))
        p.config['gauntlet_reply_probability'] = 1
        p.config['weapon_item_probability'] = 1
        p.start('match', 'Human', 123, 0)
        p.pending.clear()
        return p

    def record(self, reason, source='synthetic_test'):
        return dict(opponent_id='123', source=source, reason=reason)

    def test_selection_and_unconfirmed_events_never_reply(self):
        p = self.policy()
        for i, reason in enumerate(('weapon_selected', 'near_miss', 'rejected_unverified_event')):
            p.interaction_record(i, 1, self.record(reason))
        p.interaction_record(10, 1, self.record('revenge_started', ''))
        self.assertIsNone(p.tick(1, 1))

    def test_damage_probability_topic_interval_and_no_repeat(self):
        p = self.policy()
        p.interaction_record(1, 1, self.record('gauntlet_damage_below_threshold'))
        first = p.tick(1, 1)
        self.assertIsNotNone(first)
        p.interaction_record(1, 31, self.record('revenge_started'))
        self.assertIsNone(p.tick(31, 31))
        p.interaction_record(2, 25, self.record('revenge_started'))
        self.assertIsNone(p.tick(25, 25))
        p.interaction_record(3, 31, self.record('revenge_started'))
        self.assertNotEqual(first, p.tick(31, 31))
        p.config['gauntlet_reply_probability'] = 0
        p.interaction_record(4, 61, self.record('revenge_started'))
        self.assertIsNone(p.tick(61, 61))

    def test_corpse_reply_deferred_once_expiry_and_priority(self):
        p = self.policy()
        p.interaction_record(1, 1, self.record('corpse_episode_ignored'))
        p.interaction_record(2, 2, self.record('same_corpse_episode_ignored'))
        self.assertIsNone(p.tick(2, 2))
        p.interaction_record(3, 3, self.record('gauntlet_damage_below_threshold'))
        self.assertIsNotNone(p.tick(3, 3))
        p.interaction_record(4, 4, self.record('corpse_retaliation_enabled'))
        self.assertIsNone(p.tick(4, 4))
        p.weapon_item_offer(['K01'], 23)
        self.assertIsNotNone(p.tick(23, 23))
        self.assertEqual(p.lines[p.last_line]['category'], 'corpse_reaction')
        p.interaction_record(5, 43, self.record('corpse_retaliation_enabled'))
        self.assertIsNone(p.tick(43, 43))
        p = self.policy()
        p.last_time = 100
        p.interaction_record(6, 1, self.record('corpse_retaliation_enabled'))
        self.assertIsNone(p.tick(32, 32))
        self.assertFalse(p.pending)

    def test_item_weapon_shared_cooldown_and_match_reset(self):
        p = self.policy()
        p.item_event(1, 1, opponent_steam_id=123, kind='red', perceptible=False)
        self.assertIsNone(p.tick(1, 1))
        p.item_event(2, 1, opponent_steam_id=123, kind='red', perceptible=True)
        self.assertIsNotNone(p.tick(1, 1))
        p.death(3, 21, opponent_steam_id=123, bot_killed_human=True, weapon='railgun')
        self.assertIsNone(p.tick(21, 21))
        p.death(4, 121, opponent_steam_id=123, bot_killed_human=True, weapon='railgun')
        self.assertIsNotNone(p.tick(121, 121))
        p.start('new', 'Other', 456, 122)
        self.assertFalse(p.interactions)
        p.forget_opponent(456)
        self.assertFalse(p.present)

    def test_real_cpp_trace_to_existing_chat_policy_offline(self):
        exe = Path(__file__).resolve().parents[1] / 'out/msvc-x64/Debug/reaction_sandbox.exe'
        if not exe.exists():
            self.skipTest('Build reaction_sandbox first')
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'journal.jsonl'
            subprocess.run([str(exe), str(path)], check=True)
            records = [json.loads(line) for line in path.read_text().splitlines()]
        p = self.policy()
        sent = []
        for i, record in enumerate(records):
            self.assertFalse(record['game_command_sent'])
            p.decision_record(i, record['time'], record)
            message = p.tick(record['time'], record['time'])
            if message:
                sent.append(p.lines[p.last_line]['category'])
        p.tick(52, 52)
        self.assertEqual(sent, ['gauntlet_reaction', 'gauntlet_reaction'])
        self.assertEqual(p.lines[p.last_line]['category'], 'corpse_reaction')
        self.assertEqual(records[1]['reaction_reason'], 'gauntlet_finish_attempt')

if __name__ == '__main__':
    unittest.main()
