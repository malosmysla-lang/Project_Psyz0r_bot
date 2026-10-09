import unittest
import random
from runtime.chat import ChatPolicy

class ReactionTests(unittest.TestCase):
    def policy(self):
        p = ChatPolicy(rng=random.Random(4))
        p.start('duel', 'Human', 123, 0)
        p.tick(0, 0)
        return p

    def test_human_retort_rate_limit_and_no_bot_loop(self):
        p = self.policy()
        p.opponent_chat('bot', 20, sender_steam_id=123, text='idiot', sender_is_bot=True)
        self.assertIsNone(p.tick(20, 20))
        p.opponent_chat('other', 20, sender_steam_id=999, text='idiot')
        self.assertIsNone(p.tick(20, 20))
        p.opponent_chat('reply', 20, sender_steam_id=123, text='idiot', is_reply=True)
        self.assertIsNone(p.tick(20, 20))
        p.opponent_chat('human', 20, sender_steam_id=123, text='idiot')
        self.assertIsNotNone(p.tick(20, 20))
        p.opponent_chat('human', 40, sender_steam_id=123, text='idiot')
        p.opponent_chat('human2', 40, sender_steam_id=123, text='noob')
        self.assertIsNone(p.tick(40, 40))
        p.opponent_chat('human3', 81, sender_steam_id=123, text='noob')
        self.assertIsNotNone(p.tick(81, 81))

    def test_behavior_transition_not_per_frame(self):
        p = self.policy()
        p.behavior_update('state1', 20, 'surrender_tilt')
        self.assertIsNotNone(p.tick(20, 20))
        p.behavior_update('state2', 40, 'surrender_tilt')
        self.assertIsNone(p.tick(40, 40))
        p.behavior_update('state3', 41, 'normal')
        p.behavior_update('state4', 42, 'lead_loss_tilt')
        self.assertIsNotNone(p.tick(42, 42))
        p.behavior_update('state5', 60, 'relaxed')
        self.assertIsNone(p.tick(60, 60))

    def test_polite_and_cancelled_messages(self):
        p = self.policy()
        p.opponent_chat('gg', 20, sender_steam_id=123, text='well played')
        self.assertIsNone(p.tick(20, 20))
        p.cancel()
        p.opponent_chat('late', 30, sender_steam_id=123, text='idiot')
        p.behavior_update('late_state', 30, 'surrender_tilt')
        self.assertIsNone(p.tick(30, 30))
