import unittest
from tools.audit_red_boosts import analyze_window


class RedBoostTests(unittest.TestCase):
    def rows(self, weapon=5, delay=5000):
        rows=[]
        for t in range(0, delay+101, 100):
            rows.append(dict(segment=1, game_state_number=0, client=0, pm_type=0,
                time_ms=t, position=[0, 0, min(t/10, 100)],
                velocity=[0, 0, 350 if t==100 else 0], ground_entity=1023,
                health=100 if t==0 else 90, armor=0, weapon_id=weapon,
                events=[dict(kind='weapon_fired')] if t==0 else [],
                viewangles=[80, 0, 0], observed_pov_pickups=[]))
        rows[-1]['observed_pov_pickups']=[dict(kind='red')]
        return rows

    def test_five_second_boundary_and_weapon(self):
        for weapon, kind in [(5,'rocketjump_candidate'),(8,'plasmajump_candidate')]:
            result=analyze_window(self.rows(weapon))
            self.assertEqual(result['boosts'][0]['pickup_delay_ms'],5000)
            self.assertEqual(result['boosts'][0]['kind'],kind)
            self.assertFalse(result['boosts'][0]['self_damage_verified'])
        self.assertFalse(analyze_window(self.rows(delay=5100))['boosts'])

    def test_held_weapon_and_decay_are_not_boosts(self):
        rows=self.rows()
        rows[0]['events']=[]
        self.assertFalse(analyze_window(rows)['boosts'])

    def test_followed_player_is_valid_but_free_spectator_is_not(self):
        rows=self.rows()
        for r in rows:r.update(pm_type=2,pm_flags=4096)
        self.assertTrue(analyze_window(rows)['boosts'])
        for r in rows:r['pm_flags']=0
        self.assertFalse(analyze_window(rows)['boosts'])
        rows=self.rows()
        for r in rows[1:]:r['health']=99
        self.assertFalse(analyze_window(rows)['boosts'])

    def test_teleport_and_missing_snapshots_reject(self):
        rows=self.rows()
        for r in rows[20:]:r['position'][0]=1000
        self.assertFalse(analyze_window(rows)['boosts'])
        rows=self.rows();del rows[2]
        self.assertFalse(analyze_window(rows)['boosts'])
