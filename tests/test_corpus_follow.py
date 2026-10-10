import unittest
from tools.analyze_bloodrun_corpus import active_pov
class FollowTests(unittest.TestCase):
 def test_playing(self):self.assertTrue(active_pov(dict(pm_type=0)))
 def test_follow(self):self.assertTrue(active_pov(dict(pm_type=2,pm_flags=4096)))
 def test_free_camera(self):self.assertFalse(active_pov(dict(pm_type=2,pm_flags=0)))
 def test_intermission(self):self.assertFalse(active_pov(dict(pm_type=5,pm_flags=4096)))
if __name__=='__main__':unittest.main()
