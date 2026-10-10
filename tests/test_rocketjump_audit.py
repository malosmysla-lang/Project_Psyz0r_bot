import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from audit_rocketjumps import classify, marker_label, analyze
class RocketAuditTests(unittest.TestCase):
 def test_apex_alone_not_success(self): self.assertEqual(classify(-64,[],True),'unsuccessful')
 def test_height(self): self.assertEqual(classify(128,[],True),'success')
 def test_pickup_independent_of_height(self): self.assertEqual(classify(-64,[{'kind':'health'}],True),'success')
 def test_ammo_not_requested_reward(self): self.assertEqual(classify(0,[{'kind':'ammo'}],True),'unsuccessful')
 def test_missing_landing_unknown(self): self.assertEqual(classify(None,[{'kind':'mega'}],False),'unknown')
 def test_tolerance(self): self.assertEqual(classify(0.125,[],True),'unsuccessful')
 def test_marker_typo(self): self.assertTrue(marker_label('#bot rocketjump\\'));self.assertFalse(marker_label('#bot rocketjump later'))
class SegmentationTests(unittest.TestCase):
 def row(self,t,z,vz,ground,events=None):
  return dict(time_ms=t,position=[0,0,z],velocity=[0,0,vz],ground_entity=ground,events=events or [],segment=1,client=0,game_state_number=1,pm_type=0,weapon_id=5,viewangles=[90,0,0],health=100,armor=0)
 def test_actual_landing_beats_apex(self):
  rows=[self.row(1000,100,0,1022),self.row(1025,110,600,1023,[{'kind':'weapon_fired','udt_event_id':1}]),self.row(1050,200,0,1023),self.row(1075,50,0,1022)]
  result=analyze(rows,[dict(serverTime=1000,clientNumber=0,gameStateNumber=1,cleanMessage='#bot rocketjump')],lambda _:None)
  self.assertEqual(result[0]['status'],'unsuccessful')
  self.assertEqual(result[0]['height_gain'],-50)
 def test_other_pov_not_matched(self):
  rows=[self.row(1000,100,0,1022)]
  result=analyze(rows,[dict(serverTime=1000,clientNumber=1,gameStateNumber=1,cleanMessage='#bot rocketjump')],lambda _:None)
  self.assertEqual(result[0]['status'],'unknown')
if __name__=='__main__': unittest.main()
