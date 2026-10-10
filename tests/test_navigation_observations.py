import unittest
from tools.navigation_observations import build_graph, shortest_candidate
class NavTests(unittest.TestCase):
 def r(self,t,p):return dict(time_ms=t,position=p,health=100)
 def test_only_observed_direction(self):
  g=build_graph([self.r(0,[0,0,0]),self.r(200,[80,0,0])]);self.assertIsNotNone(shortest_candidate(g,'0,0,0','1,0,0'));self.assertIsNone(shortest_candidate(g,'1,0,0','0,0,0'))
 def test_floor_separation(self):
  g=build_graph([self.r(0,[0,0,0]),self.r(200,[0,0,64])]);self.assertEqual(len(g['nodes']),2)
 def test_teleport_not_edge(self):
  g=build_graph([self.r(0,[0,0,0]),self.r(200,[800,0,0])]);self.assertEqual(g['edges'],[])
 def test_gap_not_edge(self):
  g=build_graph([self.r(0,[0,0,0]),self.r(1000,[80,0,0])]);self.assertEqual(g['edges'],[])
 def test_candidate_never_executable(self):
  g=build_graph([self.r(0,[0,0,0]),self.r(200,[80,0,0])]);self.assertFalse(g['ready_for_execution']);self.assertFalse(shortest_candidate(g,'0,0,0','1,0,0')['validated'])
if __name__=='__main__':unittest.main()
