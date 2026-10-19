"""Render reproducible, offline research charts; no invented readiness score."""
import json, math, hashlib
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/mindmap_v7'
D=json.loads((ROOT/'docs/training/TACTICAL_PATTERNS_077.json').read_text(encoding='utf-8'))
# Рисуем в 2000×2667, затем сохраняем плакат 6000×8001 для удобного просмотра.
im=Image.new('RGB',(2000,2667),'#0b1424');p=ImageDraw.Draw(im)
def font(size,bold=False):
    return ImageFont.truetype('C:/Windows/Fonts/'+('segoeuib.ttf' if bold else 'segoeui.ttf'),size)
def text(x,y,s,size=22,color='#c5d2e5',bold=False):p.text((x,y),s,font=font(size,bold),fill=color)
def wrap(x,y,s,width=840,size=22,color='#c5d2e5'):
    words=s.split();line=''
    for word in words:
        candidate=(line+' '+word).strip()
        if p.textlength(candidate,font=font(size))>width:
            text(x,y,line,size,color);y+=size+10;line=word
        else:line=candidate
    text(x,y,line,size,color);return y+size+10
def panel(x,y,title,sub):
    p.rounded_rectangle((x,y,x+920,y+690),radius=20,fill='#142238',outline='#2e4562',width=2)
    text(x+28,y+22,title,28,'#f0f6ff',True)
    return wrap(x+28,y+69,sub,860,19,'#91a6c4')+15
def bar(x,y,label,value,maximum,color='#52c7e8'):
    text(x,y,label,21);p.rounded_rectangle((x,y+32,x+730,y+46),radius=7,fill='#25364e')
    p.rounded_rectangle((x,y+32,x+max(14,730*value/maximum),y+46),radius=7,fill=color)
    text(x+750,y+19,f'{value:g}',22,'#f0f6ff');return y+70

text(55,45,'PSYZ0R / TACTICAL LAB',52,'#f0f6ff',True)
text(58,119,'500 демок  /  офлайн-этап 0.7.7  /  играющий сервер 0.7.6',25,'#52c7e8')
text(58,163,'Наблюдения → проверяемые правила → локальные тесты → отдельный игровой прогон',22)
y=panel(50,230,'01 / Движение при стрельбе','Доля бокового движения в окнах до 100 мс после выстрела. Это не сырые клавиши.')
for weapon,label in [('rocket','RL'),('lightning','LG'),('railgun','RG')]:
    s=D['footwork'][weapon];y=bar(78,y,label,round(100*s['lateral_ms']/s['firing_ms'],1),100)
wrap(78,y+15,'LG: 76,6% наблюдаемого времени на земле. Движение и направление прицела считаются отдельно. Полёт не доказывает прыжок.',size=23)
y=panel(1030,230,'02 / Удержание перед выстрелом','250 мс: размах yaw ≤6° и pitch ≤4°. Перекрывающиеся LG-окна не независимы.')
for weapon,label in [('rocket','RL'),('lightning','LG'),('railgun','RG')]:
    s=D['preaim'][weapon];y=bar(1058,y,label,round(100*s['held']/s['windows'],1),100,'#ac94fa')
wrap(1058,y+15,'96,1% удержанных LG-окон сопровождались движением. Направление работы: плавный прицел плюс позиционные стрейфы.',size=23)
y=panel(50,950,'03 / Комбо-кандидаты','1 938 из 3 771 окон фрага: 51,4%. Выстрелы нескольких пушек не доказывают урон каждой той же цели.')
for label,n in D['combo_sequences'][:5]:y=bar(78,y,label,n,400,'#f5b454')
wrap(78,y+10,'Окно ≤5 с, очищается после фрага. 65–70% — цель подходящих решений, не искусственная квота.',size=21)
y=panel(1030,950,'04 / Цепочки ресурсов','Одно POV и одна жизнь. Частота не доказывает оптимальность дебюта или безопасность пути.')
for r in [r for r in D['macro_resource_triplets'] if 'health' not in r['sequence']][:4]:
    text(1058,y,' → '.join(r['sequence']),24,'#72dfb0',True)
    text(1058,y+36,f"{r['observations']} эпизодов / {r['demos']} демок / медиана {r['median_ms']/1000:.2f} с",21);y+=94
wrap(1058,y+5,'Режимы cycle / anchor / recover сохраняются. Реальные таймеры и цена маршрута важнее частоты шаблона.',size=21)
y=panel(50,1670,'05 / Позиции и взгляд: XY','80 кандидатов, не карта стен. Стрелки — направление взгляда из позиции игрока, а не координаты цели.')
anchors=D['aim_anchors'];xs=[a['position'][0] for a in anchors];ys=[a['position'][1] for a in anchors]
for a in anchors:
    px=115+750*(a['position'][0]-min(xs))/max(1,max(xs)-min(xs));py=y+40+350*(1-(a['position'][1]-min(ys))/max(1,max(ys)-min(ys)))
    angle=math.radians(a['yaw_deg']);end=(px+22*math.cos(angle),py-22*math.sin(angle))
    color={'lightning':'#52c7e8','railgun':'#ac94fa','rocket':'#f5b454'}.get(a['weapon'],'#72dfb0')
    p.line((px,py,*end),fill=color,width=2);p.ellipse((px-3,py-3,px+3,py+3),fill=color)
wrap(78,y+435,'У каждого кандидата есть demo ID / время / POV. Нужны BSP, LOS и проверка укрытия перед использованием.',size=21)
y=panel(1030,1670,'06 / Код и следующий тест','Новые модули LOCAL. Они ещё не управляют текущим ботом и не доказывают силу игры.')
for title,desc in [
    ('COMBO POLICY','Видимость + стек + недавний hit + патроны. Дальнее RG / средний LG / близкий RL / безопасная перчатка.'),
    ('ARRIVAL POLICY','Выход по проверенному p90 пути. HOLD только внутри объёма подбора. Под платформой красного ждать нельзя.'),
    ('ПРОВЕРКИ','118 Python / 17 CTest Debug. Далее: подтверждённые сенсоры и полный матч против Xaero на одном cfg.')]:
    text(1058,y,title,23,'#72dfb0',True);y=wrap(1058,y+38,desc,size=22)+22
text(58,2410,'Границы доказательств',30,'#f5b454',True)
wrap(58,2460,'Нет сырого WASD / mouse. Нет полного hit-attribution. 325 кандидатов 360° не доказывают намерение. Неподвижность перед подбором не доказывает stopwatch. Во время игр владельца runtime не заменяется.',1850,24)
text(58,2596,'Источник: TACTICAL_PATTERNS_077.json • Mind Map v7: 262 правила • 19.10.2026',21,'#91a6c4')
OUT.mkdir(parents=True,exist_ok=True)
im.resize((6000,8001),Image.Resampling.LANCZOS).save(OUT/'tactical_research_077.png',dpi=(100,100))
manifest_path=OUT/'manifest.json'
manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
manifest['files']['tactical_research_077.png']=hashlib.sha256((OUT/'tactical_research_077.png').read_bytes()).hexdigest()
manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
im.resize((1000,1334),Image.Resampling.LANCZOS).save(ROOT/'out/tactical-research/poster_preview.png')
print('Rendered tactical_research_077.png: 6000x8001')
