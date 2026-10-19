/* Match evidence, not an automatic-training claim. Offline snapshot + online JSON. */
(function(){
 'use strict';
 if(!window.PSYZ_ANALYTICS.duelLedger)return;
 const data=window.PSYZ_ANALYTICS,q=s=>document.querySelector(s),safe=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 let ledger=data.duelLedger,selectedId=null;
 const gunNames={machinegun:'MG',shotgun:'SG',rocket:'RL',lightning:'LG',railgun:'RG',plasma:'PG',grenade:'GL'};
 const finite=x=>typeof x==='number'&&Number.isFinite(x),value=x=>finite(x)?String(x):'—';
 function select(actor,type){return ledger.matches.filter(m=>(!actor||(m.actor||'Psyz0r')===actor)&&(!type||m.opponent_type===type));}
 function comparable(rows){
  const groups={};
  for(const r of rows){
   if(r.aborted||r.version==='unknown'||!r.version||!finite(r.duration_seconds)||r.duration_seconds<300)continue;
   const key=[r.version,r.native_sha256||r.tested_native_sha256||'unknown-build',r.map,r.opponent_type,r.opponent?.name].join('|');(groups[key]??=[]).push(r);
  }
  const best=Object.values(groups).sort((a,b)=>b.length-a.length)[0]||[];
  return {count:best.length,minimum:10,status:best.length>=10?'descriptive_comparison_possible':'insufficient_comparable_matches',automatic_learning:false};
 }
 function accuracy(p,key){const w=p?.weapons?.[key];return w&&finite(w.accuracy_pct)&&w.shots>0?`${w.accuracy_pct}%`:'—';}
 function pie(target,a,b,labels){
  const total=a+b;
  q(target).innerHTML=total?`<div class="donut" style="--share:${100*a/total}%" role="img" aria-label="${safe(labels[0])}: ${a}; ${safe(labels[1])}: ${b}"><span>${total}</span></div><div class="donut-legend"><span><i></i>${safe(labels[0])}: ${a}</span><span><i></i>${safe(labels[1])}: ${b}</span></div>`:'<p class="caption">Нет доступных наблюдений</p>';
 }
 function render(){
  const rows=select(q('#duelActor').value||'Psyz0r',q('#duelType').value||'');
  const selected=rows.find(r=>r.id===selectedId)||rows[rows.length-1];selectedId=selected?.id;
  q('#duelCount').textContent=`${rows.length} матчей в фильтре / ${ledger.matches.length} записей всего. Версия «неизвестна» не восстанавливается по дате демки.`;
  q('#duelRows').innerHTML=[...rows].reverse().map((r,i)=>`<tr class="${r.id===selectedId?'selected-duel':''}" data-duel="${safe(r.id)}"><td><button type="button" class="duel-select" data-duel-id="${safe(r.id)}">${safe(r.date_label||(r.ended_at?new Date(r.ended_at).toLocaleString('ru-RU',{timeZone:'Europe/Moscow'}):'архив'))}</button><small>${safe(r.source)}${r.aborted?' · прерван':''}</small></td><td>${safe(r.version==='unknown'?'неизвестна':r.version)}</td><td>${safe(r.opponent?.name)}<small>${r.opponent_type==='bot'?'бот':'человек'} · ${safe(r.map)}</small></td><td>${value(r.bot?.score)}:${value(r.opponent?.score)}</td><td>${value(r.bot?.damage_given)}</td><td>${value(r.bot?.pickups?.red)} / ${value(r.bot?.pickups?.mega)} / ${value(r.bot?.pickups?.yellow)}</td>${Object.keys(gunNames).filter(k=>k!=='grenade').map(k=>`<td>${accuracy(r.bot,k)}</td>`).join('')}</tr>`).join('');
  for(const b of q('#duelRows').querySelectorAll?.('[data-duel-id]')||[])b.addEventListener('click',()=>{selectedId=b.dataset.duelId;render();});
  const rated=rows.filter(r=>finite(r.bot?.score)&&finite(r.opponent?.score)&&!r.aborted);
  const wins=rated.filter(r=>r.bot.score>r.opponent.score).length,losses=rated.filter(r=>r.bot.score<r.opponent.score).length;
  pie('#duelResultsPie',wins,losses,['Победы','Поражения']);
  const points=rows.filter(r=>finite(r.bot?.score)&&finite(r.opponent?.score)&&finite(r.duration_seconds)&&r.duration_seconds>0&&!r.aborted).slice(-30);
  const vals=points.map(r=>(r.bot.score-r.opponent.score)*600/r.duration_seconds),max=Math.max(1,...vals.map(Math.abs));
  q('#duelTrend').innerHTML=points.length?`<svg class="duel-trend" viewBox="0 0 600 220" role="img" aria-label="Разница счёта на 10 минут по последним ${points.length} матчам"><path d="M40 20V190H580M40 105H580" stroke="#41516b" fill="none"/><polyline pathLength="1" points="${vals.map((v,i)=>`${40+i*540/Math.max(1,vals.length-1)},${105-v/max*80}`).join(' ')}" stroke="#53e5ed" stroke-width="2.5" fill="none"/>${vals.map((v,i)=>`<circle cx="${40+i*540/Math.max(1,vals.length-1)}" cy="${105-v/max*80}" r="4" fill="#b18aff"><title>${safe(points[i].opponent?.name)}: ${v.toFixed(1)} фрагов/10мин · ${safe(points[i].version)}</title></circle>`).join('')}<text x="4" y="25" fill="#a8b7cc" font-size="11">+${max.toFixed(0)}</text><text x="13" y="110" fill="#a8b7cc" font-size="11">0</text><text x="4" y="190" fill="#a8b7cc" font-size="11">−${max.toFixed(0)}</text></svg>`:'<p class="caption">Нужны счёт и длительность матча</p>';
  const c=comparable(rows);
  q('#learningStatus').textContent=`Автообучение модели не подключено. Сейчас — ручные версии правил и сбор результатов. Крупнейшая сопоставимая группа: ${c.count}/${c.minimum} матчей (одна версия, карта и соперник; ≥5 минут). ${c.count>=c.minimum?'Можно сравнивать описательные показатели; это ещё не доказательство обучения.':'Данных для оценки прогресса пока недостаточно.'}`;
  q('#duelSelected').textContent=selected?`Выбран: ${selected.bot.name} — ${selected.opponent.name} · ${value(selected.bot.score)}:${value(selected.opponent.score)}`:'Выбери матч';
  let direct=0,projectile=0;
  if(selected){
   const b=selected.bot,o=selected.opponent;
   q('#duelWeaponBars').innerHTML=Object.entries(gunNames).map(([key,label])=>{
    const bw=b.weapons?.[key]||{},ow=o.weapons?.[key]||{};
    if(finite(bw.damage)){if(['rocket','plasma','grenade'].includes(key))projectile+=bw.damage;else direct+=bw.damage;}
    return `<div class="weapon-detail"><strong>${label}</strong><div class="comparison-bar"><i style="width:${finite(bw.accuracy_pct)?Math.min(100,bw.accuracy_pct):0}%"></i><span>Бот ${accuracy(b,key)} · ${value(bw.shots)} shots · ${value(bw.damage)} dmg</span></div><div class="comparison-bar damage"><i style="width:${finite(ow.accuracy_pct)?Math.min(100,ow.accuracy_pct):0}%"></i><span>Соперник ${accuracy(o,key)} · ${value(ow.shots)} shots · ${value(ow.damage)} dmg</span></div></div>`;
   }).join('');
   const maxP=Math.max(1,...['red','mega','yellow'].flatMap(k=>[b.pickups?.[k],o.pickups?.[k]]).filter(finite));
   q('#duelPickupBars').innerHTML=['red','mega','yellow'].map(k=>`<div class="weapon-detail"><strong>${k.toUpperCase()}</strong><div class="comparison-bar"><i style="width:${(b.pickups?.[k]||0)/maxP*100}%"></i><span>Бот: ${value(b.pickups?.[k])}</span></div><div class="comparison-bar damage"><i style="width:${(o.pickups?.[k]||0)/maxP*100}%"></i><span>Соперник: ${value(o.pickups?.[k])}</span></div></div>`).join('');
  }
  pie('#duelDamagePie',direct,projectile,['Hitscan · известный урон','RL/PG/GL · известный урон']);
 }
 q('#duelActor').addEventListener('change',()=>{selectedId=null;render();});q('#duelType').addEventListener('change',()=>{selectedId=null;render();});render();
 async function refresh(){
  try{
   // На собственном VPS читаем свежую публичную статистику прямо с сервера.
   const ledgerUrl=['50515051.com','78.17.9.235'].includes(window.location?.hostname)?'/api/matches.json':data.ledgerUrl;
   const response=await window.fetch(ledgerUrl+'?snapshot='+Math.floor(Date.now()/30000),{cache:'no-store',credentials:'omit'});
   if(!response.ok)throw Error('not available');const text=await response.text();if(text.length>10000000)throw Error('too large');
   const fresh=JSON.parse(text);if(!Array.isArray(fresh.matches)||fresh.schema_version!==1)throw Error('schema');
   if(JSON.stringify(fresh.matches)!==JSON.stringify(ledger.matches)){ledger=fresh;render();}
   q('#ledgerSync').textContent='Онлайн-файл проверен · '+new Date().toLocaleTimeString('ru-RU')+' · новые матчи появляются после завершения и синхронизации.';
  }catch(_){q('#ledgerSync').textContent='Показан встроенный снимок. Онлайн-файл пока недоступен; данные сохранены в HTML.';}
 }
 if(typeof window.fetch==='function'){refresh();window.setInterval(refresh,30000);}
 window.PsyzDuelModel={select,comparable,accuracy};
})();
