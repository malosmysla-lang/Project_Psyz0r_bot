from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from build_red_candidates_v2 import takeoff_window


class RedCandidateTests(unittest.TestCase):
    def point(self,time,z,ground):
        return dict(time_ms=time,position=[-200,-300,z],velocity=[300,0,0],
                    viewangles=[0,90,0],health=120,armor=100,ground_entity=ground)

    def sequence(self):
        return dict(first_shot_ms=1150,last_shot_ms=1250,shot_count=2,
                    start_position=[-200,-280,430],shot_viewangles=[70,85,0])

    def test_launch_is_last_ground_contact_not_airborne_shot(self):
        window=dict(points=[self.point(1000,408,1022),self.point(1100,420,1023)],
                    pickup_ms=1900,pickup_position=[-170,0,537])
        candidate=takeoff_window(window,self.sequence())
        self.assertEqual(candidate['takeoff_position'],[-200,-300,408])
        self.assertEqual(candidate['shot_position'],[-200,-280,430])
        self.assertEqual(candidate['shot_delay_ms'],150)
        self.assertEqual(candidate['height_to_pickup'],129)

    def test_missing_or_old_ground_state_is_not_invented(self):
        window=dict(points=[self.point(100,408,1022),self.point(1100,420,1023)],
                    pickup_ms=1900,pickup_position=[-170,0,537])
        self.assertIsNone(takeoff_window(window,self.sequence()))

    def test_unknown_resources_prevent_a_launch_cost_claim(self):
        point=self.point(1000,408,1022);point['health']=None
        window=dict(points=[point],pickup_ms=1900,pickup_position=[-170,0,537])
        self.assertIsNone(takeoff_window(window,self.sequence()))


if __name__=='__main__':unittest.main()
