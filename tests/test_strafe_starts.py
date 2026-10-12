import importlib.util
import unittest
from pathlib import Path


spec = importlib.util.spec_from_file_location(
    "analyse_strafe", Path(__file__).parents[1] / "tools" / "analyze_strafe_starts.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def row(t, ground, speed, yaw, vz=0, fired=False):
    return dict(segment=1, client=0, time_ms=t, pm_type=module.ACTIVE_PM_TYPE, health=100,
                ground_entity=ground, speed_xy=speed, velocity=[speed, 0, vz],
                viewangles=[0, yaw, 0],
                events=[dict(kind="weapon_fired")] if fired else [])


class StrafeStartTests(unittest.TestCase):
    def sequence(self, fired=False):
        rows = [row(t, 1, min(300, t * .8), t * .04, fired=fired and t == 250)
                for t in range(0, 400, 25)]
        rows += [row(t, module.AIR, 320 + (t - 400) * .2, 16 + (t - 400) * .02,
                     270 if t == 400 else 50) for t in range(400, 850, 25)]
        rows += [row(850, 1, 410, 25), row(875, module.AIR, 420, 26, 270)]
        rows += [row(t, module.AIR, 420 + (t - 875) * .1, 26 + (t - 875) * .01, 40)
                 for t in range(900, 1200, 25)]
        return rows

    def test_two_jump_noncombat_start_is_measured(self):
        samples = module.analyse_rows(self.sequence(), "synthetic")
        self.assertEqual(len(samples), 1)
        self.assertEqual(samples[0]["landing_to_second_takeoff_ms"], 25)
        self.assertGreater(samples[0]["second_air_max_speed"], samples[0]["first_air_max_speed"])
        self.assertFalse(samples[0]["raw_mouse_or_keys_verified"])

    def test_combat_window_is_excluded(self):
        self.assertEqual(module.analyse_rows(self.sequence(True), "combat"), [])
