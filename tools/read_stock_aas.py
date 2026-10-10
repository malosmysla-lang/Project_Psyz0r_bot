"""Read stock EAAS v5 area transitions; never modify the game file."""
import argparse, collections, hashlib, json, struct
from pathlib import Path

def read_graph(path):
    raw = Path(path).read_bytes()
    if raw[:8] != b'EAAS\x05\x00\x00\x00':
        raise ValueError('Expected EAAS version 5')
    header = bytearray(raw[:124])
    if len(header) != 124:
        raise ValueError('Truncated header')
    for i in range(116):
        header[8+i] ^= (i*119)&255
    lumps = [struct.unpack_from('<ii', header, 12+i*8) for i in range(14)]
    for off, size in lumps:
        if off < 124 or size < 0 or off+size > len(raw):
            raise ValueError('Lump outside file')
    def rows(index, fmt):
        off,size=lumps[index]
        stride=struct.calcsize(fmt)
        if size%stride: raise ValueError('Unexpected structure size')
        return list(struct.iter_unpack(fmt,raw[off:off+size]))
    areas=rows(7,'<iii9f')
    settings=rows(8,'<7i')
    reaches=rows(9,'<iii6fiH2x')
    if len(areas)!=len(settings): raise ValueError('Area settings mismatch')
    edges=[]
    for source,s in enumerate(settings):
        count,first=s[5:7]
        if first<0 or count<0 or first+count>len(reaches): raise ValueError('Invalid reachability range')
        for r in reaches[first:first+count]:
            if not 0<r[0]<len(areas): raise ValueError('Invalid destination area')
            edges.append(dict(source=source,target=r[0],start=r[3:6],end=r[6:9],travel_type=r[9],travel_time=r[10]))
    return dict(sha256=hashlib.sha256(raw).hexdigest(),format='EAAS v5',area_count=len(areas),reachability_records=len(reaches),edge_count=len(edges),travel_types=dict(collections.Counter(e['travel_type'] for e in edges)),areas=[dict(id=i,center=a[9:12]) for i,a in enumerate(areas)],edges=edges)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('input');p.add_argument('output');a=p.parse_args()
    data=read_graph(a.input)
    Path(a.output).write_text(json.dumps(data,ensure_ascii=False),encoding='utf-8')
    print(json.dumps({k:v for k,v in data.items() if k not in ('areas','edges')}))
