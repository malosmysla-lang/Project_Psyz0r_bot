import unittest
from tools.export_resource_routes import export_routes
class ResourceRouteTests(unittest.TestCase):
 def fixture(self):
  rows=[dict(time_ms=t,position=[t,0,100],viewangles=[0,0,0],velocity=[0,0,0],weapon_id=5,ground_entity=1023,segment=1,client=0,game_state_number=1,pm_type=0,events=[]) for t in [0,50,100]]
  rows[-1]['events']=[dict(udt_event_id=2,parameter=3)]
  audit=dict(demo_sha256='test',results=[dict(status='success',shot_ms=50,start_ms=0,pickups=[dict(kind='red',time_ms=100)])])
  return rows,audit
 def test_preserves_unreviewed_observation(self):
  rows,audit=self.fixture();r=export_routes(rows,audit)[0]
  self.assertFalse(r['ready_for_execution']);self.assertFalse(r['position_reviewed']);self.assertEqual(r['physics'],'unknown');self.assertEqual(r['approach_position'],[100,0,100])
 def test_discontinuity_rejected(self):
  rows,audit=self.fixture();rows[1]['segment']=2;self.assertEqual(export_routes(rows,audit),[])
 def test_gap_rejected(self):
  rows,audit=self.fixture();rows[1]['time_ms']=200;self.assertEqual(export_routes(rows,audit),[])
 def test_failure_not_training_success(self):
  rows,audit=self.fixture();audit['results'][0]['status']='unsuccessful';self.assertEqual(export_routes(rows,audit),[])
if __name__=='__main__': unittest.main()
