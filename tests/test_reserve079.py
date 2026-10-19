import importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import analyze_reserve079 as research
import audit_motion079 as motion

def match(players,winner='one'):
    return dict(matchStats=[dict(gameTypeShort='1v1',gameStateIndex=0,startTime=0,endTime=10000,winner=winner,playerStats=players)])
def player(client,name,damage=None,shots=100,accuracy=30):
    p=dict(clientNumber=client,cleanName=name,team='free',machinegunShots=shots,machinegunAccuracy=accuracy)
    if damage is not None:p['damageGiven']=damage
    return p

class ReserveResearchTests(unittest.TestCase):
    def test_different_damage_leader_is_not_discarded(self):
        m=research.select_cohorts(match([player(0,'one',100),player(1,'two',200)]),'demo')[0]
        self.assertEqual(m['winner_clients'],[0]);self.assertEqual(m['damage_leader_clients'],[1])
    def test_partial_damage_table_cannot_establish_leader(self):
        m=research.select_cohorts(match([player(0,'one',100),player(1,'two')]),'demo')[0]
        self.assertEqual(m['damage_leader_clients'],[])
    def test_tied_damage_keeps_both_once(self):
        m=research.select_cohorts(match([player(0,'one',100),player(1,'two',100)]),'demo')[0]
        self.assertTrue(m['damage_tied']);self.assertEqual(m['damage_leader_clients'],[0,1])
    def test_no_shots_is_missing_but_fired_zero_percent_is_valid(self):
        m=research.select_cohorts(match([player(0,'one',100,shots=0),player(1,'two',200,accuracy=0)]),'demo')
        self.assertEqual(research.accuracy_table(m,'winner')['observations'],[])
        self.assertEqual(research.accuracy_table(m,'damage_leader')['observations'][0]['accuracy'],0)
    def test_ambiguous_winner_is_not_invented(self):
        m=research.select_cohorts(match([player(0,'one',100),player(1,'one',200)]),'demo')[0]
        self.assertEqual(m['winner_clients'],[])
    def test_old_log_intent_is_unknown(self):
        text='\n'.join(f'PSYZ_NAV t={t} pos=1,2,3 vel=0,0,0 health=100' for t in range(0,2200,200))
        r=motion.audit(text);self.assertEqual(r['stationary_candidates'],1)
        self.assertFalse(r['longest_candidates'][0]['commands_available'])
if __name__=='__main__':unittest.main()
