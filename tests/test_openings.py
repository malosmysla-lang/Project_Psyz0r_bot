import unittest
from tools.analyze_openings import opening


class OpeningTests(unittest.TestCase):
    def row(self, t, **kw):
        return dict(time_ms=t, game_state_number=1, client=0, segment=0,
                    pm_type=0, health=100, position=[0, 0, 0], **kw)

    def test_late_recording_is_not_opening(self):
        self.assertEqual(opening([self.row(1000)], [], 0, 1)['reason'], 'start_not_observed')

    def test_warmup_and_wrong_state_excluded(self):
        self.assertEqual(opening([self.row(0)], [], 0, 2)['status'], 'excluded')

    def test_pov_switch_does_not_mix_paths(self):
        second = self.row(50)
        second['client'] = 1
        result = opening([self.row(0), second], [], 0, 1)
        self.assertEqual(result['completion'], 'pov_discontinuity')
        self.assertEqual(result['observed_ms'], 0)

    def test_pickup_order_and_loss_are_observations(self):
        rows = [self.row(t) for t in range(0, 30001, 50)]
        rows[2]['health'] = 99
        routes = [dict(kind=k, pickup_ms=t, client=0, segment=0, points=[{'p':[1,2,3]}])
                  for k,t in [('mega', 200), ('rocket', 50), ('red', 300), ('shard', 100)]]
        result = opening(rows, routes, 0, 1)
        self.assertEqual([p['kind'] for p in result['first_three']], ['rocket', 'mega', 'red'])
        self.assertEqual(result['completion'], 'complete')
        self.assertEqual(result['observed_health_loss'], 1)
        self.assertEqual(result['early_frag'], 'not_exported')


if __name__ == '__main__':
    unittest.main()
