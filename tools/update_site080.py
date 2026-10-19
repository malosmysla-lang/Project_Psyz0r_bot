from pathlib import Path
import shutil

r=Path(__file__).resolve().parents[1]
s=r/'Аналитика разработки бота'
shutil.copy2(r'C:\Users\user\.codex\generated_images\01a11f1b-3ebc-7912-a758-4f7286e63bc1\exec-e405191f-602b-47a5-a205-cca5062c3c99.png',s/'assets/quake-weapons-atlas.png')
p=s/'bot-mascot.css'
p.write_text(p.read_text(encoding='utf-8')+'''
/* 0.8.0: тонкие веки перекрывают шов при полном смыкании. */
.eye-shutter i{height:54%;background:linear-gradient(155deg,#71848d,#30434f 48%,#18252e);box-shadow:inset 0 1px 1px #d5edf044,inset 0 -1px 2px #07131b88}
.eye-shutter .upper-lid{border-radius:45% 45% 0 0;border-bottom:1px solid #6f8e98}
.eye-shutter .lower-lid{border-radius:0 0 45% 45%;border-top:1px solid #6f8e98;background:linear-gradient(155deg,#607985,#2a414d 50%,#172731)}
.eye-shutter i::after{height:9%;opacity:.35}
''',encoding='utf-8')
p=s/'index.html';t=p.read_text(encoding='utf-8');t=t.replace('</body>','<script src="chart-interactions.js"></script></body>');p.write_text(t,encoding='utf-8')
for name in ['package_mobile_analytics.py','prepare_hosted_analytics.py']:
    p=r/'tools'/name;t=p.read_text(encoding='utf-8').replace('0_7_9','0_8_0').replace('0.7.9','0.8.0').replace('около 5 МБ','автономная версия');p.write_text(t,encoding='utf-8')
p=r/'tools/build_analytics.py';t=p.read_text(encoding='utf-8');pos=t.index("    (OUT/'data.js').write_text")
t=t[:pos]+'''    if (ROOT/'docs/training/PREALPHA_080_DEPLOYMENT.json').exists():
        data['release']='Пре-альфа 0.8.0 / test 27961'
        data['deployment']=load('docs/training/PREALPHA_080_DEPLOYMENT.json')
        data['trial080']=load('docs/training/PREALPHA_080_TRIAL.json')
        data['metrics'][-1]={'label':'ПРОВЕРКИ 0.8.0','value':'17 + 143','note':'CTest + Python; отдельно 5 Linux-групп'}
        data['tests'][1]['value']='143 / 143'
        data['versionHistory']=data['versionHistory'][-3:]+[{'version':'0.8.0','stage':'пре-альфа','rules':registry['rule_count'],'demos':700,'cpp':17,'note':'Наблюдатель прямого LG/RG-урона и combo-политика подключены. В коротком smoke переключений не было; игровая эффективность не доказана.'}]
        data['tests'].append({'label':'LIVE / 0.8.0','value':'0 combo switches','note':'Ограниченный smoke без fatal; один combat brake. Это не полный матч и не доказательство силы.'})
'''+t[pos:];p.write_text(t,encoding='utf-8')
