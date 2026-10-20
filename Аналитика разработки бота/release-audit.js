/* Current executable state is distinct from historical feature specifications. */
(() => {
 const data=window.PSYZ_ANALYTICS,root=document.querySelector('#releaseAudit');
 if(!root||!data.freshFeedback082)return;
 const escape=value=>String(value??'—').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const rows=data.freshFeedback082.records.slice().reverse().map(record=>{
   const bot=record.players.find(p=>p.cleanName==='Psyz0r_bot');
   const human=record.players.find(p=>p.cleanName==='nekitz0r');
   return `<tr><td>${escape(record.demo)}</td><td>${escape(bot?.score)}:${escape(human?.score)}</td><td>${escape(bot?.railgunAccuracy)}%</td><td>${escape(bot?.redArmorPickups)} / ${escape(bot?.megaHealthPickups)}</td><td>${record.resource_concession?'Ресурсы уступались владельцем':'Условия не размечены'}</td></tr>`;
 }).join('');
 root.innerHTML=`<div class="section-label">20.10.2026 / АУДИТ 0.8.6</div><h2>Что работает сейчас</h2><article class="card panel"><h3>Пре-альфа 0.8.6 / тест 27961</h3><p>Исправлен конфликт профилей: отдельный файл перекрывал пакет и оставлял старые веса Psyz. Журнал движка после исправления подтвердил загрузку <code>xaero_w.c</code> для Psyz0r. Урон за попадание не менялся.</p><p>Чат понимает дополнительные RU/EN/транслит-реплики, «как дела», «найди меня» и поток сообщений. Реакцию в живой игре ещё нужно подтвердить.</p><p>Forfeit выбирается один раз за матч с вероятностью 35%, затем требует отставание 15+ и отсутствие прогресса. Это настройка вероятности, а не число уже состоявшихся выходов.</p><p>Закрытый стенд Xaero ↔ Psy ↔ Psy на 27962 собирает события матчей. Он измеряет базовый профиль; автоматическое обучение и комбо-исполнение пока не заявлены готовыми.</p></article><h3>Все восемь локальных демо против Psyz0r</h3><div class="tablewrap"><table class="table"><thead><tr><th>Запись</th><th>Бот : игрок</th><th>Railgun бота</th><th>RA / Mega бота</th><th>Условия</th></tr></thead><tbody>${rows}</tbody></table></div><p class="caption">Непрерывные кнопки и мышь бота в POV владельца не наблюдаются. Статистика scoreboard не означает автоматическое обучение.</p>`;
})();
