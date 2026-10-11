import copy
import unittest
from tools.build_opening_bank import select


class OpeningBankTests(unittest.TestCase):
    def setUp(self):
        self.record = dict(status='observed', start_delay_ms=700, observed_ms=10000,
                           observed_health_loss=15, start_position=[0, 0, 0],
                           demo_id='test', source_sha256='test', first_three=[
                               dict(kind='rocket', position=[100, 0, 0]),
                               dict(kind='mega', position=[200, 0, 0])])
        self.items = [dict(classname='weapon_rocketlauncher', position=[100, 0, 0]),
                      dict(classname='item_health_mega', position=[200, 0, 0])]

    def test_reject_high_loss_and_missing_start(self):
        for field, value in [('observed_health_loss', 41), ('start_delay_ms', 1501),
                             ('observed_ms', 4999)]:
            r = copy.deepcopy(self.record)
            r[field] = value
            self.assertEqual(select([r], self.items), [])

    def test_wrong_item_geometry_is_not_relabelled(self):
        self.items[0]['position'] = [1000, 0, 0]
        self.assertEqual(select([self.record], self.items), [])

    def test_provenance_retained_without_success_claim(self):
        r = select([self.record], self.items)[0]
        self.assertFalse(r['live_verified'])
        self.assertEqual(r['source_sha256'], 'test')
        self.assertEqual(r['steps'][0]['classname'], 'weapon_rocketlauncher')
