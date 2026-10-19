import importlib.util,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('sync',Path(__file__).parents[1]/'tools/sync_match_ledger.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class MatchSyncTests(unittest.TestCase):
    def test_merge_updates_one_guid_without_duplicates(self):
        seed=dict(matches=[dict(id='demo:x'),dict(id='live:abc',bot=dict(is_psyz=True),score=1)])
        live=dict(matches=[dict(id='live:abc',bot=dict(is_psyz=True),score=2)])
        merged=m.merge(seed,live);self.assertEqual(len(merged['matches']),2);self.assertEqual(merged['matches'][1]['score'],2)
    def test_foreign_records_are_not_published_as_our_bot(self):
        result=m.merge(dict(matches=[]),dict(matches=[dict(id='live:abc',bot=dict(is_psyz=False)),dict(id='other:fake',bot=dict(is_psyz=True))]))
        self.assertEqual(result['matches'],[])
    def test_automatic_training_cannot_be_claimed_by_incoming_data(self):
        self.assertFalse(m.merge(dict(matches=[],automatic_learning=True),dict(matches=[]))['automatic_learning'])
if __name__=='__main__':unittest.main()
