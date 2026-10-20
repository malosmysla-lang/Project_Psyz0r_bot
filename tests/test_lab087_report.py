import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

path = Path(__file__).resolve().parents[1] / 'tools/summarize_lab087.py'
spec = importlib.util.spec_from_file_location('lab087_report', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ReportTests(unittest.TestCase):
    def test_warmup_quit_and_short_setup_are_excluded_and_guid_deduplicates(self):
        rows = [dict(event='game_end', time=100, data=dict(result=dict(MATCH_GUID='short', GAME_LENGTH=5))),
                dict(event='game_start', version='0.8.7', block='stock_control', data=dict(detail=dict(MATCH_GUID='real'))),
                dict(event='game_end', data=dict(result=dict(MATCH_GUID='real', GAME_LENGTH=300)))]
        for name, shots, hits in [('Psyz0r_bot', 10, 6), ('Psyz0r', 20, 8)]:
            p = dict(MATCH_GUID='real', NAME=name, PLAY_TIME=300, SCORE=3, KILLS=3, DEATHS=2,
                     DAMAGE=dict(DEALT=500), WEAPONS=dict(RAILGUN=dict(S=shots, H=hits, DG=480, K=3)))
            rows += [dict(event='player_stats', data=dict(DATA=p))] * 2
            rows += [dict(event='player_stats', data=dict(DATA=dict(p, WARMUP=True, NAME='Warmup'))),
                     dict(event='player_stats', data=dict(DATA=dict(p, QUIT=1, NAME='Quitter')))]
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / 'lab-events.jsonl'
            target.write_text('\n'.join(json.dumps(row) for row in rows), encoding='utf-8')
            report = module.summarize([target])
        self.assertEqual(report['completed_matches'], 1)
        self.assertEqual(report['setup_ends_excluded'], 1)
        self.assertEqual(report['matches_with_two_final_stats'], 1)
        players = report['cohorts']['0.8.7:stock_control']['players']
        self.assertEqual(set(players), {'Psyz0r_bot', 'Psyz0r'})
        self.assertEqual(players['Psyz0r_bot']['games'], 1)
        self.assertEqual(players['Psyz0r_bot']['weapons']['RAILGUN']['accuracy_pct'], 60)


if __name__ == '__main__':
    unittest.main()
