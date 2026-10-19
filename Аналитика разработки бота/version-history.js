/* Interactive local comparison, no network/live telemetry is implied. */
if(D.versionHistory){
 const labels={demos:'Разобранные демки',rules:'Правила карты',cpp:'Группы CTest'};
 function renderHistory(){
  const selected=$('#versionSelect').value||'0.7.9',key=$('#metricSelect').value||'demos';
  const rows=D.versionHistory,active=rows.find(x=>x.version===selected)||rows[rows.length-1],max=Math.max(1,...rows.map(x=>x[key]));
  $('#versionTrend').innerHTML=rows.map(x=>`<div class="history-row ${x===active?'is-selected':''}"><span>${esc(x.version)}</span><div class="history-track"><i style="width:${x[key]/max*100}%"></i></div><strong>${x[key]}</strong></div>`).join('');
  $('#versionTitle').textContent=`${active.version} · ${active.stage}`;
  $('#versionNote').textContent=active.note;
  $('#versionValues').innerHTML=Object.entries(labels).map(([k,label])=>`<div class="jumpmetric"><span>${label}</span><strong>${active[k]}</strong></div>`).join('');
 }
 $('#versionSelect').addEventListener('change',renderHistory);$('#metricSelect').addEventListener('change',renderHistory);renderHistory();
}
