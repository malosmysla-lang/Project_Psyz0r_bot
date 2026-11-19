from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from summarize_xaero_v2 import summarize


class XaeroV2Tests(unittest.TestCase):
    def demo(self):
        return {'sha256':'a','originals':[], 'matches':[dict(map='bloodrun',startTime=100,endTime=200,
                intermissionEndTime=250,forfeited=False,startDate=None,playerStats=[
                {'name':'nekitz0r','team':'free','score':1,'machinegunShots':10,'machinegunHits':5},
                {'name':'Xaero','team':'free','score':0}])]}

    def test_missing_pickups_are_unknown_and_duplicate_source_is_counted_once(self):
        result=summarize([self.demo(),self.demo()])
        self.assertEqual(result['summary']['completed'],1)
        self.assertIsNone(result['maps']['bloodrun']['owner']['pickups']['red']['total'])
        self.assertEqual(result['maps']['bloodrun']['owner']['weapons']['machinegun']['weighted_accuracy_pct'],50)

    def test_unfinished_scoreboard_is_retained_outside_completed_aggregate(self):
        d=self.demo();d['matches'][0]['intermissionEndTime']=None
        result=summarize([d])
        self.assertEqual(result['summary']['incomplete_or_forfeit'],1)
        self.assertEqual(result['maps'],{})


if __name__=='__main__':unittest.main()
