"""Private 27962 round robin. Measures games; does not claim automatic learning."""
import json
import time
from pathlib import Path
import minqlx

PAIRS = ((('Xaero','Lab_Xaero'),('Psyz0r','Psyz0r_bot')),
         (('Psyz0r','Psyz0r_bot'),('Xaero','Lab_Xaero')),
         (('Psyz0r','Psyz0r_bot'),('Psyz0r','Psyz0r')))

class psyz_lab(minqlx.Plugin):
    def __init__(self):
        self.round=0
        self.generation=0
        self.add_hook('map',self.on_map)
        self.add_hook('game_end',self.on_end)
        self.add_hook('death',self.on_death)
        self.add_hook('stats',self.on_stats)
        self.on_map()

    def enabled(self):
        return self.get_cvar('net_port')=='27962' and self.get_cvar('qlx_psyzLabEnabled')=='1'

    def humans(self):
        return [p for p in self.players() if int(p.steam_id)!=0 and
                (int(p.steam_id)&0xFFFFFFFF00000000)!=0x0140000100000000]

    def record(self,event,data):
        if not self.enabled():return
        path=Path(self.get_cvar('fs_homepath'))/'lab-events.jsonl'
        with path.open('a',encoding='utf-8') as out:
            out.write(json.dumps(dict(time=time.time(),round=self.round,event=event,data=data),default=str)+'\n')

    def on_map(self,*args):
        if not self.enabled():return
        self.generation+=1
        self.setup(self.generation)

    @minqlx.delay(5)
    def setup(self,generation):
        if not self.enabled() or generation!=self.generation:return
        # Any human, including a spectator, suspends automatic match changes.
        if self.humans():
            self.record('paused_for_human',{})
            return
        for p in self.players():
            sid=int(p.steam_id)
            if sid==0 or (sid&0xFFFFFFFF00000000)==0x0140000100000000:
                p.kick('Lab next controlled pair')
            else:return
        pair=PAIRS[self.round%len(PAIRS)]
        for model,name in pair:
            minqlx.console_command('addbot {} 5 free 0 {}'.format(model,name))
        self.record('pair',dict(pair=pair,automatic_learning=False))
        self.ready(generation)

    @minqlx.delay(4)
    def ready(self,generation):
        if self.enabled() and generation==self.generation and not self.humans():
            minqlx.console_command('allready')

    def on_end(self,data):
        if not self.enabled():return
        self.record('game_end',dict(result=data,scores=[dict(name=p.name,score=p.score) for p in self.players()]))
        self.round+=1
        self.next_map(self.generation)

    @minqlx.delay(10)
    def next_map(self,generation):
        if self.enabled() and generation==self.generation and not self.humans():
            minqlx.console_command('map bloodrun duel')

    def on_death(self,victim,killer,data):
        if self.enabled() and not self.humans():
            self.record('death',dict(victim=getattr(victim,'name',None),killer=getattr(killer,'name',None),detail=data))

    def on_stats(self,data):
        if self.enabled() and not self.humans() and isinstance(data,dict) and data.get('TYPE')=='PLAYER_STATS':
            self.record('player_stats',data)
