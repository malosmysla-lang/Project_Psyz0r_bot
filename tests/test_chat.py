import random
import unittest
from runtime.chat import ChatPolicy, render


class ChatTests(unittest.TestCase):
    def policy(self):
        p = ChatPolicy(rng=random.Random(3))
        p.start('duel-1', '^1Human', 123, 0)
        return p

    def test_catalog(self):
        p = self.policy()
        self.assertEqual(len(p.lines), 51)
        self.assertEqual(sum('$100' in x['text'] and x['enabled'] for x in p.lines.values()), 1)
        self.assertFalse(p.lines['J01']['enabled'])
        self.assertIn('one bad decision', p.lines['T06']['text'])

    def test_start_once_and_cooldown(self):
        p = self.policy()
        text = p.tick(0, 0)
        self.assertTrue(text.startswith('^1'))
        self.assertEqual(text.count('^'), 2)
        p.start('duel-1', 'Human', 123, 1)
        self.assertIsNone(p.tick(1, 1))
        p.death('kill1', 10, bot_killed_human=True, weapon='railgun', opponent_steam_id=123)
        self.assertIsNone(p.tick(10, 10))
        self.assertIsNone(p.tick(16, 16))

    def test_event_filter_and_dedup(self):
        p = self.policy()
        p.tick(0, 0)
        p.death('x', 20, bot_killed_human=True, weapon='railgun', opponent_steam_id=999)
        self.assertIsNone(p.tick(20, 20))
        p.death('x', 20, bot_killed_human=True, weapon='railgun', opponent_steam_id=123)
        self.assertIn('confidence', p.tick(20, 20))
        p.death('x', 40, bot_killed_human=True, weapon='rocket', opponent_steam_id=123)
        self.assertIsNone(p.tick(40, 40))

    def test_end_priority_replace_and_cancel(self):
        p = self.policy()
        p.tick(0, 0)
        p.death('x', 20, bot_killed_human=True, weapon='railgun', opponent_steam_id=123)
        p.end(20, 'human_win', leaving=True)
        self.assertIn('then I\'m off', p.tick(20, 20))
        p.end(40, 'bot_win')
        self.assertIsNone(p.tick(40, 40))
        p.start('duel-2', 'Human', 123, 41)
        p.end(42, 'human_win')
        p.cancel()
        self.assertIsNone(p.tick(60, 60))

    def test_end_deferred_and_expired(self):
        p = self.policy()
        p.tick(0, 0)
        p.end(2, 'human_win')
        self.assertIsNone(p.tick(2, 2))
        self.assertIn('GG', p.tick(15, 15))
        p = self.policy()
        p.tick(0, 0)
        p.end(2, 'human_win')
        self.assertIsNone(p.tick(20, 20))

    def test_owner_and_missing_opponent(self):
        p = self.policy()
        line = p.lines['P04']
        self.assertIsNone(render(line, None, None, 123))
        self.assertIn('^4Human^7', render(line, '^1Human', 123, 123))
        self.assertIn('^3Human^7', render(line, '^1Human', 124, 123))
        p.steam_id = p.config['owner_steam_id']
        p.pending.clear()
        p.offer(2, ['P04'], 20)
        self.assertFalse(p.pending)

    def test_rare_once_no_repeats_and_state_reset(self):
        p = self.policy()
        p.config['rare_probability'] = 1
        p.tick(0, 0)
        self.assertIsNotNone(p.tick(150, 150))
        self.assertTrue(p.rare_used)
        for now in range(300, 2550, 150):
            p.tick(now, now)
        self.assertEqual(sum(p.lines[i]['category'] == 'rare' for i in p.used), 1)
        self.assertIsNone(p.tick(2550, 2550))
        p.start('new-duel', 'Other', 999, 2500)
        self.assertFalse(p.rare_used)
        self.assertFalse(p.events)

    def test_unknown_and_aborted_results(self):
        for result, aborted in [(None, False), ('bot_win', True)]:
            p = self.policy()
            p.tick(0, 0)
            p.end(20, result, aborted=aborted)
            self.assertIsNone(p.tick(20, 20))


if __name__ == '__main__':
    unittest.main()
