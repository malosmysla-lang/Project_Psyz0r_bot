import importlib.util,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('tactical',Path(__file__).parents[1]/'tools/analyze_tactical_patterns.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def row(t,yaw=0,x=0):
    return dict(client=0,segment=1,game_state_number=1,time_ms=t,health=100,pm_type=0,position=[x,0,0],velocity=[100,0,0],viewangles=[0,yaw,0],speed_xy=100)
class TacticalTests(unittest.TestCase):
    def test_wraparound_is_small_aim_change(self):
        rows=[row(t,179 if t<125 else -179) for t in range(0,250,25)]
        p=m.preaim_window(rows,row(250,-179))
        self.assertTrue(p['held']);self.assertEqual(p['yaw_span'],2)
    def test_prefire_cannot_cross_teleport_or_death(self):
        rs=[row(t) for t in range(0,250,25)];rs[5]['position'][0]=500
        self.assertIsNone(m.preaim_window(rs,row(250)))
        rs=[row(t) for t in range(0,250,25)];rs[5]['health']=0
        self.assertIsNone(m.preaim_window(rs,row(250)))
    def test_relative_foot_velocity(self):
        self.assertEqual(m.foot_pattern(row(0,0))[0],'forward')
        self.assertEqual(m.foot_pattern(row(0,90))[0],'lateral')
        self.assertEqual(m.foot_pattern(row(0,180))[0],'backward')
    def test_kill_candidate_never_uses_other_pov_or_future_shot(self):
        shots=[dict(state=1,client=0,segment=1,t=t,weapon=w) for t,w in [(100,'rocket'),(500,'lightning'),(1500,'railgun')]]
        kill=dict(gameStateNumber=1,attackerClientNumber=0,serverTime=1000)
        self.assertEqual(m.kill_sequence(shots,kill,1,0,1),['rocket','lightning'])
        self.assertIsNone(m.kill_sequence(shots,kill,1,2,1))
        self.assertEqual(m.kill_sequence(shots,kill,1,0,2),[])
    def test_resource_chain_is_split_by_life_and_duplicates(self):
        rs=[dict(client=0,segment=1,pickup_ms=t,kind=k,points=[]) for t,k in [(100,'rocket'),(200,'red'),(300,'mega')]]
        lives={(0,1,100):1,(0,1,200):1,(0,1,300):2}
        transitions,chains,_=m.resource_sequences(rs+[rs[0]],lives)
        self.assertEqual(transitions,[('rocket','red',100)]);self.assertEqual(chains,[])
    def test_dwell_is_not_claimed_as_timer(self):
        r=dict(client=0,segment=1,pickup_ms=1000,kind='red',points=[dict(t=t,p=[0,0,0],v=[0,0,0]) for t in [0,500,1000]])
        _,_,d=m.resource_sequences([r],{(0,1,1000):1})
        self.assertEqual(d[0]['stationary_ms'],1000);self.assertFalse(d[0]['timer_verified'])
    def test_macro_chain_does_not_reduce_to_shard_cluster(self):
        rs=[dict(client=0,segment=1,pickup_ms=t,kind=k,points=[]) for t,k in [(100,'rocket'),(200,'shard'),(300,'shard'),(400,'red'),(500,'mega')]]
        lives={(0,1,r['pickup_ms']):1 for r in rs}
        _,chains,_=m.resource_sequences(rs,lives,True)
        self.assertEqual(chains,[(('rocket','red','mega'),400)])
if __name__=='__main__':unittest.main()
