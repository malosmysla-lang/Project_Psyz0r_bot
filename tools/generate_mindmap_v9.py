"""Versioned MD -> PNG/SVG/OPML/HTML/JSON; v4 is retained unchanged."""
from pathlib import Path
import hashlib
import json
import re
import types
from collections import Counter
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
# Reuse the established visual language, with version/date fixed before rendering.
base_path = ROOT/'tools/generate_mindmap_v4.py'
source = base_path.read_text(encoding='utf-8').replace('v4','v9').replace('V4','V9').replace('12.10.2026','19.10.2026')
source = source.replace('Человечная игра\\nбез WH и физических читов','Сильная человеческая игра\\nobserver-таймеры и стек\\nбез скрытого наведения')
base=types.ModuleType('mindmap_v9_renderer');base.__file__=str(base_path)
exec(compile(source,str(base_path),'exec'),base.__dict__)
OUT=base.OUT
layout=[]

def lines_px(draw,text,fnt,width):
    result=[];line=''
    for word in text.split():
        candidate=(line+' '+word).strip()
        if line and draw.textlength(candidate,font=fnt)>width:
            result.append(line);line=word
        else:line=candidate
    return result+[line]

def detail_sheets(branches,conflicts):
    paths=[]
    groups=[(b['letter'],b['title'],b['items'],base.COLORS[i]) for i,b in enumerate(branches)]
    groups.append(('16','Решения, ограничения и открытые вопросы',[
        {'id':f'Q{i:02d}','status':'CONFLICT','text':t} for i,t in enumerate(conflicts,1)],'#FF747C'))
    for letter,title,items,color in groups:
        page=1;index=0
        while index<len(items):
            im=base.Image.new('RGB',(3840,2160),'#151922');d=base.ImageDraw.Draw(im)
            d.rounded_rectangle((90,70,3750,295),42,fill='#222936',outline=color,width=5)
            f=base.font(49,True)
            titlelines=lines_px(d,letter+'. '+title,f,3500)
            d.multiline_text((145,100),'\n'.join(titlelines),font=f,fill=color,spacing=4)
            d.text((145,244),f'{len(items)} правил | v9 | 19.10.2026 | лист {page} | статусы по документальным свидетельствам',font=base.font(23),fill='#B5C1D3')
            ypos=[350,350];nstart=index
            while index<len(items):
                item=items[index];fnt=base.font(25)
                lines=lines_px(d,item['text'],fnt,1695)
                cardh=84+len(lines)*35
                col=min(range(2),key=lambda c:ypos[c]);x=[150,2000][col];y=ypos[col]
                if y+cardh>2040:break
                sc=base.STATUS_COLORS.get(item['status'].split('/')[0],'#D0D6E2')
                d.rounded_rectangle((x,y,x+1760,y+cardh),22,fill='#202632',outline='#343C4D',width=2)
                d.ellipse((x+24,y+23,x+46,y+45),fill=sc)
                d.text((x+64,y+15),item['id']+'  '+item['status'],font=base.font(25,True),fill=sc)
                d.multiline_text((x+28,y+62),'\n'.join(lines),font=fnt,fill='#E6EAF0',spacing=9)
                layout.append({'id':item['id'],'page':f'{letter}_{page}','bounds':[x,y,x+1760,y+cardh]})
                ypos[col]+=cardh+18;index+=1
            assert index>nstart,('oversize card',letter,index)
            d.text((150,2090),'SPEC = требование | DATA = материал | LOCAL = локальная реализация | PARTIAL = часть проверена | LIVE = наблюдалось в игре',font=base.font(21),fill='#9DA8BA')
            stem=f'{ord(letter)-64:02d}_{letter}_detail' if len(letter)==1 else '16_conflicts_detail'
            if page>1:stem+=f'_p{page}'
            path=OUT/(stem+'.png');im.save(path,dpi=(100,100),optimize=True);paths.append(path);page+=1
    return paths

def full_svg(branches):
    # Complete scalable reference: every rule is retained, with measured text wrap.
    dummy=base.ImageDraw.Draw(base.Image.new('RGB',(1,1)))
    cards=[];heights=[]
    for i,b in enumerate(branches):
        yy=95;body=[]
        for item in b['items']:
            textlines=lines_px(dummy,item['text'],base.font(22),1000)
            sc=base.STATUS_COLORS.get(item['status'].split('/')[0],'#D0D6E2')
            body.append(base.svg_text([item['id']+' '+item['status']],30,yy,22,sc,weight=700))
            body.append(base.svg_text(textlines,30,yy+31,22,'#E6EAF0',gap=1.4))
            yy+=65+len(textlines)*31
        cards.append((b,body,yy));heights.append(yy+20)
    rows=[max(heights[i:i+3]) for i in range(0,len(heights),3)]
    w=3480;h=200+sum(rows)+len(rows)*45
    out=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">','<rect width="100%" height="100%" fill="#151922"/>',base.svg_text(['Psyz0r_bot | полный реестр v9 | 19.10.2026'],50,80,42,'#74D8FF',weight=700)]
    yy=145
    for row in range(5):
        for col in range(3):
            i=row*3+col;b,body,ch=cards[i];xx=45+col*1140;color=base.COLORS[i]
            out.append(f'<g transform="translate({xx},{yy})"><rect width="1100" height="{ch}" rx="22" fill="#202632" stroke="{color}" stroke-width="3"/>')
            out.append(base.svg_text(base.wrap(b['letter']+'. '+b['title'],55),30,36,25,color,weight=700))
            out+=body;out.append('</g>')
        yy+=rows[row]+45
    out.append('</svg>');p=OUT/'Psyz0r_bot_mindmap_v9_full.svg';p.write_text('\n'.join(out),encoding='utf-8');return p

def summary(branches):
    im=base.Image.new('RGB',(4096,2048),'#151922');d=base.ImageDraw.Draw(im)
    d.text((70,40),'PSYZ0R_BOT | логика и приоритеты v9',font=base.font(55,True),fill='white')
    d.text((70,115),'19.10.2026 | сильный тестовый профиль | observer-таймеры/стек | статус не равен общему % готовности',font=base.font(26),fill='#79D8FF')
    for i,b in enumerate(branches):
        col=i%3;row=i//3;x=65+col*1348;y=200+row*340;color=base.COLORS[i]
        d.rounded_rectangle((x,y,x+1295,y+312),20,fill='#222936',outline=color,width=3)
        title=lines_px(d,b['letter']+'. '+b['title'],base.font(31,True),1225)
        d.multiline_text((x+24,y+18),'\n'.join(title),font=base.font(31,True),fill=color,spacing=3)
        counts=Counter(it['status'].split('/')[0] for it in b['items'])
        d.text((x+24,y+110),f"{len(b['items'])} правил | "+' · '.join(f'{k}:{v}' for k,v in counts.items()),font=base.font(21),fill='#D5DEEC')
        # Explicitly a pointer sheet; full wording remains on every detail page.
        chosen=b['items'][-2:]
        yy=y+156
        for item in chosen:
            lines=lines_px(d,item['id']+': '+item['text'],base.font(22),1225)
            if len(lines)>2:lines=lines[:2];lines[-1]+=' …'
            d.multiline_text((x+24,yy),'\n'.join(lines),font=base.font(22),fill='#E6EAF0',spacing=3);yy+=68
    d.text((70,1940),'Обзор: новые акценты и указатели. Полные формулировки без сокращений — листы A–O, SVG, OPML, HTML и MD.',font=base.font(26),fill='#B7C3D4')
    p=OUT/'Psyz0r_bot_logic_summary_v9_4096x2048.png';im.save(p,dpi=(100,100),optimize=True);return p

def main():
    OUT.mkdir(exist_ok=True,parents=True)
    center,branches,conflicts=base.parse()
    oldbranches=json.loads((ROOT/'docs/mindmap_v8/logic_registry_v8.json').read_text(encoding='utf-8'))['branches']
    oldids={i['id'] for b in oldbranches for i in b['items']}
    ids=[i['id'] for b in branches for i in b['items']]
    assert len(ids)==len(set(ids)) and oldids<=set(ids)
    paths=[base.generate_overview_png(branches),*detail_sheets(branches,conflicts),full_svg(branches),base.generate_opml(center,branches,conflicts),summary(branches),base.generate_html(branches,conflicts),base.generate_readme(branches)]
    hp=OUT/'index.html';s=hp.read_text(encoding='utf-8').replace('198 микро-правил',f'{len(ids)} микро-правил')
    gallery='<h2>Полный графический комплект</h2><p>'+''.join(f'<a href="{p.name}">{p.stem}</a> · ' for p in paths if p.suffix in ('.png','.svg'))+'</p>'
    s=s.replace('<input id="search"',gallery+'<input id="search"');hp.write_text(s,encoding='utf-8')
    (OUT/'README.md').write_text(f'''# Psyz0r_bot — карта логики v9

19.10.2026: {len(branches)} веток, {len(ids)} правил; все {len(oldids)} ID v8 сохранены.

- [Открыть полный комплект с поиском](index.html).
- [Обзорная радиальная схема 3840×2160](Psyz0r_bot_mindmap_v9_overview_4K.png).
- [Сводный слайд 4096×2048](Psyz0r_bot_logic_summary_v9_4096x2048.png).
- [Полный масштабируемый реестр SVG](Psyz0r_bot_mindmap_v9_full.svg).
- [Редактируемое дерево OPML](Psyz0r_bot_mindmap_v9.opml).
- Листы 01_A … 15_O: полный текст каждого правила; 16_conflicts — решения и ограничения.
- [Машиночитаемый реестр](logic_registry_v9.json), manifest.json — SHA-256 и проверки границ.

PNG: 100 dpi. Цвет — тема, метка — документальный статус. LIVE означает свидетельство прошлого этапа, а не новый опрос сервера. SPEC/DATA не являются процентом готовности.

Источник: [MD v9](../MINDMAP_V9_CONTENT_RECONCILIATION_RU.md). Обновление: `python tools/update_logic_v9.py`, затем `python tools/generate_mindmap_v9.py`. v4 остаётся историческим снимком. Генератор проверяет сохранность ID, XML, полноту листов и переносит переполнение на следующий лист.

Актуальная локальная панель: ../../Аналитика разработки бота/index.html. Этот HTML сохраняет полный печатный реестр.
''',encoding='utf-8')
    data={'version':9,'date':'2026-10-19','source':base.SOURCE.name,'rule_count':len(ids),'retained_v8_ids':len(oldids),'new_ids':sorted(set(ids)-oldids),'status_note':'Documentary evidence; not a new live runtime audit or percentage completion','branches':branches,'questions':conflicts}
    jp=OUT/'logic_registry_v9.json';jp.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8');paths.append(jp)
    # Verify complete OPML and SVG membership and every raster page's bounds.
    tree=ET.parse(OUT/'Psyz0r_bot_mindmap_v9.opml')
    labels=[n.get('text','') for n in tree.iter('outline')]
    svg=(OUT/'Psyz0r_bot_mindmap_v9_full.svg').read_text(encoding='utf-8');ET.fromstring(svg)
    for ident in ids:
        assert sum(t.startswith(ident+' [') for t in labels)==1,ident
        assert ident+' ' in svg,ident
        assert sum(r['id']==ident for r in layout)==1,ident
    assert all(r['bounds'][3]<=2040 for r in layout)
    # LF сохраняет одинаковый SHA и после Git checkout на Linux.
    for path in paths:
        if path.suffix in ('.svg','.opml','.json','.html','.md'):
            path.write_text(path.read_text(encoding='utf-8'),encoding='utf-8',newline='\n')
    manifest={'version':9,'rules':len(ids),'old_ids_preserved':len(oldids),'layout_checks':layout,'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
    (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'Generated {len(paths)} artifacts; {len(ids)} rules; all {len(oldids)} old IDs retained; pagination/bounds/XML verified')

if __name__=='__main__':main()
