import importlib.util
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('prealpha_log', Path(__file__).parents[1] / 'tools/audit_prealpha_log.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class LogEvidenceTests(unittest.TestCase):
    def test_v2_missed_target_is_not_success_even_on_higher_ground(self):
        self.assertFalse(module.jump_success(dict(outcome='target_not_picked',higher='1',pickup='0',target='200',actor='0')))
        self.assertFalse(module.jump_success(dict(outcome='target_pickup',pickup='1')))
        self.assertTrue(module.jump_success(dict(outcome='target_pickup',pickup='1',target='200',actor='0')))

    def test_legacy_height_is_separate_from_verified_target_pickup(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'console.log'
            path.write_text('PSYZ_RJ_END t=1 higher=1 pickup=0\n'
                            'PSYZ_RJ_END t=2 target=200 actor=0 higher=1 pickup=0 outcome=target_not_picked\n'
                            'PSYZ_RJ_END t=3 target=200 actor=0 higher=0 pickup=1 outcome=target_pickup\n')
            result=module.summarize(path)
            self.assertEqual(result['rocketjump_successes'],2)
            self.assertEqual(result['verified_target_pickup_successes'],1)

    def test_hook_failure_is_exposed_even_without_gameplay_events(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'console.log'
            path.write_text('PSYZ_CONTROL install=-3\nPSYZ_STOCK_GOAL refused: hook error=-3\n')
            result = module.summarize(path)
            self.assertEqual(len(result['integration_errors']), 2)
            self.assertEqual(result['actual_pickup_count'], 0)

    def test_opening_plan_and_abort_are_not_completion(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'console.log'
            path.write_text('PSYZ_OPENING_BEGIN t=1\n'
                            'PSYZ_OPENING_PLAN t=2 plan=0\n'
                            'PSYZ_OPENING_PICKUP t=3 plan=0 step=0 entity=20\n'
                            'PSYZ_OPENING_END t=4 plan=0 step=1 reason=unavailable_or_distant\n')
            result = module.summarize(path)
            self.assertEqual(result['opening_actual_pickups'], 1)
            self.assertEqual(result['opening_completed_orders'], 0)

    def test_intentions_and_failed_jumps_are_not_successes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'console.log'
            path.write_text('PSYZ_PICKUP install=0\n'
                            'PSYZ_TARGET t=100 entity=20\n'
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
