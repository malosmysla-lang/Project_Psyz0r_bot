import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from build_marked_demo_dataset import window

def row(t,x=0,client=1):
 return dict(game_state_number=1,time_ms=t,client=client,segment=1,pm_type=0,position=[x,0,0],speed_xy=320)

class MarkedDatasetTests(unittest.TestCase):
 def test_bot_note_cannot_label_human_pov_positive(self):
  result=window([row(975),row(1000,8),row(1025,16)],dict(state=1,time=1000,text='Good move Psyz0r'))
  self.assertTrue(result['aligned']);self.assertEqual(result['annotation_subject'],'bot')
  self.assertFalse(result['eligible_for_automatic_positive_imitation'])
 def test_teleport_is_not_learned_turn(self):
  result=window([row(975),row(1000,800),row(1025,810)],dict(state=1,time=1000,text='Good move'))
  self.assertFalse(result['continuous'])
 def test_wrong_clock_or_game_state_rejected(self):
  self.assertFalse(window([row(1000)],dict(state=2,time=1000,text='Good move'))['aligned'])
  self.assertFalse(window([row(900)],dict(state=1,time=1000,text='Good move'))['aligned'])

if __name__=='__main__':unittest.main()
