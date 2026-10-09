import unittest
from tools.review_movement import review

class MovementTests(unittest.TestCase):
    def row(self, time, speed=0, yaw=179, pm_type=0, segment=1):
        return dict(time_ms=time, speed_xy=speed, viewangles=[0, yaw, 0], pm_type=pm_type,
                    segment=segment, client=0, position=[0, 0, 0], velocity=[speed, 0, 0], weapon_id=1)

    def test_waiting_not_fault_and_yaw_wrap(self):
        rows = [self.row(t) for t in range(0, 1101, 50)]
        rows[1]['viewangles'][1] = -179
        result = review(rows)
        self.assertEqual(result['candidates'][0]['kind'], 'stationary_review')
        self.assertLessEqual(result['observed_yaw_degrees_per_second_p95'], 40)

    def test_gaps_deaths_and_pov_changes_split_intervals(self):
        rows = [self.row(0), self.row(500), self.row(550, pm_type=3), self.row(600, segment=2), self.row(1200, segment=2)]
        self.assertFalse(review(rows)['candidates'])

    def test_item_approach_never_crosses_teleport_or_death(self):
        rows = [self.row(0, 320), self.row(50, 320), self.row(100, 320)]
        rows[-1]['position'] = [1000, 0, 0]
        rows[-1]['observed_pov_pickups'] = [dict(kind='mega')]
        route = review(rows)['item_approaches'][0]
        self.assertEqual(route['duration_seconds'], 0)
        self.assertEqual(len(route['samples']), 1)
