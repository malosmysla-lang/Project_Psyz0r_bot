"""Read-only ZMQ sidecar for 27961. Never sends game commands or edits the bot."""
import argparse,datetime,hashlib,json,os,re,shlex,time
from pathlib import Path
BOT_NAMES={'psyz0r','psyz0r_bot','pzyz0r-bot','pzyz0r_bot'}
WEAPONS={'GAUNTLET':'gauntlet','MACHINEGUN':'machinegun','SHOTGUN':'shotgun','GRENADE':'grenade','ROCKET':'rocket','LIGHTNING':'lightning','RAILGUN':'railgun','PLASMA':'plasma','BFG':'bfg'}
def clean(value):return re.sub(r'\^[0-9]','',str(value or '')).strip()[:80]
def number(value):
    return value if isinstance(value,(int,float)) and not isinstance(value,bool) and -100000000<value<100000000 else None
def utc(now):return datetime.datetime.fromtimestamp(now,datetime.timezone.utc).isoformat()
def bot_sid(value):
    try:
        sid=int(value);return sid==0 or (sid&0xFFFFFFFF00000000)==0x0140000100000000
    except (TypeError,ValueError):return False
def sanitize_player(data):
    name=clean(data.get('NAME'));guns={}
    for raw,key in WEAPONS.items():
        w=data.get('WEAPONS',{}).get(raw,{})
        shots,hits=number(w.get('S')),number(w.get('H'))
        accuracy=round(100*hits/shots,2) if shots is not None and shots>0 and hits is not None and 0<=hits<=shots else None
        guns[key]=dict(shots=shots,hits=hits,accuracy_pct=accuracy,damage=number(w.get('DG')),kills=number(w.get('K')),
            accuracy_source='derived_hits_over_shots' if accuracy is not None else 'unavailable_or_counter_semantics')
    pickups=data.get('PICKUPS',{});damage=data.get('DAMAGE',{})
    return dict(name=name,is_bot=bot_sid(data.get('STEAM_ID')),is_psyz=name.casefold() in BOT_NAMES,
        score=number(data.get('SCORE')),kills=number(data.get('KILLS')),deaths=number(data.get('DEATHS')),
        damage_given=number(damage.get('DEALT')),damage_taken=number(damage.get('TAKEN')),
        play_seconds=number(data.get('PLAY_TIME')),won=data.get('WIN')==1,quit=data.get('QUIT')==1,
        pickups={key:number(pickups.get(raw)) for raw,key in [('RED_ARMOR','red'),('YELLOW_ARMOR','yellow'),('GREEN_ARMOR','green'),('MEGA_HEALTH','mega'),('HEALTH','health'),('AMMO','ammo')]},weapons=guns)

def atomic(path,data,private=False):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(path.suffix+'.tmp');temp.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    if private:os.chmod(temp,0o600)
    temp.replace(path)

class Collector:
    def __init__(self,directory,version_reader,now=time.time,binary_hash_reader=lambda:None):
        self.directory=Path(directory);self.version_reader=version_reader;self.now=now
        self.pending={};self.matches={};self.events=0;self.last_event=None;self.binary_hash_reader=binary_hash_reader
        p=self.directory/'private_state.json'
        if p.exists():
            state=json.loads(p.read_text(encoding='utf-8'));self.pending=state.get('pending',{});self.matches=state.get('matches',{})
    def handle(self,event):
        kind=event.get('TYPE');data=event.get('DATA')
        if kind not in ('MATCH_STARTED','PLAYER_STATS','MATCH_REPORT') or not isinstance(data,dict):return
        guid=data.get('MATCH_GUID')
        if not isinstance(guid,str) or not re.fullmatch(r'[A-Za-z0-9_-]{6,100}',guid):return
        if kind=='PLAYER_STATS' and data.get('WARMUP') is not False:return
        stamp=self.now();self.events+=1;self.last_event=utc(stamp)
        state=self.pending.setdefault(guid,dict(version=self.version_reader(),version_source='config_at_stats_receive',players={},created_at=utc(stamp)))
        state['updated']=stamp;state['finalized']=False
        if kind=='MATCH_STARTED':
            state.update(started_at=utc(stamp),header=data,version=self.version_reader(),version_source='config_at_match_start',native_sha256=self.binary_hash_reader())
        elif kind=='PLAYER_STATS':
            # GUID + server identity deduplicate retransmissions without merging
            # two different same-name humans. Identity never enters public JSON.
            sid=data.get('STEAM_ID')
            identity=str(sid)+':'+clean(data.get('NAME')) if bot_sid(sid) else str(sid or clean(data.get('NAME')))
            state['players'][identity]=data
        else:state['report']=data;state['reported_at']=utc(stamp)
        self.save_private()
    def save_private(self):atomic(self.directory/'private_state.json',dict(pending=self.pending,matches=self.matches),True)
    def flush(self,force=False):
        changed=False
        for guid,state in list(self.pending.items()):
            if state.get('finalized') or 'report' not in state or (not force and self.now()-state['updated']<4):continue
            players=[sanitize_player(p) for p in state['players'].values()]
            ours=[p for p in players if p['is_psyz']];r=state['report'];header=state.get('header',{})
            if len(ours)!=1:continue
            others=[p for p in players if p is not ours[0]]
            game_type=str(r.get('GAME_TYPE',header.get('GAME_TYPE',''))).upper()
            if game_type and game_type!='DUEL':continue
            if len(others)!=1:continue # Do not silently label FFA as Duel.
            duration=max((p['play_seconds'] or 0 for p in players),default=0) or None
            record=dict(id='live:'+guid,source='quakelive_zmq',source_quality='server_report',map=clean(r.get('MAP',header.get('MAP'))),
                version=state['version'],version_source=state['version_source'],native_sha256=state.get('native_sha256'),started_at=state.get('started_at'),ended_at=state.get('reported_at',utc(self.now())),
                duration_seconds=duration,aborted=bool(r.get('ABORTED')),opponent_type='bot' if others[0]['is_bot'] else 'human',
                bot=ours[0],opponent=others[0],players=players,automatic_learning=False,
                learning_status='not_proven_manual_policy_updates',counter_semantics='WEAPONS H/S; splash/pellet counters are not interchangeable with hitscan')
            self.matches[guid]=record;changed=True
            # Keep a compact finalized marker. Late corrected stats can reopen it.
            state['finalized']=True
        if changed:self.save_private()
        records=sorted(self.matches.values(),key=lambda r:r.get('ended_at') or '')
        atomic(self.directory/'public_matches.json',dict(schema_version=1,updated_at=utc(self.now()),matches=records,
            collector=dict(read_only=True,source='127.0.0.1:27961 ZMQ',events=self.events,last_event=self.last_event),
            automatic_learning=False,learning_status='not_proven_manual_policy_updates'))
        # Remove only old finalized buffers; the durable public match is retained.
        for guid,s in list(self.pending.items()):
            if s.get('finalized') and self.now()-s['updated']>300:del self.pending[guid]

def settings(home):
    values={};seen=set();base=(home/'baseq3').resolve()
    def read(path):
        path=path.resolve()
        if path in seen or not path.is_relative_to(base) or not path.is_file():return
        seen.add(path)
        for line in path.read_text(errors='replace').splitlines():
            try:args=shlex.split(line,comments=True)
            except ValueError:continue
            if len(args)>=3 and args[0] in ('set','seta','sets') and args[1] in ('zmq_stats_password','zmq_stats_port','zmq_stats_enable','qlx_psyzVersion'):values[args[1]]=args[2]
            elif len(args)>=2 and args[0]=='exec':read(base/args[1])
    read(base/'psyz_test.cfg');return values

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--home',type=Path,default=Path('/home/qlserver/psyz0r-test-server-home'));ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    cfg=settings(a.home);port=int(cfg.get('zmq_stats_port','27961'))
    if port!=27961:raise RuntimeError('Refusing non-test stats endpoint')
    import zmq
    ctx=zmq.Context();sock=ctx.socket(zmq.SUB);sock.setsockopt(zmq.SUBSCRIBE,b'');sock.setsockopt(zmq.LINGER,0)
    if cfg.get('zmq_stats_password'):
        sock.plain_username=b'stats';sock.plain_password=cfg['zmq_stats_password'].encode();sock.zap_domain=b'stats'
    sock.connect('tcp://127.0.0.1:27961')
    binary=Path('/home/qlserver/psyz0r-test-server/psyz_test/minqlx_nopy.so')
    collector=Collector(a.output,lambda:settings(a.home).get('qlx_psyzVersion','unknown'),binary_hash_reader=lambda:hashlib.sha256(binary.read_bytes()).hexdigest() if binary.exists() else None)
    print('PSYZ_MATCH_COLLECTOR ready read_only=1 endpoint=127.0.0.1:27961',flush=True)
    last=0
    while True:
        if sock.poll(1000):
            raw=sock.recv()
            try:collector.handle(json.loads(raw))
            except (ValueError,TypeError,KeyError):print('Ignored malformed stats event',flush=True)
        if time.time()-last>=5:collector.flush();last=time.time()
if __name__=='__main__':main()
