from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from audit_movement_v2 import speed_since_ground_start


class MovementV2AuditTests(unittest.TestCase):
    def test_time_is_relative_to_ground_start_not_air_takeoff(self):
        sample={'ground_prestrafe_ms':375,'view_trace':[{'elapsed_ms':1625,'speed':500},{'elapsed_ms':2000,'speed':550}]}
        self.assertEqual(speed_since_ground_start(sample,2000),500)

    def test_missing_four_second_coverage_is_unknown(self):
        sample={'ground_prestrafe_ms':375,'view_trace':[{'elapsed_ms':1625,'speed':500}]}
        self.assertIsNone(speed_since_ground_start(sample,4000))


if __name__=='__main__':unittest.main()
