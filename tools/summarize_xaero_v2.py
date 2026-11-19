"""Summarize every preserved owner-v-Xaero scoreboard without mixing rankings."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import re


def clean(s):return re.sub(r'\^[0-9]','',s or '').strip().casefold()


def summarize(parsed):
    rows=[];clips=[];seen=set()
    for demo in parsed:
        relevant=False
        for index,m in enumerate(demo.get('matches',[])):
            ps=[p for p in m.get('playerStats',[]) if p.get('team')=='free' and 'score' in p]
            names={clean(p.get('cleanName',p.get('name'))) for p in ps}
            if names!={'nekitz0r','xaero'} or len(ps)!=2:
                continue
            relevant=True
            key=(demo['sha256'],index)
            if key in seen:continue
            seen.add(key)
            owner=next(p for p in ps if clean(p.get('cleanName',p.get('name')))=='nekitz0r')
            bot=next(p for p in ps if p is not owner)
            complete=bool(m.get('intermissionEndTime')) and not m.get('forfeited')
            rows.append({'demo_sha256':demo['sha256'],'match_index':index,'map':m.get('map'),
                         'complete':complete,'forfeited':m.get('forfeited'),'start_date':m.get('startDate'),
                         'observed_seconds':(m['endTime']-m['startTime'])/1000,
                         'owner':owner,'xaero':bot})
        if not relevant and any('xaero' in Path(p).name.casefold() and 'nekitz0r' in Path(p).name.casefold()
                                for p in demo.get('originals',[])):
            clips.append({'sha256':demo['sha256'],'status':'filename_candidate_without_two_player_scoreboard'})
    by_map=defaultdict(list)
    for row in rows:
        if row['complete']:by_map[row['map']].append(row)
    summaries={}
    for mapname,ms in sorted(by_map.items()):
        sides={}
        for side in ('owner','xaero'):
            weapons={}
            for weapon in ('machinegun','shotgun','rocketLauncher','lightningGun','railgun','plasmaGun','grenadeLauncher'):
                available=[m[side] for m in ms if m[side].get(weapon+'Shots') is not None and m[side].get(weapon+'Hits') is not None]
                shots=sum(p[weapon+'Shots'] for p in available);hits=sum(p[weapon+'Hits'] for p in available)
                weapons[weapon]={'shots':shots,'hits':hits,'weighted_accuracy_pct':100*hits/shots if shots else None,
                                 'matches_with_counters':len(available),'semantics':'recorded scoreboard H/S; weapon counters differ'}
            pickups={}
            for name,field in [('red','redArmorPickups'),('mega','megaHealthPickups'),('yellow','yellowArmorPickups')]:
                known=[m[side][field] for m in ms if m[side].get(field) is not None]
                pickups[name]={'total':sum(known) if known else None,'matches_with_counters':len(known)}
            sides[side]={'pickups':pickups,'weapons':weapons}
        summaries[mapname]={'completed_matches':len(ms),**sides}
    return {'records':rows,'clip_candidates':clips,'maps':summaries,
            'summary':{'scoreboards':len(rows),'completed':sum(r['complete'] for r in rows),
                       'incomplete_or_forfeit':sum(not r['complete'] for r in rows),
                       'filename_candidates_only':len(clips),'unique_demo_sources':len({r['demo_sha256'] for r in rows})}}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('intake',type=Path);ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args();result=summarize(json.loads((args.intake/'PARSED_DEMOS.private.json').read_text(encoding='utf-8')))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result['summary']))


if __name__=='__main__':main()
