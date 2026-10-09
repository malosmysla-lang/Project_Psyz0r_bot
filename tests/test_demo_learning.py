import copy
import unittest
from tools.demo_learning import build_episodes, chat_markers, label_text, metrics, audit_chat_alignment


class DemoLearningTests(unittest.TestCase):
    def rows(self, count=141):
        return [dict(time_ms=i*50, segment=1, game_state_number=1, client=1, pm_type=0,
                     position=[0, 0, 0], velocity=[0, 0, 0], speed_xy=0,
                     viewangles=[0, 0, 0], weapon_id=5, health=100, armor=50,
                     events=[], raw_mouse_or_keys_verified=False) for i in range(count)]

    def build(self, rows, markers):
        return build_episodes(rows, markers, map_name='bloodrun', physics='classic',
                              source_kind='solo', owner_client=1)

    def marker(self, **changes):
        return dict(dict(label='rocketjump', time_ms=3000, segment=1, client=1,
                         clock='demo_server_time', before_ms=2000, after_ms=3000), **changes)

    def test_window_alignment_and_metrics_preserve_unknowns(self):
        rows=self.rows()
        rows[100]['health']=None
        before=copy.deepcopy(rows)
        result=self.build(rows,[self.marker()])
        e=result['episodes'][0]
        self.assertEqual(e['samples'][0]['time_ms'],1000)
        self.assertEqual(e['samples'][-1]['time_ms'],6000)
        self.assertEqual(e['alignment_error_ms'],0)
        self.assertFalse(e['control_sequence_reconstructed'])
        self.assertFalse(e['metrics']['self_damage_attribution_verified'])
        self.assertEqual(rows,before)
        self.assertIsNone(metrics([rows[0], rows[100]])['net_health_delta_loss'])

    def test_actual_udt_chat_schema_pov_and_time_domain(self):
        data={'chat':[{'clean message':'#bot punish mega','server time':3000,
                       'client number':1,'game state number':1}]}
        markers=chat_markers(data)
        result=self.build(self.rows(),markers)
        self.assertEqual(result['episodes'][0]['label'],'punish mega')
        self.assertEqual(result['episodes'][0]['marker_source'],'udt_chat')
        data['chat'][0]['client number']=2
        self.assertFalse(self.build(self.rows(),chat_markers(data))['episodes'])
        self.assertIsNone(label_text('say #bot hide'))

    def test_installed_udt_camel_case_chat_schema(self):
        data={'chat':[{'cleanMessage':'#bot hide','serverTime':3000,'clientNumber':1,'gameStateNumber':1}]}
        self.assertEqual(self.build(self.rows(),chat_markers(data))['episodes'][0]['label'],'hide')
        audit=audit_chat_alignment(data,self.rows(),1)
        self.assertTrue(audit[0]['aligned'])
        self.assertEqual(audit[0]['alignment_error_ms'],0)

    def test_bad_clocks_missing_sender_and_ambiguous_segments_rejected(self):
        for change in [dict(clock='duel_clock'),dict(client=None),dict(time_ms=30000),dict(label='unknown')]:
            result=self.build(self.rows(),[self.marker(**change)])
            self.assertEqual(len(result['rejected_markers']),1)
        rows=self.rows()+[dict(r,segment=2) for r in self.rows()]
        marker=self.marker();marker.pop('segment');marker['game_state_number']=1
        self.assertFalse(self.build(rows,[marker])['episodes'])

    def test_no_crossing_gap_teleport_death_or_pov(self):
        for mutation in ('gap','teleport','death','pov'):
            rows=self.rows()
            if mutation=='gap':
                rows=[r for r in rows if not 3500<=r['time_ms']<=4000]
            elif mutation=='teleport':
                for r in rows[70:]:r['position']=[1000,0,0]
            elif mutation=='death':rows[70]['pm_type']=3
            else:rows[70]['client']=2
            e=self.build(rows,[self.marker()])['episodes'][0]
            self.assertLess(e['samples'][-1]['time_ms'],3500)
            self.assertTrue(e['window_clipped'])

    def test_stationary_position_needs_role_confirmation(self):
        result=self.build(self.rows(),[])
        self.assertEqual(len(result['stationary_positions']),1)
        self.assertIsNone(result['stationary_positions'][0]['role'])
        rows=self.rows()
        for i,r in enumerate(rows):r['position']=[i,0,0]
        self.assertFalse(self.build(rows,[])['stationary_positions'])
        self.assertFalse(self.build(self.rows(90),[])['stationary_positions'])

    def test_health_delta_is_not_rocket_selfdamage(self):
        rows=self.rows()
        rows[120]['health']=70;rows[120]['armor']=40
        m=self.build(rows,[self.marker()])['episodes'][0]['metrics']
        self.assertEqual(m['net_health_delta_loss'],30)
        self.assertFalse(m['self_damage_attribution_verified'])
        self.assertIsNone(m['measured_attempt_success'])


if __name__=='__main__':
    unittest.main()
