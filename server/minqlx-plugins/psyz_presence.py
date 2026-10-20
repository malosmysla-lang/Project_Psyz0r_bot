"""Keep one practice bot on each test ZTN load; never manage the primary server."""
import re
import minqlx

class psyz_presence(minqlx.Plugin):
    def __init__(self):
        self.generation=0
        self.add_hook('map',self.on_map)
        self.add_command('psyz_brand_status',self.brand_status,5)
        self.on_map()

    def on_map(self,*args,**kwargs):
        self.generation+=1
        self.ensure(self.generation)

    @minqlx.delay(4)
    def ensure(self,generation):
        try:
            if generation!=self.generation or self.get_cvar('net_port')!='27961':return
            if self.game.map.lower() not in ('bloodrun','ztn3tourney1'):return
            # Replace only the two minqlx loading-screen branding lines on test.
            # Preserve all third-party copyright/license notices in source/docs.
            minqlx.set_configstring(678,'^4ProQ^7room Server ^4Bot')
            minqlx.set_configstring(679,'^7Blood Run / ZTN | Training Duel | test 27961')
            # bot_minplayers остаётся 0: случайные stock-боты не подменяют Psyz0r.
            for player in self.players():
                name=re.sub(r'\^[0-9]','',player.name).lower()
                sid=int(player.steam_id)
                bot=sid==0 or (sid&0xFFFFFFFF00000000)==0x0140000100000000
                if bot and name in ('psyz0r','psyz0r_bot','pzyz0r-bot','pzyz0r_bot'):return
            minqlx.console_command('addbot Psyz0r 5 free 0 Psyz0r_bot')
        except Exception:minqlx.log_exception()

    def brand_status(self,player,msg,channel):
        """Console-only evidence of the two loading-screen lines on test 27961."""
        console_player=player is None or isinstance(player,getattr(minqlx,'RconDummyPlayer',()))
        if not console_player or str(channel)!='console' or self.get_cvar('net_port')!='27961':return
        minqlx.console_print('PSYZ_BRAND 678=^4ProQ^7room Server ^4Bot 679=^7Blood Run / ZTN | Training Duel | test 27961')
