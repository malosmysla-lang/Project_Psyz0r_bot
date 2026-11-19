from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from run_jump_probe_sweep_remote import probe_result


class JumpSweepResultsTests(unittest.TestCase):
    def test_target_only_and_sample_boundary(self):
        text=('PSYZ_RJ_BEGIN t=1 sample=2 target=200\n'
              'PSYZ_RJ_END t=2 sample=2 target=200 actor=0 higher=1 pickup=0 outcome=target_not_picked\n'
              'PSYZ_RJ_END t=3 sample=2 target=200 actor=0 higher=0 pickup=1 outcome=target_pickup\n'
              'PSYZ_RJ_END t=4 sample=12 target=200 actor=0 pickup=1 outcome=target_pickup\n')
        self.assertEqual(probe_result(text,3),dict(probe=3,sample=2,begins=1,successes=1,endings=2))

    def test_legacy_height_or_incomplete_proof_cannot_pass_v2_sweep(self):
        text=('PSYZ_RJ_END sample=2 higher=1 pickup=0\n'
              'PSYZ_RJ_END sample=2 pickup=1 outcome=target_pickup\n'
              'PSYZ_RJ_END sample=2 target=200 actor=invalid pickup=1 outcome=target_pickup\n')
        self.assertEqual(probe_result(text,3)['successes'],0)


if __name__=='__main__':unittest.main()
