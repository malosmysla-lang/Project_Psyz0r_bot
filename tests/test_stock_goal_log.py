import struct
import unittest
from tools.read_stock_goal_log import parse_log
class GoalLogTests(unittest.TestCase):
    def line(self,origin=(1.,2.,3.)):
        raw=struct.pack('<3fi',*origin,123)+bytes(32)
        return 'PSYZ_STOCK_GOAL sequence=1 state=0x123 travel_flags=456 result=1 prefix48='+raw.hex()+' source=stock_ltg layout=unverified\n'
    def test_candidate_not_verified(self):
        r=parse_log(self.line())[0]
        self.assertEqual(r['candidate_origin'],[1,2,3])
        self.assertEqual(r['candidate_area'],123)
        self.assertFalse(r['layout_verified'])
        self.assertFalse(r['ready_for_execution'])
    def test_nonfinite_keeps_raw_diagnostic(self):
        r=parse_log(self.line((float('inf'),0.,0.)))[0]
        self.assertIsNone(r['candidate_origin'])
        self.assertEqual(len(r['raw_prefix_hex']),96)
    def test_truncated_rejected(self):
        self.assertEqual(parse_log(self.line().replace(' prefix48=',' prefix48=0')),[])
    def test_other_source_not_accepted(self):
        self.assertEqual(parse_log(self.line().replace('source=stock_ltg','source=unknown')),[])
    def test_unrelated_lines_ignored(self):
        self.assertEqual(parse_log('server running\n'),[])
if __name__=='__main__':unittest.main()
