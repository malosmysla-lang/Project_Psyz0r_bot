import unittest
from tools.analyze_red_approaches import classify


class RedApproachTests(unittest.TestCase):
    def test_rocket_in_hand_does_not_claim_confirmed_rj(self):
        points=[dict(ground=1023,weapon=5,p=[x,0,100]) for x in (0,200)]
        self.assertEqual(classify(points),'rocket_equipped_airborne_candidate')

    def test_grounded_route_and_airborne_distance_are_separate(self):
        points=[dict(ground=1022,weapon=7,p=[x,0,100]) for x in (0,200)]
        self.assertEqual(classify(points),'grounded')
        for p in points:p['ground']=1023
        self.assertEqual(classify(points),'longjump_candidate')
