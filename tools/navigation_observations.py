"""Observed navigation graph: measured directed transitions, not a verified navmesh."""
import argparse
import heapq
import json
import math
import re
from pathlib import Path
PATTERN=re.compile(r'PSYZ_NAV t=(\d+) pos=([-\d.,]+) vel=([-\d.,]+) yaw=([-\d.]+) weapon=(\d+) health=(-?\d+) ground=(\d+) source=stock_aas')
def read_log(text):
    return [dict(time_ms=int(m[0]),position=list(map(float,m[1].split(','))),velocity=list(map(float,m[2].split(','))),yaw=float(m[3]),weapon=int(m[4]),health=int(m[5]),ground=int(m[6])) for m in PATTERN.findall(text)]
def build_graph(rows):
    nodes={};edges={};previous=None;rejected=0;entered_time=None
    for row in rows:
        pos=row['position']
        if len(pos)!=3 or not all(math.isfinite(v) for v in pos) or row['health']<=0:
            previous=None;entered_time=None;continue
        if entered_time is None: entered_time=row['time_ms']
        key=','.join(str(math.floor(pos[i]/(64 if i<2 else 32))) for i in range(3))
        node=nodes.setdefault(key,dict(first_observed_position=pos,visits=0))
        node['visits']+=1
        if previous is not None:
            prior,pkey=previous;dt=row['time_ms']-prior['time_ms'];distance=math.dist(pos,prior['position'])
            if not 0<dt<=400 or distance>256:
                rejected+=1;entered_time=row["time_ms"]
            elif pkey!=key:
                measured=row['time_ms']-entered_time
                entered_time=row['time_ms']
                pair=(pkey,key);old=edges.get(pair)
                if old is None: edges[pair]=dict(source=pkey,target=key,observations=1,fastest_ms=measured,from_position=prior['position'],to_position=pos)
                else:
                    old['observations']+=1
                    if measured<old['fastest_ms']: old.update(fastest_ms=measured,from_position=prior['position'],to_position=pos)
        previous=row,key
    return dict(nodes=nodes,edges=list(edges.values()),rejected_discontinuities=rejected,geometry_verified=False,ready_for_execution=False,source='stock_aas_observed',cost_semantics='observed_cell_residence_plus_exit_time; spatial merging requires geometric validation')
def shortest_candidate(graph,start,goal):
    # A shared spatial bin can contain disconnected spaces: candidate only.
    if start not in graph['nodes'] or goal not in graph['nodes']:return None
    adjacency={}
    for e in graph['edges']:adjacency.setdefault(e['source'],[]).append(e)
    heap=[(0,start,[start])];best={start:0}
    while heap:
        cost,node,path=heapq.heappop(heap)
        if cost!=best[node]:continue
        if node==goal:return dict(nodes=path,cost_ms=cost,validated=False)
        for e in adjacency.get(node,[]):
            new=cost+e['fastest_ms']
            if new<best.get(e['target'],math.inf):best[e['target']]=new;heapq.heappush(heap,(new,e['target'],path+[e['target']]))
    return None

def main():
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    rows=read_log(a.log.read_text(errors='replace'));g=build_graph(rows)
    g['samples']=len(rows);g['observed_duration_ms']=rows[-1]['time_ms']-rows[0]['time_ms'] if rows else 0
    a.output.write_text(json.dumps(g,indent=2),encoding='utf-8')
    print({k:len(g[k]) for k in ['nodes','edges']},'samples',len(rows),'duration_ms',g['observed_duration_ms'])
if __name__=='__main__':main()
