import importlib.util
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('prealpha_log', Path(__file__).parents[1] / 'tools/audit_prealpha_log.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class LogEvidenceTests(unittest.TestCase):
    def test_intentions_and_failed_jumps_are_not_successes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'console.log'
            path.write_text('PSYZ_TARGET t=100 entity=20\n'
                            'PSYZ_DEMO_ROUTE t=150 target=20 route=3\n'
                            'PSYZ_RJ_END t=200 higher=0 pickup=0\n'
                            'PSYZ_RJ_END t=300 outcome=timeout\n'
                            'PSYZ_RJ_END t=400 higher=1 pickup=0\n'
                            'PSYZ_PICKUP t=500 entity=20 target=20 route=3 class=item_armor_combat\n')
            result = module.summarize(path)
            self.assertEqual(result['actual_pickup_count'], 1)
            self.assertEqual(result['rocketjump_successes'], 1)
            self.assertEqual(len(result['pickups_with_matching_target_and_active_demo_route']), 1)


if __name__ == '__main__':
    unittest.main()
