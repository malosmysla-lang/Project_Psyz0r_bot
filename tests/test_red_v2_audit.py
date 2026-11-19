import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from audit_red_v2 import inspect_snapshots, observed_actor


class RedV2AuditTests(unittest.TestCase):
    def setUp(self):
        self.metadata={'gameStates':[{'configStringValues':{'mapname':'bloodrun'},
                                     'players':[{'clientNumber':2,'cleanName':'^1nekitz0r','startTime':100,'endTime':1000}]}]}
        self.row={'game_state_number':1,'client':2,'time_ms':200}

    def test_one_based_snapshot_state_matches_zero_based_metadata(self):
        self.assertEqual(observed_actor(self.metadata,self.row),'nekitz0r')

    def test_unknown_state_or_changed_actor_is_not_assigned(self):
        self.assertIsNone(observed_actor(self.metadata,dict(self.row,game_state_number=0)))
        self.assertIsNone(observed_actor(self.metadata,dict(self.row,client=3)))
        self.assertIsNone(observed_actor(self.metadata,dict(self.row,time_ms=1001)))
        self.metadata['gameStates'][0]['players'].append(dict(clientNumber=2,cleanName='other',startTime=100,endTime=1000))
        self.assertIsNone(observed_actor(self.metadata,self.row))

    def test_other_map_never_produces_bloodrun_training_example(self):
        self.metadata['gameStates'][0]['configStringValues']['mapname']='bloodrunintel'
        self.assertIsNone(observed_actor(self.metadata,self.row))

    def test_pickup_is_attributed_to_observed_client_not_demo_taker(self):
        row=dict(self.row,segment=1,pm_type=0,pm_flags=0,position=[0,0,0],
                 velocity=[0,0,0],ground_entity=1022,weapon_id=5,health=100,armor=100,
                 viewangles=[0,0,0],events=[],observed_pov_pickups=[{'kind':'red'}])
        self.metadata['gameStates'][0]['demoTakerCleanName']='spectator'
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'snapshots.jsonl'
            path.write_text(json.dumps(row)+'\n',encoding='utf-8')
            windows,counts=inspect_snapshots(path,self.metadata,{'nekitz0r'})
        self.assertEqual(counts['nekitz0r'],1)
        self.assertEqual(len(windows),1)
        self.assertEqual(windows[0]['actor'],'nekitz0r')
        self.assertFalse(windows[0]['raw_controls_verified'])


if __name__=='__main__':
    unittest.main()
