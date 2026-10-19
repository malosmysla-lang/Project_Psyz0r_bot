"""Versioned reconciliation of two new duels, live fixes and winner accuracy targets."""
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ADDITIONS={
 'A':[('SPEC','Новая серия до альфы должна сохранять силу штатного Xaero 5. Общие attack/aim/view нельзя незаметно ослаблять вместе с human accuracy; профиль и дополнительные ошибки документируются отдельно.')],
 'D':[('PARTIAL','0.7.8 добавляет независимый от смены целей сторож реального перемещения на каждом think. Остановка в радиусе 32u от 1.8с запускает ограниченный 3с возврат движения штатному AAS; цель и плохой demo-route получают cooldown. Вечный огонь имеет конечный бюджет паузы.'),('PARTIAL','Управляемый бот определяется по bot flag и имени, а не по слоту 0. Человек в нулевом слоте не получает надстройки и его подборы не записываются как подборы Psyz0r.')],
 'F':[('DATA','Из 500 демок найдены 478 матчей с однозначно сопоставленным победителем. Среднее accuracy считается только по наблюдаемым положительным shots у строки победителя; pooled hits/shots отдельно. Нет данных — не нулевая точность.'),('PARTIAL','0.7.8 применяет среднее accuracy победителей и диапазон ±7.5 процентного пункта для MG/SG/RL/LG/RG/plasma как цели калибровки. Ошибка наведения отдельная для каждой пушки; урон/регистрацию попаданий не менять. GL исключён.')],
 'G':[('PARTIAL','Недобор двух пушек Trinity повышает ресурсные приоритеты, но не обнуляет forwardmove во время защитной стрельбы с MG. Нельзя создавать неподвижность вместо осмысленного восстановления.')],
 'H':[('PARTIAL','Доступная Mega/RA может прервать удерживаемую вторичную цель без требования двух пушек. Стек соперника сам по себе не доказывает опасность на точке. При HP<40 RA не получает принудительный приоритет; недоступные будущие предметы по-прежнему требуют боевого набора.')],
 'L':[('PARTIAL','0.7.8 понимает нуб/nub/noob и русские/английские приветствия/темы. Отправитель сравнивается по Steam ID и слоту, не Python identity. Ответы на одну тему повторяются после 4с паузы с разными репликами; короткое продолжение разговора хранится 45с. Метки #bot и команды не обсуждаются.')],
 'N':[('DATA','Две свежие 10-минутные ZTN-дуэли 19.10 дали Psyz0r 1:29 и 3:13; в каждой RA=1, Mega=4. Статистика UDT и подборы правильной эпохи serverTime совпали. Исходники сохранены в проекте и видимой папке demos с SHA-256.'),('SPEC','Сольный круг владельца остаётся источником циклов, GL/plasma spam и стартов. Сырые кнопки и намерение не объявлять известными; эпизод спама требует позиции/времени/оружия и геометрической проверки.')],
 'O':[('PARTIAL','0.7.8 собрана с сохранением основного 27960; четыре изменяемых live-файла копируются перед заменой. Развёртывание только при отсутствии людей; новая короткая проба не считается полной победой или альфой.')]
}
def main():
    text=(ROOT/'docs/MINDMAP_V7_CONTENT_RECONCILIATION_RU.md').read_text(encoding='utf-8').replace('Mind Map v7','Mind Map v8')
    # Предыдущие временные запреты сохраняются как история своего этапа.
    text='> Актуально для 0.7.8: см. PREALPHA_0_7_8_RU.md. Правила о текущем тесте 0.7.6 ниже относятся к офлайн-этапу 0.7.7; подключение 0.7.8 имеет отдельный журнал.\n\n'+text
    text=text.replace('yaw-span≤6° и pitch-span≤4°','максимальное отклонение от угла выстрела yaw≤6° и pitch≤4°')
    for letter,rows in ADDITIONS.items():
        match=re.search(r'^## '+letter+r'\. .*?(?=^## |\Z)',text,re.M|re.S);block=match.group()
        last=max(int(n) for n in re.findall(r'`'+letter+r'(\d+) ',block))
        extra='\n'.join(f'- `{letter}{last+i:02d} {status}` {line}' for i,(status,line) in enumerate(rows,1))
        text=text[:match.start()]+block.rstrip()+'\n'+extra+'\n\n'+text[match.end():]
    text+='\n## Источники 0.7.8\n\n- PREALPHA_0_7_8_RU.md; training/FRESH_FEEDBACK_078.json; training/WINNER_ACCURACY_078.json; training/PREALPHA_078_DEPLOYMENT.json.\n'
    (ROOT/'docs/MINDMAP_V8_CONTENT_RECONCILIATION_RU.md').write_text(text,encoding='utf-8')
    generator=ROOT/'tools/generate_mindmap_v8.py'
    if not generator.exists():
        s=(ROOT/'tools/generate_mindmap_v7.py').read_text(encoding='utf-8').replace('v7','v8').replace('V7','V8').replace("'version':7","'version':8")
        s=s.replace("_,oldbranches,_=__import__('generate_mindmap_v4').parse()","oldbranches=json.loads((ROOT/'docs/mindmap_v7/logic_registry_v7.json').read_text(encoding='utf-8'))['branches']")
        generator.write_text(s,encoding='utf-8')
    print('Prepared v8; all v7 IDs retained')
if __name__=='__main__':main()
