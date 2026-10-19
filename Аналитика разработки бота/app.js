/* All data is generated locally. No fetch, analytics trackers, credentials or live-server commands. */
const D=window.PSYZ_ANALYTICS, $=s=>document.querySelector(s);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const pill=s=>`<span class="pill ${esc(s.split('/')[0])}">${esc(s)}</span>`;
const colors=['#59dbec','#f4cc78','#bb91f3','#ff92a4','#8bdd98','#ffda9c','#72dccc','#ffae6f','#8fb8ff','#dd9cef','#b9dc77','#ff8b87','#7bd4a7','#bfa4fc','#ffc482'];
function bars(rows,max){return rows.map(([k,v,c])=>`<div class="barrow"><span>${esc(k)}</span><div class="bar"><i style="width:${max?v/max*100:0}%;background:${c||'var(--cyan)'}"></i></div><b>${v}</b></div>`).join('')}
$('#metrics').innerHTML=D.metrics.map(x=>`<article class="metric"><div class="section-label">${esc(x.label)}</div><strong>${esc(x.value)}</strong><small>${esc(x.note)}</small></article>`).join('');
$('#release').textContent=D.release;
const counts={};for(const b of D.registry.branches)for(const r of b.items){const s=r.status.split('/')[0];counts[s]=(counts[s]||0)+1}
$('#statusbars').innerHTML=bars(Object.entries(counts).sort((a,b)=>b[1]-a[1]),D.registry.rule_count);
$('#moduleRows').innerHTML=D.modules.map(x=>`<tr><td>${esc(x.name)}</td><td>${pill(x.code)}</td><td>${pill(x.game)}</td><td>${esc(x.evidence)}<br><a href="../${encodeURI(x.source)}">Источник ↗</a></td></tr>`).join('');
function renderRules(){const q=$('#search').value.trim().toLocaleLowerCase('ru'),s=$('#status').value;let total=0;$('#branches').innerHTML=D.registry.branches.map((b,i)=>{const rs=b.items.filter(r=>(!s||r.status.split('/')[0]===s)&&(!q||(`${r.id} ${r.text} ${b.title}`).toLocaleLowerCase('ru').includes(q)));total+=rs.length;return rs.length?`<details style="--branch:${colors[i]}" ${q||s?'open':''}><summary>${esc(b.letter)} / ${esc(b.title)}<small>${rs.length} из ${b.items.length} правил · раскрыть ↓</small></summary>${rs.map(r=>`<div class="rule"><code>${esc(r.id)}</code> ${pill(r.status)}<p>${esc(r.text)}</p></div>`).join('')}</details>`:''}).join('');$('#ruleCount').textContent=`Показано ${total} из ${D.registry.rule_count} правил. Все прежние ID сохранены.`}
$('#search').addEventListener('input',renderRules);$('#status').addEventListener('change',renderRules);$('#expand').addEventListener('click',()=>{const all=[...document.querySelectorAll('#branches details')],open=all.some(x=>!x.open);all.forEach(x=>x.open=open);$('#expand').textContent=open?'Свернуть все':'Раскрыть все'});renderRules();
$('#players').innerHTML=bars(D.players,Math.max(1,...D.players.map(x=>x[1])));
$('#jumpStats').innerHTML=D.jumpStats.map(x=>`<div class="jumpmetric"><span>${esc(x.label)}</span><strong>${esc(x.value)}</strong></div>`).join('');
$('#modes').innerHTML=D.modes.map(x=>`<article class="card panel mode"><div class="section-label">${esc(x.tag)}</div><h3>${esc(x.name)}</h3><p>${esc(x.text)}</p>${pill(x.status)}</article>`).join('');
$('#lgStats').innerHTML=`<div class="tablewrap"><table class="table"><thead><tr><th>Игрок</th><th>Кадры LG</th><th>Yaw median</th><th>Yaw p95</th><th>Стрейф median</th></tr></thead><tbody>${D.lg.map(x=>`<tr><td>${esc(x.name)}</td><td>${esc(x.frames)}</td><td>${esc(x.yaw)} °/с</td><td>${esc(x.p95)} °/с</td><td>${esc(x.strafe)} мс</td></tr>`).join('')}</tbody></table></div>`;
$('#testCards').innerHTML=D.tests.map(x=>`<article class="card panel test"><div class="section-label">${esc(x.label)}</div><strong>${esc(x.value)}</strong><p>${esc(x.note)}</p></article>`).join('');
$('#ownerMatches').innerHTML=`<div class="tablewrap"><table class="table"><thead><tr><th>Бот</th><th>Матчи ZTN</th><th>Строки статистики</th><th>RA</th><th>Mega</th><th>YA</th><th>Фраги / смерти</th></tr></thead><tbody>${D.ownerComparison.map(x=>`<tr><td>${esc(x.category)}</td><td>${x.matches}</td><td>${x.scoreboards_with_bot_stats}</td><td>${x.red}</td><td>${x.mega}</td><td>${x.yellow}</td><td>${x.kills} / ${x.deaths}</td></tr>`).join('')}</tbody></table></div>`;
$('#longMatch').textContent=D.longMatch;
$('#questions').innerHTML=D.questions.map(x=>`<li>${esc(x)}</li>`).join('');
$('#backlogRows').innerHTML=D.backlog.map((x,i)=>`<article class="task"><b>${String(i+1).padStart(2,'0')}</b><div><h3>${esc(x.name)}</h3><p>${esc(x.test)}</p></div>${pill(x.status)}</article>`).join('');$('#generated').textContent=D.generated;
