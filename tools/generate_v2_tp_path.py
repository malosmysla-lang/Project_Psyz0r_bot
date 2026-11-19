"""Read a pinned AAS and export a bounded ground/jump route after upper TP."""
import argparse,hashlib,heapq,json,math
from pathlib import Path
from associate_demo_aas import AasLocator

def main():
    ap=argparse.ArgumentParser();ap.add_argument('aas',type=Path);args=ap.parse_args()
    locator=AasLocator(args.aas);graph=locator.graph
    assert graph['sha256']=='c4ca730c12d02cb84758e8a6534bafadbb9f9e2dffc4efb7aa3559b851b55895'
    centers={a['id']:a['center'] for a in graph['areas']};adj={}
    for edge in graph['edges']:
        if edge['travel_type'] in {2,4,5,7} and min(edge['start'][2],edge['end'][2])>=400:
            adj.setdefault(edge['source'],[]).append(edge)
    distance={878:0};parent={};queue=[(0,878)]
    while queue:
        cost,node=heapq.heappop(queue)
        if cost!=distance[node]:continue
        if node==1429:break
        for e in adj.get(node,[]):
            target=e['target'];score=cost+math.dist(centers[node],e['start'])+math.dist(e['start'],e['end'])+e['travel_time']*3
            if score<distance.get(target,float('inf')):
                distance[target]=score;parent[target]=e;heapq.heappush(queue,(score,target))
    edges=[];node=1429
    while node!=878:edges.append(parent[node]);node=parent[node]['source']
    edges.reverse()
    # The teleport launches the player southwards in the air. Land on the
    # broad upper floor before turning east, rather than chasing a tiny stair.
    points=[{'p':[-560,240,536.125],'area':869,'jump':0}]
    for e in edges[2:]:
        if e['travel_type'] in {4,5}:points.append({'p':e['start'],'area':e['source'],'jump':1})
        points.append({'p':e['end'],'area':e['target'],'jump':0})
    root=Path(__file__).resolve().parents[1]
    report={'map':'bloodrun','aas_sha256':graph['sha256'],'source':'pinned AAS reachability, no Rocket-Jump links',
            'points':points,'edges':edges,'automatic_execution_requires_live_pickup':True}
    (root/'docs/training/V2_TP_PATH.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    text=['/* Generated from pinned Blood Run AAS; no rocket/BFG/teleport shortcut edges. */',
          'typedef struct { float p[3];int area,jump; } PsyzV2TPPoint;',
          'static const PsyzV2TPPoint psyz_v2_tp_points[] = {']
    for p in points:text.append('{{'+','.join(f'{v:.5f}f' for v in p['p'])+'},'+str(p['area'])+','+str(p['jump'])+'},')
    text+=['};','#define PSYZ_V2_TP_COUNT '+str(len(points))]
    (root/'adapter/native/psyz_v2_tp_path.h').write_text('\n'.join(text)+'\n',encoding='utf-8')
    print(json.dumps({'points':len(points),'normal_jumps':sum(p['jump'] for p in points)}))

if __name__=='__main__':main()
