import importlib.util,sys,types,unittest
from pathlib import Path
class PresenceTests(unittest.TestCase):
    def setUp(self):
        self.commands=[];self.people=[];self.port='27961';self.map='bloodrun'
        outer=self
        class Base:
            game=types.SimpleNamespace(map=outer.map)
            def add_hook(self,*a):pass
            def get_cvar(self,k):return outer.port
            def players(self):return outer.people
        fake=types.SimpleNamespace(Plugin=Base,delay=lambda _:lambda f:f,console_command=self.commands.append,log_exception=lambda:None)
        self.old=sys.modules.get('minqlx');sys.modules['minqlx']=fake
        spec=importlib.util.spec_from_file_location('presence_test_module',Path(__file__).resolve().parents[1]/'server/minqlx-plugins/psyz_presence.py')
        self.module=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.module)
    def tearDown(self):
        if self.old is None:sys.modules.pop('minqlx',None)
        else:sys.modules['minqlx']=self.old
    def test_empty_ztn_gets_one_bot(self):
        self.module.psyz_presence();self.assertEqual(self.commands,['addbot Psyz0r 5 free 0 Psyz0r_bot'])
    def test_existing_bot_is_not_duplicated(self):
        self.people=[types.SimpleNamespace(name='^4Psyz0r_bot',steam_id=0)];self.module.psyz_presence();self.assertEqual(self.commands,[])
    def test_primary_never_gets_bot(self):
        self.port='27960';self.module.psyz_presence();self.assertEqual(self.commands,[])
    def test_other_maps_untouched(self):
        plugin=self.module.psyz_presence();self.commands.clear();plugin.game.map='aerowalk';plugin.on_map();self.assertEqual(self.commands,[])
    def test_stale_generation_ignored(self):
        plugin=self.module.psyz_presence();self.commands.clear();plugin.ensure(plugin.generation-1);self.assertEqual(self.commands,[])
if __name__=='__main__':unittest.main()
