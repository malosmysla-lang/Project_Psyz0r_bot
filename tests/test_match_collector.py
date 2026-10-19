import importlib.util,json,tempfile,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('collector',Path(__file__).parents[1]/'server/telemetry/psyz_match_collector.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def event(kind,**data):return dict(TYPE=kind,DATA=dict(MATCH_GUID='match-test-guid',**data))
def player(name='Psyz0r_bot',sid='0',shots=10,hits=3,warmup=False):
    return event('PLAYER_STATS',NAME=name,STEAM_ID=sid,WARMUP=warmup,SCORE=3,KILLS=3,DEATHS=4,PLAY_TIME=600,DAMAGE=dict(DEALT=100,TAKEN=200),PICKUPS=dict(RED_ARMOR=2),WEAPONS=dict(MACHINEGUN=dict(S=shots,H=hits,DG=25,K=0)))
class CollectorTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.now=100
        self.c=m.Collector(Path(self.tmp.name),lambda:'0.7.9',lambda:self.now)
    def finish(self):
        self.c.handle(player());self.c.handle(player('Xaero',sid='0'));self.c.handle(event('MATCH_REPORT',GAME_TYPE='DUEL',MAP='bloodrun',ABORTED=False));self.now+=5;self.c.flush()
    def test_zero_id_bots_do_not_overwrite_each_other(self):
        self.finish();r=next(iter(self.c.matches.values()));self.assertEqual(r['opponent']['name'],'Xaero');self.assertEqual(r['bot']['weapons']['machinegun']['accuracy_pct'],30)
    def test_no_shots_is_unknown(self):
        p=m.sanitize_player(player(shots=0,hits=0)['DATA']);self.assertIsNone(p['weapons']['machinegun']['accuracy_pct'])
    def test_warmup_is_not_a_match(self):
        self.c.handle(player(warmup=True));self.assertFalse(self.c.pending)
    def test_late_stats_after_match_report_are_kept(self):
        self.c.handle(event('MATCH_REPORT',GAME_TYPE='DUEL',MAP='bloodrun'));self.c.flush(force=True);self.assertFalse(self.c.matches)
        self.c.handle(player());self.c.handle(player('human',sid='76561198000000001'));self.c.flush(force=True);self.assertEqual(len(self.c.matches),1)
    def test_repeat_flush_does_not_change_match_end(self):
        self.finish();before=next(iter(self.c.matches.values()))['ended_at'];self.now+=60;self.c.flush();self.assertEqual(next(iter(self.c.matches.values()))['ended_at'],before)
    def test_public_json_has_no_steam_ids(self):
        self.finish();text=(Path(self.tmp.name)/'public_matches.json').read_text();self.assertNotIn('STEAM_ID',text);self.assertNotIn('steam_id',text)
    def test_restarts_preserve_completed_matches(self):
        self.finish();restored=m.Collector(Path(self.tmp.name),lambda:'new');self.assertEqual(len(restored.matches),1)
    def test_impossible_hit_ratio_is_not_clamped_into_accuracy(self):
        self.assertIsNone(m.sanitize_player(player(shots=1,hits=4)['DATA'])['weapons']['machinegun']['accuracy_pct'])
if __name__=='__main__':unittest.main()
