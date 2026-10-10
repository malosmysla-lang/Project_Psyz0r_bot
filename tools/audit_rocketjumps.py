"""Offline rocket-jump audit. Demo events are evidence, not bot commands."""
import argparse
import ctypes as c
import json
import hashlib
from pathlib import Path

ITEMS = {19:'red',20:'yellow',21:'green',22:'shard',30:'health',31:'health_large',32:'mega',33:'health_small',46:'bfg',47:'chaingun',48:'gauntlet',49:'grapple',50:'grenade',51:'hmg',52:'lightning',53:'machinegun',54:'nailgun',55:'plasma',56:'prox',57:'railgun',58:'rocket',59:'shotgun'}
REWARD_ITEMS = {'red','yellow','green','mega','health','health_large','health_small'} | {v for k,v in ITEMS.items() if k>=46}

def marker_label(text):
    return text.strip().rstrip('/\\').strip() == '#bot rocketjump'

def classify(gain, pickups, complete):
    if not complete:
        return 'unknown'
    # 8 units is a conservative tolerance for stair/snapshot quantization.
    return 'success' if gain > 8 or any(p['kind'] in REWARD_ITEMS for p in pickups) else 'unsuccessful'

def analyze(rows, chat, decode_item):
    markers=[m for m in chat if marker_label(m.get('cleanMessage',''))]
    result=[]
    for n,m in enumerate(markers):
        time=m['serverTime']; end=min(time+10000,markers[n+1]['serverTime'] if n+1<len(markers) else rows[-1]['time_ms']+1)
        indices=[i for i,x in enumerate(rows) if time<=x['time_ms']<end and x['client']==m['clientNumber'] and x['game_state_number']==m['gameStateNumber'] and x['weapon_id']==5 and any(e['kind']=='weapon_fired' for e in x['events'])]
        if not indices:
            result.append(dict(marker_ms=time,status='unknown',reason='no_rocket_shot_in_10s'))
        for i in indices:
            shot=rows[i]; identity=(shot['segment'],shot['client'],shot['game_state_number'])
            def same(x): return (x['segment'],x['client'],x['game_state_number'])==identity and x['pm_type']==0
            nearby=[j for j in range(max(1,i-6),min(len(rows),i+9)) if same(rows[j]) and same(rows[j-1]) and 0<rows[j]['time_ms']-rows[j-1]['time_ms']<=100]
            impulses=[j for j in nearby if rows[j]['velocity'][2]-rows[j-1]['velocity'][2]>100 and rows[j]['velocity'][2]>300]
            entry=dict(marker_ms=time,shot_ms=shot['time_ms'],shot_position=shot['position'],shot_viewangles=shot['viewangles'])
            if not impulses:
                entry.update(status='excluded',reason='no_vertical_rocket_impulse_observed');result.append(entry);continue
            boost=min(impulses,key=lambda j:abs(rows[j]['time_ms']-shot['time_ms']))
            start=boost-1
            while start>0 and same(rows[start]) and rows[start]['ground_entity']==1023 and rows[boost]['time_ms']-rows[start]['time_ms']<1000: start-=1
            air=next((j for j in range(boost,min(boost+10,len(rows))) if same(rows[j]) and rows[j]['ground_entity']==1023),None)
            land=None; reason='landing_not_observed'
            if air is not None:
                for j in range(air+1,len(rows)):
                    if not same(rows[j]) or rows[j]['time_ms']-rows[j-1]['time_ms']>100: reason='state_discontinuity';break
                    if rows[j]['time_ms']-rows[boost]['time_ms']>5000: break
                    if rows[j]['ground_entity']!=1023: land=j;break
            complete=land is not None and same(rows[start]) and rows[start]['ground_entity']!=1023
            stop=land if land is not None else min(boost+200,len(rows)-1)
            pickups=[]
            for x in rows[i:stop+1]:
                if not same(x): break
                for e in x['events']:
                    if e['udt_event_id'] in (2,3):
                        kind=decode_item(e['parameter'])
                        if kind: pickups.append(dict(time_ms=x['time_ms'],kind=kind))
            # Pickups within 1.5 s after landing count only before the next launch/shot,
            # and within 96 horizontal units of the landing point.
            if land is not None:
                for x in rows[land+1:]:
                    if not same(x) or x['time_ms']-rows[land]['time_ms']>1500: break
                    if x['ground_entity']==1023 or any(e['kind']=='weapon_fired' for e in x['events']): break
                    if sum((x['position'][a]-rows[land]['position'][a])**2 for a in (0,1))>96**2: break
                    for e in x['events']:
                        if e['udt_event_id'] in (2,3):
                            kind=decode_item(e['parameter'])
                            if kind: pickups.append(dict(time_ms=x['time_ms'],kind=kind))
            gain=rows[land]['position'][2]-rows[start]['position'][2] if complete else None
            entry.update(start_ms=rows[start]['time_ms'],start_position=rows[start]['position'],boost_ms=rows[boost]['time_ms'],landing_ms=rows[land]['time_ms'] if land is not None else None,landing_position=rows[land]['position'] if land is not None else None,height_gain=round(gain,2) if gain is not None else None,apex_z=max(x['position'][2] for x in rows[boost:stop+1]),health_before=rows[start]['health'],health_after=rows[stop]['health'],armor_before=rows[start]['armor'],armor_after=rows[stop]['armor'],pickups=pickups,status=classify(gain,pickups,complete),reason=('higher_landing' if gain > 8 else 'immediate_pickup' if classify(gain,pickups,True)=='success' else 'same_or_lower_landing_without_reward') if complete else reason)
            result.append(entry)
    return result

def main():
    ap=argparse.ArgumentParser();ap.add_argument('folder',type=Path);ap.add_argument('demo',type=Path);args=ap.parse_args()
    dll=c.CDLL(str(Path(__file__).parent.resolve()/'udt/bin/UDT.dll'))
    dll.udtGetVersionString.restype=c.c_char_p
    if dll.udtGetVersionString()!=b'1.3.1': raise RuntimeError('Expected UDT 1.3.1')
    if dll.udtInitLibrary()!=0: raise RuntimeError('UDT init failed')
    dll.udtGetProtocolByFilePath.argtypes=[c.c_char_p];dll.udtGetProtocolByFilePath.restype=c.c_uint32
    protocol=dll.udtGetProtocolByFilePath(str(args.demo.resolve()).encode())
    fn=dll.udtGetUDTMagicNumber;fn.argtypes=[c.POINTER(c.c_int32),c.c_uint32,c.c_int32,c.c_uint32,c.c_uint32];fn.restype=c.c_int32
    def decode(parm):
        item=c.c_int32()
        return ITEMS.get(item.value) if fn(c.byref(item),12,parm,protocol,0)==0 else None
    data=json.loads((args.folder/(args.demo.stem+'.json')).read_text());rows=[json.loads(x) for x in (args.folder/'snapshots.jsonl').read_text().splitlines()]
    try: results=analyze(rows,data.get('chat',[]),decode)
    finally: dll.udtShutDownLibrary()
    out=dict(demo=args.demo.name,demo_sha256=hashlib.sha256(args.demo.read_bytes()).hexdigest(),parser='UDT 1.3.1',criteria='higher first landing (>8 units tolerance) OR pickup during maneuver / nearby within 1.5s after landing',physics_verified=False,results=results)
    (args.folder/'rocketjump_audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({s:sum(x['status']==s for x in results) for s in ['success','unsuccessful','unknown','excluded']}))

if __name__=='__main__': main()
