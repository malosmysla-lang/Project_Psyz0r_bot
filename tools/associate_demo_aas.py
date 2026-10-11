"""Offline association of demo pickup approaches with stock AAS areas.

Area membership is not collision/physics validation. Never emits executable routes.
"""
import argparse
from collections import Counter, defaultdict
import gzip
import json
import math
from pathlib import Path
import statistics
import struct
try:
    from .read_stock_aas import read_graph
except ImportError:
    from read_stock_aas import read_graph

class AasLocator:
    def __init__(self, path):
        self.graph = read_graph(path)
        raw = Path(path).read_bytes()
        header = bytearray(raw[:124])
        for i in range(116):
            header[8+i] ^= (i*119)&255
        def rows(index, fmt):
            off, size = struct.unpack_from('<ii', header, 12+index*8)
            stride = struct.calcsize(fmt)
            if size % stride:
                raise ValueError('Unexpected plane/node record size')
            return list(struct.iter_unpack(fmt, raw[off:off+size]))
        self.planes = rows(2, '<4fi')
        self.nodes = rows(10, '<3i')
        self.edges = {(e['source'], e['target']) for e in self.graph['edges']}
        for plane, front, back in self.nodes[1:]:
            if not 0 <= plane < len(self.planes):
                raise ValueError('Invalid plane index')
            for child in (front, back):
                if child >= len(self.nodes) or -child >= self.graph['area_count']:
                    raise ValueError('Invalid BSP child')

    def area(self, point):
        if len(point) != 3 or not all(math.isfinite(v) for v in point):
            raise ValueError('Invalid point')
        node = 1
        for _ in range(len(self.nodes)):
            if node <= 0:
                return -node
            if node >= len(self.nodes):
                raise ValueError('Invalid BSP node')
            plane, front, back = self.nodes[node]
            nx, ny, nz, dist, _ = self.planes[plane]
            node = front if point[0]*nx+point[1]*ny+point[2]*nz-dist > 0 else back
        raise ValueError('BSP cycle')

def associate(route, locator):
    points = route['points']
    if len(points) < 2:
        raise ValueError('Too few samples')
    for prior, current in zip(points, points[1:]):
        if not 0 < current['t']-prior['t'] <= 100 or math.dist(current['p'], prior['p']) > 256:
            raise ValueError('Discontinuous approach')
    sequence = []
    solid = 0
    for point in points:
        area = locator.area(point['p'])
        solid += area == 0
        if not sequence or sequence[-1] != area:
            sequence.append(area)
    pairs = list(zip(sequence, sequence[1:]))
    direct = sum(pair in locator.edges for pair in pairs)
    return dict(kind=route['kind'], pickup_ms=route['pickup_ms'], client=route['client'],
                segment=route['segment'], duration_ms=points[-1]['t']-points[0]['t'],
                areas=sequence, sample_count=len(points), solid_samples=solid,
                direct_aas_transitions=direct, unresolved_transitions=len(pairs)-direct,
                association_complete=solid == 0, geometry_verified=False,
                physics_verified=False, ready_for_execution=False)

def analyze(aas, corpora, output):
    locator = AasLocator(aas)
    output.mkdir(parents=True, exist_ok=True)
    records=[]; counts=Counter(); groups=defaultdict(list); hashes=set(); areas=set()
    for corpus in corpora:
        index=json.loads((corpus/'analysis_index.json').read_text(encoding='utf-8'))
        for row in index['records']:
            if row.get('status') != 'parsed' or row.get('maps') != ['bloodrun']:
                counts['excluded_index_records']+=1
                continue
            path=corpus/str(row['archive_id'])/'observed_approaches.json.gz'
            with gzip.open(path,'rt',encoding='utf-8') as source:
                data=json.load(source)
            if data['map'] != 'bloodrun' or data['source_sha256'] != row['source_sha256']:
                raise ValueError('Source map/hash mismatch: '+str(path))
            if data['source_sha256'] in hashes:
                counts['duplicate_demo_files']+=1
                continue
            hashes.add(data['source_sha256']); counts['demos']+=1
            for ordinal, route in enumerate(data['routes']):
                counts['input_approaches']+=1
                try:
                    match=associate(route,locator)
                except ValueError:
                    counts['rejected_discontinuous_approaches']+=1
                    continue
                match.update(source_sha256=data['source_sha256'], archive_id=row['archive_id'],
                             corpus=corpus.name, source_route_index=ordinal)
                records.append(match)
                counts['associated_approaches']+=1
                counts['samples']+=match['sample_count']
                counts['solid_samples']+=match['solid_samples']
                counts['direct_aas_transitions']+=match['direct_aas_transitions']
                counts['unresolved_transitions']+=match['unresolved_transitions']
                counts['complete_area_associations']+=match['association_complete']
                areas.update(a for a in match['areas'] if a)
                if match['association_complete']:
                    groups[(match['kind'],tuple(match['areas']))].append(match)
            if counts['demos']%20==0:
                print('Associated demos:',counts['demos'],flush=True)
    candidates=[]
    for (kind,sequence), observations in groups.items():
        candidates.append(dict(kind=kind,areas=sequence,observations=len(observations),
           unique_demo_files=len({o['source_sha256'] for o in observations}),
           median_observed_window_ms=statistics.median(o['duration_ms'] for o in observations),
           source_examples=[dict(source_sha256=o['source_sha256'],pickup_ms=o['pickup_ms'],
                                source_route_index=o['source_route_index'],corpus=o['corpus'])
                            for o in observations[:3]],ready_for_execution=False))
    candidates.sort(key=lambda x:(-x['unique_demo_files'],-x['observations'],x['kind']))
    with gzip.open(output/'approaches_with_aas.json.gz','wt',encoding='utf-8') as target:
        json.dump(records,target)
    with gzip.open(output/'candidate_catalog.json.gz','wt',encoding='utf-8') as target:
        json.dump(candidates,target)
    summary=dict(map='bloodrun',aas_sha256=locator.graph['sha256'],counts=dict(counts),
       observed_area_count=len(areas),candidate_sequence_count=len(candidates),
       repeated_sequence_count=sum(c['unique_demo_files']>=2 for c in candidates),
       repeated_multi_area_sequence_count=sum(c['unique_demo_files']>=2 and len(c['areas'])>=2 for c in candidates),
       single_area_sequence_count=sum(len(c['areas'])==1 for c in candidates),
       top_candidates=[c for c in candidates if len(c['areas'])>=2][:12],geometry_verified=False,physics_verified=False,
       ready_for_execution=False,semantics='AAS BSP point association only; unresolved edges may skip intermediate areas; windows are not full routes; different POV files may represent the same match')
    (output/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items() if k!='top_candidates'},ensure_ascii=False))
    return summary

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--aas',type=Path,required=True)
    p.add_argument('--corpus',type=Path,action='append',required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    analyze(a.aas,a.corpus,a.output)
