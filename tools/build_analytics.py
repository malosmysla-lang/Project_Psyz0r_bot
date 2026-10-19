"""Build a file:// compatible dashboard from tracked evidence, never a live promise."""
import json,collections,datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'Аналитика разработки бота'
def load(name):return json.loads((ROOT/name).read_text(encoding='utf-8-sig'))
def main():
    registry=load('docs/mindmap_v6/logic_registry_v6.json')
    old=load('docs/mindmap_v5/logic_registry_v5.json')
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
      ('Локальная аналитика','LOCAL','SPEC','252 правила, фильтры, графики и источники. HTML работает без сервера; визуальная проверка браузером ограничена недоступным UI-инструментом.','Аналитика разработки бота/README.md')]
    smoke=load('docs/training/PREALPHA_076_SMOKE.json') if (ROOT/'docs/training/PREALPHA_076_SMOKE.json').exists() else None
    owner=load('docs/training/OWNER_MATCHES_076.json')
    restored=load('демки для обучения/RESTORED_DEMOS_20261019/manifest.json')['unique_demos']
    fresh_strafe=load('docs/training/STRAFE_TOP500_076.json')
    data={'release':'0.7.6 / тестовый сервер','generated':'2026-10-19 · локальный снимок','registry':registry,
      'metrics':[{'label':'ПРАВИЛА ЛОГИКИ','value':registry['rule_count'],'note':'15 веток · прежние ID сохранены'}, {'label':'ВОССТАНОВЛЕННЫЕ ДЕМКИ','value':restored+900,'note':f'{restored} локальных + 900 из архива'}, {'label':'ПОВТОРНЫЙ РАЗБОР ТОПОВ','value':f"{fresh['parsed']} / 500",'note':'Оригиналы сверены по SHA-256'}, {'label':'ЛОКАЛЬНЫЕ ПРОВЕРКИ','value':'15 + 111','note':'C++ группы и Python тесты · не игровой рейтинг'}],
      'modules':[dict(name=a,code=b,game=c,evidence=d,source=e) for a,b,c,d,e in modules],
      'players':sorted(players.items(),key=lambda x:-x[1]),
      'ownerComparison':owner['bloodrun_comparison'],
      'longMatch':'Самый длинный найденный интервал: '+owner['longest_recorded_intervals'][0]['demo']+' · '+str(round(owner['longest_recorded_intervals'][0]['observed_interval_ms']/60000,2))+' мин. Поле overtimeCount=0 противоречит длине; число овертаймов не утверждается.',
      'jumpStats':[{'label':'Квалифицированные старты (свежие top-500)','value':fresh_strafe['sample_count']},{'label':'Полное окно 4 секунды','value':sum(s['observed_horizon_ms']>=3900 for s in fresh_strafe['samples'])},{'label':'Архивное объединение 925 выгрузок','value':strafe['sample_count']},{'label':'Допуск владельца','value':'±10–15 UPS'},{'label':'Клавиши и мышь','value':'не подтверждены'}],
      'lg':[dict(name=k,frames=v['frames'],yaw=v['yaw_deg_s']['p50'],p95=v['yaw_deg_s']['p95'],strafe=v['lateral_reversal_ms']['p50']) for k,v in lg.items()],
      'modes':[{'tag':'CONTROL / CYCLE','name':'Связать карту в цикл','text':'Сильный стек и подходящие пушки. Основные и вторичные ресурсы в связке; приход заранее, выход после подбора.','status':'PARTIAL'},{'tag':'ANCHOR / ONE MAJOR','name':'Играть от одного основного','text':'Mega или RA как опора. Не превращать выбор в бесконечное ожидание; учитывать второй ресурс и безопасные штрафы.','status':'PARTIAL'},{'tag':'RECOVER / HIDE','name':'Восстановиться от жёлтых','text':'Избегать невыгодной прямой драки. YA, аптечки, ammo и оружие; тихий маршрут, штраф и выход. Полный исполнитель укрытий ещё нужен.','status':'PARTIAL'}],
      'tests':[{'label':'C++ / DEBUG','value':'15 / 15','note':'Сценарии ядра, watchdog и LG. Не измеряют силу в дуэли.'},{'label':'PYTHON','value':'111 / 111','note':'Парсеры, политики и чат. Native damage hook этим не появляется.'},{'label':'BOT VS XAERO / 0.7.6','value':'65 сек','note':f"{smoke['pickups']} подборов / RA {smoke['red_pickups']} / Mega {smoke['mega_pickups']} / {smoke['opening_pickups']} шага дебюта / {smoke['nav_recoveries']} восстановления. LG не стрелял. Это smoke, не полный матч." if smoke else 'Ожидается проверка'}],
      'questions':registry['questions']+['Прицел в пикселях нельзя перевести в физический угол без FOV/разрешения; настройки задаются в градусах и времени реакции.','Не извлекать «сырые WASD» из одной скорости. Возможны разные управляющие команды при сходной траектории.','Сравнивать победы, подборы, damage и застревания серией полных матчей; один удачный RJ не подтверждает всю навигацию.'],
      'backlog':[{'name':'Подборы и застревания','test':'Полный Duel: близкий доступный ресурс должен быть взят либо записана причина отказа; без AFK под платформой.','status':'LOCAL'},{'name':'Дебют → второй RA → Mega','test':'Проверить каждый старт и порядок 2–3 предметов против Xaero; штраф вместо самоубийственного входа.','status':'PARTIAL'},{'name':'Стартовый разгон по сольной демке и топам','test':'Измерить 2с и 4с, первые 2–3 прыжка, yaw и потери скорости на поворотах.','status':'DATA'},{'name':'LG и dodge по наблюдаемым ракетам','test':'Плавный прицел без тряски, безопасные наземные смены направления; не выдумывать будущий выстрел.','status':'PARTIAL'},{'name':'Комбо / gauntlet revenge / трупы','test':'Сначала подтвердить сенсоры и damage той же цели; затем выполнять безопасное добивание.','status':'SPEC'},{'name':'Реальный forfeit','test':'Один выбор на матч, сильное отставание, корректный выход, отсутствие немедленного возврата через autofill.','status':'SPEC'}]}
    (OUT/'data.js').write_text('window.PSYZ_ANALYTICS = '+json.dumps(data,ensure_ascii=False)+';\n',encoding='utf-8')
    (OUT/'data.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Dashboard:',registry['rule_count'],'rules;',len(modules),'modules; sources linked')
if __name__=='__main__':main()
