from dataclasses import replace
import copy
import unittest
from runtime.difficulty import DifficultySession, DuelResult, explicit_answer
from runtime.chat import ChatPolicy


class DifficultyTests(unittest.TestCase):
    def result(self, match='one', **kwargs):
        r = DuelResult(match, '123', 'bloodrun', 5, 20, 600, 40, verified=True)
        return replace(r, **kwargs)

    def session(self, level=3):
        s = DifficultySession()
        s.levels['123'] = level
        self.assertEqual(s.begin('one', '123', 'bloodrun', 0), level)
        return s

    def test_new_players_level_three_and_frozen_match(self):
        s = DifficultySession()
        self.assertEqual(s.begin('one', '123', 'bloodrun', 0), 3)
        self.assertEqual(s.begin('one', '123', 'bloodrun', 10), 3)
        self.assertEqual(s.profile('123')['level'], 3)
        self.assertFalse(s.profile('123')['execution_enabled'])
        self.assertIsNone(s.profile('123')['accuracy_percent'])
        s.cancel()
        self.assertEqual(s.begin('two', 'other', 'sinister', 20), 3)

    def test_up_and_down_one_step_only_next_map_with_consent(self):
        for bot, human, expected in [(5, 20, 4), (20, 5, 2)]:
            s = self.session()
            self.assertIn(f'{expected}-м', s.finish(self.result(bot_frags=bot, human_frags=human), 600))
            self.assertEqual(s.level('123'), 3)
            s.mark_sent(600)
            self.assertTrue(s.answer('123', 'да', 601))
            self.assertEqual(s.level('123'), 3)
            self.assertEqual(s.begin('two', '123', 'sinister', 610), expected)

    def test_no_change_without_consent_or_on_same_map(self):
        for answer, next_map in [(None, 'sinister'), ('gg', 'sinister'), ('нет', 'sinister'), ('да', 'bloodrun')]:
            s = self.session()
            s.finish(self.result(), 600)
            s.mark_sent(600)
            if answer is not None:
                s.answer('123', answer, 601)
            self.assertEqual(s.begin('two', '123', next_map, 610), 3)

    def test_bounds_and_close_scores(self):
        for level, bot, human in [(5, 1, 30), (1, 30, 1), (3, 10, 12), (3, 30, 25)]:
            s = self.session(level)
            self.assertIn('Реванш', s.finish(self.result(bot_frags=bot, human_frags=human), 600))
            self.assertEqual(s.pending['next_level'], level)

    def test_unreliable_matches_do_not_adapt(self):
        for fields in [dict(forfeit=True), dict(intentional_tilt=True), dict(combat_samples=0), dict(active_seconds=10)]:
            s = self.session()
            self.assertIsNotNone(s.finish(self.result(**fields), 600))
            self.assertEqual(s.pending['next_level'], 3)
        for fields in [dict(aborted=True), dict(full_duel=False), dict(verified=False), dict(leaving=True)]:
            s = self.session()
            self.assertIsNone(s.finish(self.result(**fields), 600))
            self.assertIsNone(s.pending)

    def test_one_question_human_identity_deadline_and_sent_gate(self):
        s = self.session()
        r = self.result()
        self.assertIsNotNone(s.finish(r, 600))
        self.assertIsNone(s.finish(r, 601))
        self.assertIsNone(s.answer('123', 'да', 601))
        s.mark_sent(602)
        self.assertIsNone(s.answer('999', 'да', 603))
        self.assertIsNone(s.answer('123', 'да', 603, human=False))
        self.assertIsNone(s.answer('123', 'да', 700))
        self.assertEqual(s.begin('two', '123', 'sinister', 701), 3)

    def test_ambiguous_answers(self):
        for phrase in ['gg', 'GG WP', 'да нет', 'может быть', 'не знаю', 'yes but not now', 'он сказал да']:
            self.assertIsNone(explicit_answer(phrase))
        self.assertTrue(explicit_answer('^3Давай ещё!'))
        self.assertFalse(explicit_answer('NO thanks.'))

    def test_acceptance_can_be_revoked_and_player_levels_remain_separate(self):
        s = self.session()
        s.finish(self.result(), 600)
        s.mark_sent(600)
        self.assertTrue(s.answer('123', 'да', 601))
        self.assertFalse(s.answer('123', 'нет', 602))
        self.assertEqual(s.begin('two', '123', 'sinister', 610), 3)
        s.cancel()
        s.levels['123'] = 4
        s.cancel(opponent='123')
        self.assertEqual(s.begin('three', 'other', 'bloodrun', 700), 3)
        self.assertEqual(s.level('123'), 4)

    def test_config_rejects_unapproved_accuracy_and_bad_levels(self):
        c = copy.deepcopy(DifficultySession().config)
        c['profiles'][0]['accuracy_percent'] = 50
        with self.assertRaises(ValueError):
            DifficultySession(c)
        c = copy.deepcopy(DifficultySession().config)
        c['profiles'][0]['level'] = 2
        with self.assertRaises(ValueError):
            DifficultySession(c)

    def test_result_identity_and_invalid_evidence(self):
        s = self.session()
        with self.assertRaises(ValueError):
            s.finish(self.result(opponent_id='other'), 600)
        with self.assertRaises(ValueError):
            s.finish(self.result(active_seconds=float('nan')), 600)
        self.assertIsNotNone(s.active)

    def test_existing_chat_integration_no_double_final_question(self):
        p = ChatPolicy()
        p.start('one', 'Human', '123', 0, map_id='bloodrun')
        p.tick(0, 0)
        p.end(600, 'human_win', summary=self.result())
        text = p.tick(600, 600)
        self.assertIn('4-м', text)
        p.end(601, 'human_win', summary=self.result())
        self.assertIsNone(p.tick(630, 630))
        p.opponent_chat(1, 601, sender_steam_id='123', text='gg')
        self.assertFalse(p.difficulty.pending['accepted'])
        p.opponent_chat(2, 602, sender_steam_id='123', text='да')
        self.assertTrue(p.difficulty.pending['accepted'])
        self.assertEqual(p.difficulty.level('123'), 3)
        p.cancel(preserve_rematch=True)  # Normal post-final map transition, not disconnect.
        p.start('two', 'Human', '123', 610, map_id='sinister')
        self.assertEqual(p.difficulty.level('123'), 4)

    def test_leaving_no_question_and_disconnect_cancels(self):
        p = ChatPolicy()
        p.start('one', 'Human', '123', 0, map_id='bloodrun')
        p.end(600, 'human_win', leaving=True, summary=self.result(leaving=True, forfeit=True))
        self.assertNotIn('Реванш', p.tick(600, 600))
        self.assertIsNone(p.difficulty.pending)
        p = ChatPolicy()
        p.start('one', 'Human', '123', 0, map_id='bloodrun')
        p.end(600, 'human_win', summary=self.result())
        p.tick(600, 600)
        p.forget_opponent('123')
        self.assertIsNone(p.difficulty.pending)


if __name__ == '__main__':
    unittest.main()
