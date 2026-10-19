"""Import known recorded duels; unknown historical versions remain unknown."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
GUNS={'gauntlet':'gauntlet','machinegun':'machinegun','shotgun':'shotgun','grenadeLauncher':'grenade','rocketLauncher':'rocket','lightningGun':'lightning','railgun':'railgun','plasmaGun':'plasma','bfg':'bfg'}
def clean(s):return re.sub(r'\^[0-9]','',s or '').strip()
def imported_player(p,actor):
    name=clean(p.get('cleanName',p.get('name','')))
    return dict(name=name,is_bot=name.casefold() in ('psyz0r','psyz0r_bot','xaero'),is_psyz=name.casefold() in ('psyz0r','psyz0r_bot'),
        score=p.get('score'),kills=p.get('kills'),deaths=p.get('deaths'),damage_given=p.get('damageGiven'),damage_taken=p.get('damageReceived'),
        play_seconds=None,pickups={k:p.get(v) for k,v in [('red','redArmorPickups'),('mega','megaHealthPickups'),('yellow','yellowArmorPickups'),('green','greenArmorPickups')]},
        weapons={gun:dict(shots=p.get(prefix+'Shots'),hits=p.get(prefix+'Hits'),accuracy_pct=p.get(prefix+'Accuracy') if p.get(prefix+'Shots',0)>0 else None,damage=p.get(prefix+'Damage'),kills=p.get(prefix+'Kills'),accuracy_source='reported_demo_scoreboard') for prefix,gun in GUNS.items()})
def main():
    matches=[];seen=set()
    owner=json.loads((ROOT/'docs/training/OWNER_MATCHES_076.json').read_text(encoding='utf-8'))['matches']
    fresh=json.loads((ROOT/'docs/training/FRESH_FEEDBACK_078.json').read_text(encoding='utf-8'))['records']
    rows=[dict(demo=r['demo'],map=r['map'],players=r['players'],duration=r.get('observed_interval_ms',r.get('duration')),category=r['category']) for r in owner if r['category'] in ('psyz0r','xaero')]
    rows += [dict(demo=r['demo'],map='bloodrun',players=r['player_stats'],duration=600000,category='psyz0r') for r in fresh]
    for r in rows:
        fingerprint=r['demo']+':'+str([(clean(p.get('cleanName',p.get('name',''))),p.get('score')) for p in r['players']])
        ident='demo:'+hashlib.sha256(fingerprint.encode()).hexdigest()[:24]
        if ident in seen:continue
        actor='psyz0r' if r['category']=='psyz0r' else 'xaero'
        ps=[imported_player(p,actor) for p in r['players'] if p.get('team')=='free' and 'score' in p]
        candidates=[p for p in ps if ('psyz' in p['name'].casefold()) if actor=='psyz0r'] if actor=='psyz0r' else [p for p in ps if p['name'].casefold()=='xaero']
        if len(candidates)!=1 or len(ps)!=2:continue
        bot=candidates[0];opponent=next(p for p in ps if p is not bot)
        seen.add(ident)
        matches.append(dict(id=ident,actor='Psyz0r' if actor=='psyz0r' else 'Xaero baseline',source='demo_udt',source_quality='recorded_scoreboard',
            demo=r['demo'],map=r['map'],version='unknown',version_source='not_saved_with_historical_demo',ended_at=None,
            date_label=re.search(r'\d{4}_\d{2}_\d{2}-\d{2}_\d{2}_\d{2}',r['demo'])[0] if re.search(r'\d{4}_\d{2}_\d{2}-\d{2}_\d{2}_\d{2}',r['demo']) else 'архив',
            duration_seconds=r['duration']/1000 if r['duration'] else None,aborted=False,opponent_type='bot' if opponent['is_bot'] else 'human',
            bot=bot,opponent=opponent,players=ps,automatic_learning=False,learning_status='not_proven_manual_policy_updates'))
    trial=json.loads((ROOT/'docs/training/PREALPHA_079_TRIAL.json').read_text())
    players=[]
    for slot,name in [('0','Psyz0r_bot'),('1','Xaero 5')]:
        picks=trial['clock_pickups_by_slot'].get(slot,{})
        players.append(dict(name=name,is_bot=True,is_psyz=slot=='0',score=trial['final_score']['Psyz0r_bot' if slot=='0' else 'Trial_Xaero'],
            kills=None,deaths=None,damage_given=None,damage_taken=None,weapons={},pickups={k:picks.get(v,0) for k,v in [('red','item_armor_body'),('mega','item_health_mega'),('yellow','item_armor_combat')]}))
    matches.append(dict(id='trial:079-first-five-minute',actor='Psyz0r',version='0.7.9',version_source='pinned_native_sha',source='server_console_trial',source_quality='scores_and_pickups_only',
        map='bloodrun',ended_at=None,date_label='19.10.2026 · тест 0.7.9',duration_seconds=300,aborted=False,opponent_type='bot',bot=players[0],opponent=players[1],players=players,
        tested_native_sha256=trial['tested_native_sha256'],automatic_learning=False,learning_status='not_proven_manual_policy_updates'))
    report=dict(schema_version=1,updated_at=None,matches=matches,automatic_learning=False,learning_status='not_proven_manual_policy_updates',
        collector=dict(mode='read_only_zmq',ready=True),limits=['Historical versions are unknown unless explicitly saved','Demo and live H/S counters may have different accuracy semantics','No automatic model training is implemented; compare like-for-like matches'])
    target=ROOT/'docs/training/MATCH_LEDGER.json';target.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Ledger',len(matches),'Psyz',sum(r['actor']=='Psyz0r' for r in matches),'baseline',sum(r['actor']!='Psyz0r' for r in matches))
if __name__=='__main__':main()
