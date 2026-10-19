"""Keep one practice bot on each test ZTN load; never manage the primary server."""
import re
import minqlx

class psyz_presence(minqlx.Plugin):
    def __init__(self):
        self.generation=0
        self.add_hook('map',self.on_map)
        self.on_map()

    def on_map(self,*args,**kwargs):
        self.generation+=1
        self.ensure(self.generation)

    @minqlx.delay(4)
    def ensure(self,generation):
        try:
            if generation!=self.generation or self.get_cvar('net_port')!='27961':return
            if self.game.map.lower() not in ('bloodrun','ztn3tourney1'):return
            # bot_minplayers остаётся 0: случайные stock-боты не подменяют Psyz0r.
            for player in self.players():
                name=re.sub(r'\^[0-9]','',player.name).lower()
                sid=int(player.steam_id)
                bot=sid==0 or (sid&0xFFFFFFFF00000000)==0x0140000100000000
                if bot and name in ('psyz0r','psyz0r_bot','pzyz0r-bot','pzyz0r_bot'):return
            minqlx.console_command('addbot Psyz0r 5 free 0 Psyz0r_bot')
        except Exception:minqlx.log_exception()
