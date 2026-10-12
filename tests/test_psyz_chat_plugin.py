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


fake = types.SimpleNamespace(Plugin=Plugin, RET_STOP_ALL=1,
                             delay=lambda seconds: (lambda fn: fn),
                             log_exception=lambda: None)
sys.modules["minqlx"] = fake
path = Path(__file__).parents[1] / "server" / "minqlx-plugins" / "psyz_chat.py"
spec = importlib.util.spec_from_file_location("psyz_chat", path)
chat = importlib.util.module_from_spec(spec); spec.loader.exec_module(chat)


class Player:
    def __init__(self, name, sid): self.name=self.clean_name=name;self.steam_id=sid


class ChatTests(unittest.TestCase):
    def plugin(self):
        p=chat.psyz_chat();p.sent=[]
        p.human=Player("Human",7656119);p.bot=Player("Psyz0r",0x0140000100000000)
        p._players=[p.human,p.bot];p.game=types.SimpleNamespace(state="in_progress")
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
        self.assertEqual(p.sent,[]);p.handle_damage(p.bot,p.human,15,0,"MOD_GAUNTLET")
        self.assertEqual(len(p.sent),1)

    def test_ignores_wrong_bot_and_multiple_humans(self):
        p=self.plugin();p._players.append(Player("Other",123));p.handle_chat(p.human,"gl hf",None)
        self.assertEqual(p.sent,[])


if __name__ == "__main__": unittest.main()
