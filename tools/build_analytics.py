"""Build a file:// compatible dashboard from tracked evidence, never a live promise."""
import json,collections,datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'Аналитика разработки бота'
def load(name):return json.loads((ROOT/name).read_text(encoding='utf-8-sig'))
def main():
    current=9 if (ROOT/'docs/mindmap_v9/logic_registry_v9.json').exists() else 8 if (ROOT/'docs/mindmap_v8/logic_registry_v8.json').exists() else 7 if (ROOT/'docs/mindmap_v7/logic_registry_v7.json').exists() else 6
    registry=load(f'docs/mindmap_v{current}/logic_registry_v{current}.json')
    old=load(f'docs/mindmap_v{current-1}/logic_registry_v{current-1}.json')
    assert {x['id'] for b in old['branches'] for x in b['items']}<={x['id'] for b in registry['branches'] for x in b['items']}
    corpus=load('docs/training/ZTN_TOP500_MANIFEST_20261019.json');players=collections.Counter()
    for r in corpus['records']:
        for name in r.get('requested_players',[]):players[name]+=1
    lgfile='docs/training/LG_FOOTWORK_076.json' if (ROOT/'docs/training/LG_FOOTWORK_076.json').exists() else 'docs/training/LG_FOOTWORK_075.json'
    lg=load(lgfile)['players'];strafe=load('docs/training/STRAFE_ALL_074.json')
    fresh=load('docs/training/REANALYSIS_TOP500_076.json') if (ROOT/'docs/training/REANALYSIS_TOP500_076.json').exists() else {'parsed':0}
    modules=[
      ('Таймеры всех предметов','LOCAL','LIVE','Часы читаются из engine nextthink. Включённый таймер не доказывает своевременный приход.','adapter/native/psyz_item_timing.h'),
      ('Маршруты и антизастревание','LOCAL','PARTIAL','257 подходов исторического банка; новый фикс близкого застревания проверен локально. Полное отсутствие застреваний не подтверждено.','adapter/native/psyz_nav_recovery.h'),
      ('Дебюты / второй красный','LOCAL','PARTIAL','48 кандидатов и обязательный второй RA. Статические цели сверены; глобальная оптимальность и полный порядок под противодействием не подтверждены.','adapter/native/psyz_opening.h'),
      ('Макро: цикл / один основной / восстановление','LOCAL','PARTIAL','Три режима и веса ресурсов подключены в прототипе. Позиционное hide-and-seek и безопасные пути ухода не завершены.','adapter/native/psyz_macro.h'),
      ('Разгон и первые прыжки','LOCAL','PARTIAL','129 архивных квалифицированных стартов; нет подтверждения, что бот повторяет эталон скорости за 4 секунды.','docs/training/STRAFE_ALL_074.json'),
      ('Rocket jump / plasma climb','LOCAL','PARTIAL','RJ sample 0 подтверждён ранее; остальные экспериментальные. Plasma-кандидат не равен стабильному подбору RA в дуэли.','docs/training/BLOODRUN_RED_BOOSTS_3S.json'),
      ('LG: плавный прицел и ноги','LOCAL','PARTIAL','0.7.5 сглаживает прицел и команды штатного AI. Тесты ограничений добавлены; полная связь стрейфов с позицией ещё не реализована.','adapter/native/psyz_lg_style.h'),
      ('Додж ракеты после выстрела','LOCAL','SPEC','Есть расчёты геометрии/предикта. Реальный сенсор летящей ракеты и проверенный исполнитель не подтверждены.','src/combat_prediction.cpp'),
      ('Комбо и добивание','LOCAL','PARTIAL','Базовые правила оружия есть. 65–70% подходящих комбо и месть перчаткой в игре не подтверждены.','docs/OWNER_REQUIREMENTS_20261019_RU.md'),
      ('Чат и реакция на перчатку','LOCAL','PARTIAL','Приветствия, темы и нормализация пунктуации добавлены. Native damage/corpse sensors в старом minqlx отсутствуют.','server/minqlx-plugins/psyz_chat.py'),
      ('Forfeit / характер','LOCAL','PARTIAL','Подключена опция: один 15% выбор на матч, после 120с, разрыв ≥18. Guard 27961/один человек/подтверждённый бот/autofill=0. Частота в серии живых дуэлей не проверена.','server/minqlx-plugins/psyz_chat.py'),
      ('Локальная аналитика','LOCAL','SPEC','Полный реестр, фильтры, графики и источники. HTML работает без сервера; визуальная проверка браузером ограничена недоступным UI-инструментом.','Аналитика разработки бота/README.md'),
      ('Добивание / combo policy 0.7.7','LOCAL','SPEC','Новый контракт видимости, стека, давности hit, патронов и безопасного melee. Не подключён к текущему usercmd.','adapter/native/psyz_combo_policy.h'),
      ('Ранний приход / arrival policy 0.7.7','LOCAL','SPEC','Расписание по проверенному p90 пути; HOLD требует реального объёма подбора. Демо-кандидаты ETA ещё требуют AAS/physics проверки.','adapter/native/psyz_item_arrival.h')]
    smoke=load('docs/training/PREALPHA_076_SMOKE.json') if (ROOT/'docs/training/PREALPHA_076_SMOKE.json').exists() else None
    owner=load('docs/training/OWNER_MATCHES_076.json')
    restored=load('демки для обучения/RESTORED_DEMOS_20261019/manifest.json')['unique_demos']
    fresh_strafe=load('docs/training/STRAFE_TOP500_076.json')
    tactical=load('docs/training/TACTICAL_PATTERNS_077.json') if (ROOT/'docs/training/TACTICAL_PATTERNS_077.json').exists() else None
    data={'release':'0.7.6 live / 0.7.7 offline','generated':'2026-10-19 · локальный снимок','registry':registry,'tactical':tactical,
      'metrics':[{'label':'ПРАВИЛА ЛОГИКИ','value':registry['rule_count'],'note':'15 веток · прежние ID сохранены'}, {'label':'ВОССТАНОВЛЕННЫЕ ДЕМКИ','value':restored+900,'note':f'{restored} локальных + 900 из архива'}, {'label':'ПОВТОРНЫЙ РАЗБОР ТОПОВ','value':f"{fresh['parsed']} / 500",'note':'Оригиналы сверены по SHA-256'}, {'label':'ЛОКАЛЬНЫЕ ПРОВЕРКИ','value':'17 + 118' if tactical else '15 + 111','note':'Следующий офлайн-этап · сервер остаётся 0.7.6'}],
      'modules':[dict(name=a,code=b,game=c,evidence=d,source=e) for a,b,c,d,e in modules],
      'players':sorted(players.items(),key=lambda x:-x[1]),
      'ownerComparison':owner['bloodrun_comparison'],
      'longMatch':'Самый длинный найденный интервал: '+owner['longest_recorded_intervals'][0]['demo']+' · '+str(round(owner['longest_recorded_intervals'][0]['observed_interval_ms']/60000,2))+' мин. Поле overtimeCount=0 противоречит длине; число овертаймов не утверждается.',
      'jumpStats':[{'label':'Квалифицированные старты (свежие top-500)','value':fresh_strafe['sample_count']},{'label':'Полное окно 4 секунды','value':sum(s['observed_horizon_ms']>=3900 for s in fresh_strafe['samples'])},{'label':'Архивное объединение 925 выгрузок','value':strafe['sample_count']},{'label':'Допуск владельца','value':'±10–15 UPS'},{'label':'Клавиши и мышь','value':'не подтверждены'}],
      'lg':[dict(name=k,frames=v['frames'],yaw=v['yaw_deg_s']['p50'],p95=v['yaw_deg_s']['p95'],strafe=v['lateral_reversal_ms']['p50']) for k,v in lg.items()],
      'modes':[{'tag':'CONTROL / CYCLE','name':'Связать карту в цикл','text':'Сильный стек и подходящие пушки. Основные и вторичные ресурсы в связке; приход заранее, выход после подбора.','status':'PARTIAL'},{'tag':'ANCHOR / ONE MAJOR','name':'Играть от одного основного','text':'Mega или RA как опора. Не превращать выбор в бесконечное ожидание; учитывать второй ресурс и безопасные штрафы.','status':'PARTIAL'},{'tag':'RECOVER / HIDE','name':'Восстановиться от жёлтых','text':'Избегать невыгодной прямой драки. YA, аптечки, ammo и оружие; тихий маршрут, штраф и выход. Полный исполнитель укрытий ещё нужен.','status':'PARTIAL'}],
      'tests':[{'label':'C++ / ЛОКАЛЬНЫЙ ЭТАП','value':'17 / 17' if tactical else '15 / 15','note':'Включает новые combo/arrival политики. Сервер0.7.6 не заменён этим кодом.'},{'label':'PYTHON / ЛОКАЛЬНЫЙ ЭТАП','value':'118 / 118' if tactical else '111 / 111','note':'Парсеры, политики и чат. Native damage hook этим не появляется.'},{'label':'BOT VS XAERO / 0.7.6','value':'65 сек','note':f"{smoke['pickups']} подборов / RA {smoke['red_pickups']} / Mega {smoke['mega_pickups']} / {smoke['opening_pickups']} шага дебюта / {smoke['nav_recoveries']} восстановления. LG не стрелял. Это smoke, не полный матч." if smoke else 'Ожидается проверка'}],
      'questions':registry['questions']+['Прицел в пикселях нельзя перевести в физический угол без FOV/разрешения; настройки задаются в градусах и времени реакции.','Не извлекать «сырые WASD» из одной скорости. Возможны разные управляющие команды при сходной траектории.','Сравнивать победы, подборы, damage и застревания серией полных матчей; один удачный RJ не подтверждает всю навигацию.'],
      'backlog':[{'name':'Подборы и застревания','test':'Полный Duel: близкий доступный ресурс должен быть взят либо записана причина отказа; без AFK под платформой.','status':'LOCAL'},{'name':'Дебют → второй RA → Mega','test':'Проверить каждый старт и порядок 2–3 предметов против Xaero; штраф вместо самоубийственного входа.','status':'PARTIAL'},{'name':'Стартовый разгон по сольной демке и топам','test':'Измерить 2с и 4с, первые 2–3 прыжка, yaw и потери скорости на поворотах.','status':'DATA'},{'name':'LG и dodge по наблюдаемым ракетам','test':'Плавный прицел без тряски, безопасные наземные смены направления; не выдумывать будущий выстрел.','status':'PARTIAL'},{'name':'Комбо / gauntlet revenge / трупы','test':'Сначала подтвердить сенсоры и damage той же цели; затем выполнять безопасное добивание.','status':'SPEC'},{'name':'Реальный forfeit','test':'Один выбор на матч, сильное отставание, корректный выход, отсутствие немедленного возврата через autofill.','status':'SPEC'}]}
    if (ROOT/'docs/training/PREALPHA_078_DEPLOYMENT.json').exists():
        data['release']='0.7.8 / test 27961'
        data['winnerAccuracy']=load('docs/training/WINNER_ACCURACY_078.json')
        data['freshFeedback']=load('docs/training/FRESH_FEEDBACK_078.json')['records']
        data['ownerSpam']=load('docs/training/OWNER_SPAM_CIRCLE_078.json')
        data['unopposed']=load('docs/training/UNOPPOSED_078.json')
        data['deployment']=load('docs/training/PREALPHA_078_DEPLOYMENT.json')
        smoke078=ROOT/'docs/training/PREALPHA_078_SMOKE.json'
        data['smoke078']=load(str(smoke078.relative_to(ROOT))) if smoke078.exists() else None
        data['metrics'][-1]={'label':'ЛОКАЛЬНЫЕ ПРОВЕРКИ','value':'17 + 121','note':'Windows + 5 Linux-проверок · 0.7.8 установлена'}
        data['tests'][0]['note']='Новые проверки не блокируют штатное движение при защитном MG-огне; бот определяется по имени/флагу.'
        data['tests'][1]['value']='121 / 121'
        data['tests'].append({'label':'LINUX / 0.7.8','value':'5 / 5','note':'Native context, nav, LG, combo и arrival; не доказательство силы полной дуэли.'})
        for module in data['modules']:
            if 'Маршруты' in module['name']:module['evidence']='0.7.8: независимый motion-watch и 3с возврат stock AAS; неподвижность не скрывается сменой цели. Полное отсутствие застреваний не доказано.'
            if 'Чат и' in module['name']:module['evidence']='0.7.8: Steam ID/слот вместо object identity; нуб/nub/noob; повторные реплики через 4с и контекст 45с. Native corpse/damage сенсора ещё нет.'
        data['metrics'][1]['note']+='; включает 2 свежие записи'
    if (ROOT/'docs/training/RESERVE200_RESEARCH_079.json').exists():
        r=load('docs/training/RESERVE200_RESEARCH_079.json')
        data['research079']={k:v for k,v in r.items() if k not in ('accuracy_reserve','accuracy_combined','opening_examples')}
        data['research079']['accuracy']={c:r['accuracy_combined'][c]['table'] for c in ['winner','damage_leader']}
        data['research079']['histograms']={}
        for wid in [2,3,5,6,7,8]:
            bins=[0]*10
            for row in r['accuracy_combined']['winner']['observations']:
                if row['weapon_id']==wid:bins[min(9,int(row['accuracy']//10))]+=1
            data['research079']['histograms'][str(wid)]=bins
        data['release']='Пре-альфа 0.7.9 / test 27961'
        data['metrics'][1]={'label':'СТЕК ДЕМОК','value':restored+900,'note':'Уникальные оригиналы в локальном проекте'}
        data['metrics'][2]={'label':'РАЗОБРАНО','value':f"{500+r['parsed']} / 700",'note':'500 top-player + 200 дополнительных; доступность scoreboard отличается'}
        data['metrics'].insert(3,{'label':'ОХВАТ СТЕКА','value':f"{500+r['parsed']} / {restored+900}",'note':'Без повторного учёта SHA-256'})
        data['metrics'][-1]={'label':'ПРОВЕРКИ 0.7.9','value':'17 + 138','note':'CTest + Python; отдельно 5 Linux-групп'}
        data['tests'][0]['note']='0.7.9: native context, stock-only motion watch, bounded wait, LG/combo/arrival.'
        data['tests'][1]['value']='138 / 138'
        data['tests'][1]['note']='Добавлены проверки отдельных winner/damage когорт и отсутствующих наблюдений.'
        for module in data['modules']:
            if 'Маршруты' in module['name']:module['evidence']='0.7.9: motion-watch учитывает stock-команды при target=-1; ожидание одинаково ограничено у обоих сторожей. Выход из каждого угла и сила контроля ещё не доказаны.'
        if (ROOT/'docs/training/PREALPHA_079_DEPLOYMENT.json').exists():data['deployment']=load('docs/training/PREALPHA_079_DEPLOYMENT.json')
        if (ROOT/'docs/training/PREALPHA_079_TRIAL.json').exists():data['trial079']=load('docs/training/PREALPHA_079_TRIAL.json')
        data['versionHistory']=[
            {'version':'0.7.6','stage':'тестовая','rules':load('docs/mindmap_v6/logic_registry_v6.json')['rule_count'],'demos':500,'cpp':17,'note':'Разгон и ранние прогоны; карта v6. Исторические статусы не подтверждают силу.'},
            {'version':'0.7.7','stage':'офлайн','rules':load('docs/mindmap_v7/logic_registry_v7.json')['rule_count'],'demos':500,'cpp':17,'note':'Комбо/arrival политики проверялись локально. Отдельного live-результата 0.7.7 нет.'},
            {'version':'0.7.8','stage':'тестовая','rules':load('docs/mindmap_v8/logic_registry_v8.json')['rule_count'],'demos':500,'cpp':17,'note':'Две человеческие демки 1:29 и 3:13. Короткий smoke не доказывает силу.'},
            {'version':'0.7.9','stage':'пре-альфа','rules':registry['rule_count'],'demos':700,'cpp':17,'note':'Ещё 200 оригиналов; независимый stock motion-watch и единое короткое ожидание.'}]
    if (ROOT/'docs/training/MATCH_LEDGER.json').exists():
        data['duelLedger']=load('docs/training/MATCH_LEDGER.json')
        data['ledgerUrl']='https://raw.githubusercontent.com/malosmysla-lang/Project_Psyz0r_bot/main/docs/training/MATCH_LEDGER.json'
    if (ROOT/'docs/training/PREALPHA_080_DEPLOYMENT.json').exists():
        data['release']='Пре-альфа 0.8.0 / test 27961'
        data['deployment']=load('docs/training/PREALPHA_080_DEPLOYMENT.json')
        data['trial080']=load('docs/training/PREALPHA_080_TRIAL.json')
        data['metrics'][-1]={'label':'ПРОВЕРКИ 0.8.0','value':'17 + 143','note':'CTest + Python; отдельно 5 Linux-групп'}
        data['tests'][1]['value']='143 / 143'
        data['versionHistory']=data['versionHistory'][-3:]+[{'version':'0.8.0','stage':'пре-альфа','rules':registry['rule_count'],'demos':700,'cpp':17,'note':'Наблюдатель прямого LG/RG-урона и combo-политика подключены. В коротком smoke переключений не было; игровая эффективность не доказана.'}]
        data['tests'].append({'label':'LIVE / 0.8.0','value':'0 combo switches','note':'Ограниченный smoke без fatal; один combat brake. Это не полный матч и не доказательство силы.'})
    (OUT/'data.js').write_text('window.PSYZ_ANALYTICS = '+json.dumps(data,ensure_ascii=False)+';\n',encoding='utf-8')
    (OUT/'data.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Dashboard:',registry['rule_count'],'rules;',len(modules),'modules; sources linked')
if __name__=='__main__':main()
