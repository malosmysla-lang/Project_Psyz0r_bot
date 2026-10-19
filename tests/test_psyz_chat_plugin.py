import importlib.util
from pathlib import Path
import sys
import types
import unittest


class Plugin:
    def add_hook(self, *args, **kwargs): pass
    def add_command(self, *args, **kwargs): pass
    def players(self): return self._players
    def msg(self, text): self.sent.append(text)
    def get_cvar(self,name):return self._cvars.get(name)


fake = types.SimpleNamespace(Plugin=Plugin, RET_STOP_ALL=1,
                             delay=lambda seconds: (lambda fn: fn),
                             log_exception=lambda: None)
sys.modules["minqlx"] = fake
path = Path(__file__).parents[1] / "server" / "minqlx-plugins" / "psyz_chat.py"
spec = importlib.util.spec_from_file_location("psyz_chat", path)
chat = importlib.util.module_from_spec(spec); spec.loader.exec_module(chat)


class Player:
    def __init__(self, name, sid): self.name=self.clean_name=name;self.steam_id=sid
    def kick(self,reason):self.kicked=reason


class ChatTests(unittest.TestCase):
    def plugin(self):
        p=chat.psyz_chat();p.sent=[]
        p.human=Player("Human",7656119);p.bot=Player("Psyz0r",0x0140000100000000)
        p._players=[p.human,p.bot];p.game=types.SimpleNamespace(state="in_progress")
        p._cvars={'net_port':'27961','qlx_psyzForfeitEnabled':'1','bot_minplayers':'0'}
        p.human.score=20;p.bot.score=0
        return p

    def test_classification(self):
        self.assertEqual(chat.classify_chat("GL HF"),"sport")
        self.assertEqual(chat.classify_chat("gg wp"),"gg")
        self.assertEqual(chat.classify_chat("bot noob"),"retort")

    def test_sports_reply_once(self):
        p=self.plugin();p.handle_chat(p.human,"have fun",None);p.handle_chat(p.human,"gl",None)
        self.assertEqual(len(p.sent),1);self.assertIn("Psyz0r",p.sent[0])

    def test_gauntlet_damage_threshold(self):
        p=self.plugin();p.handle_damage(p.bot,p.human,10,0,"MOD_GAUNTLET")
        self.assertEqual(p.sent,[]);p.handle_damage(p.bot,p.human,39,0,"MOD_GAUNTLET")
        self.assertEqual(p.sent,[]);p.handle_damage(p.bot,p.human,1,0,"MOD_GAUNTLET")
        self.assertEqual(len(p.sent),1)

    def test_ignores_wrong_bot_and_multiple_humans(self):
        p=self.plugin();p._players.append(Player("Other",123));p.handle_chat(p.human,"gl hf",None)
        self.assertEqual(p.sent,[])

    def test_hello_topic_and_no_false_insult(self):
        self.assertEqual(chat.classify_chat("^1привет"),"hello")
        self.assertEqual(chat.classify_chat("mega"),"mega")
        self.assertIsNone(chat.classify_chat("bot"))
        p=self.plugin();p.handle_chat(p.human,"hi",None);p.handle_chat(p.human,"hello",None)
        self.assertEqual(len(p.sent),1)

    def test_plain_game_punctuation(self):
        self.assertNotIn(",",chat.render("Hello, {player} — ready?",Player("A,B",123)))

    def test_forfeit_once_only_confirmed_bot(self):
        p=self.plugin();p.forfeit_selected=True;p.forfeit_started=100
        self.assertFalse(p.maybe_forfeit(219))
        self.assertTrue(p.maybe_forfeit(220));self.assertTrue(hasattr(p.bot,'kicked'))
        self.assertFalse(hasattr(p.human,'kicked'));self.assertFalse(p.maybe_forfeit(240))

    def test_forfeit_guards_main_server_autofill_and_small_gap(self):
        for key,value in [('net_port','27960'),('bot_minplayers','1'),('qlx_psyzForfeitEnabled','0')]:
            p=self.plugin();p.forfeit_selected=True;p._cvars[key]=value
            self.assertFalse(p.maybe_forfeit(1000));self.assertFalse(hasattr(p.bot,'kicked'))
        p=self.plugin();p.forfeit_selected=True;p.human.score=17
        self.assertFalse(p.maybe_forfeit(1000))

    def test_forfeit_never_acts_with_multiple_humans(self):
        p=self.plugin();p.forfeit_selected=True;p._players.append(Player('Other',123))
        self.assertFalse(p.maybe_forfeit(1000));self.assertFalse(hasattr(p.bot,'kicked'))


if __name__ == "__main__": unittest.main()
