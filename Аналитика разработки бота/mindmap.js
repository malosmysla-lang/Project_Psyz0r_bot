/* Pinterest-inspired living tree: DOM cards, SVG connections, local-only layout. */
(function(){
 'use strict';
 const host=document.querySelector('#mindmapApp');if(!host||typeof host.querySelector!=='function')return;
 const C=window.PsyzMapCore,R=window.PSYZ_ANALYTICS.registry;
 const escape=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const key='psyzMindmap:v'+R.version;let saved={};
 try{saved=JSON.parse(localStorage.getItem(key)||'{}')||{};}catch(_){}
 const state={expanded:new Set(Array.isArray(saved.expanded)?saved.expanded:[]),positions:saved.positions&&typeof saved.positions==='object'?saved.positions:{},query:'',status:'',selected:null,view:{scale:1,x:0,y:0}};
 host.innerHTML=`<div class="map-shell"><div class="map-controls"><div class="map-title"><span class="map-live-dot"></span>Живая карта <small>${R.rule_count} правил / ${R.branches.length} веток</small></div><div class="map-actions"><button type="button" data-map="overview">Обзор</button><button type="button" data-map="expand">Развернуть всё</button><button type="button" data-map="fit">Вписать</button><button type="button" data-map="full">На весь экран</button></div></div>
 <div class="map-filter"><input type="search" aria-label="Поиск в интерактивной карте" placeholder="Найти правило или тему: F27 / шафт / красный…"><select aria-label="Статус правил на карте"><option value="">Все статусы</option>${['LIVE','PARTIAL','LOCAL','SPEC','DATA','PAUSED','CONFLICT'].map(s=>`<option>${s}</option>`).join('')}</select><button type="button" data-map="reset" title="Сбросить только положения узлов этой карты">Сброс раскладки</button></div>
 <div class="map-workspace"><div class="map-viewport" tabindex="0" aria-label="Интерактивная mind map. Тяни фон для перемещения. Колесо и кнопки меняют масштаб. Enter раскрывает ветку."><div class="map-layer"><svg class="map-edges" width="1" height="1" aria-hidden="true"><g></g></svg><div class="map-nodes"></div></div><div class="map-empty" hidden>Правила не найдены. Попробуй другой запрос.</div><div class="map-zoom"><button type="button" data-map="minus" aria-label="Уменьшить масштаб">−</button><output>100%</output><button type="button" data-map="plus" aria-label="Увеличить масштаб">+</button></div><svg class="map-mini" aria-label="Мини-карта. Нажми для перехода" role="img" preserveAspectRatio="none"></svg><div class="map-gesture">Тяни узлы или фон · колесо — масштаб · F — вписать</div></div><aside class="map-inspector" hidden aria-live="polite"></aside></div>
 <div class="map-bottom"><span class="map-state" aria-live="polite"></span><button type="button" data-map="layout">Скачать раскладку JSON</button></div></div>`;
 const shell=host.querySelector('.map-shell'),vp=host.querySelector('.map-viewport'),layer=host.querySelector('.map-layer'),nodeHost=host.querySelector('.map-nodes'),edges=host.querySelector('.map-edges g'),mini=host.querySelector('.map-mini'),inspector=host.querySelector('.map-inspector'),search=host.querySelector('input'),status=host.querySelector('select'),message=host.querySelector('.map-state');
 let model,nodeMap=new Map(),buttons=new Map(),drag=null,frame=0,saveTimer;
 function persist(){
  try{localStorage.setItem(key,JSON.stringify({expanded:[...state.expanded],positions:state.positions}));return true;}catch(_){message.textContent+=' · браузер не разрешил сохранение раскладки';return false;}
 }
 function paintView(){
  const v=state.view;layer.style.transform=`translate(${v.x}px,${v.y}px) scale(${v.scale})`;
  host.querySelector('.map-zoom output').textContent=Math.round(v.scale*100)+'%';paintMini();
 }
 function paintEdges(){edges.innerHTML=model.edges.map(e=>{const a=nodeMap.get(e.from),b=nodeMap.get(e.to),selected=state.selected===e.to||state.selected===e.from;return`<path d="${C.edgePath(a,b)}" fill="none" stroke="${e.color}" class="${selected?'map-edge-active':''}" stroke-width="${b.type==='branch'?2.2:1.25}" opacity="${selected?.95:.38}"/>`;}).join('');}
 function paintMini(){
  if(!model)return;const b=C.bounds(model.nodes),pad=70,box={x:b.x-pad,y:b.y-pad,width:b.width+pad*2,height:b.height+pad*2};
  mini.setAttribute('viewBox',`${box.x} ${box.y} ${box.width} ${box.height}`);
  mini.innerHTML=model.nodes.map(n=>`<rect x="${n.x-n.width/2}" y="${n.y-n.height/2}" width="${n.width}" height="${n.height}" rx="${n.type==='rule'?12:40}" fill="${n.color}" opacity="${n.type==='rule'?.42:.9}"/>`).join('')+`<rect class="mini-window" x="${-state.view.x/state.view.scale}" y="${-state.view.y/state.view.scale}" width="${vp.clientWidth/state.view.scale}" height="${vp.clientHeight/state.view.scale}" fill="none" stroke="#f1f6ff" stroke-width="${Math.max(3,box.width/160)}"/>`;
 }
 function fitNodes(ids){
  const ns=ids?model.nodes.filter(n=>ids.has(n.id)):model.nodes;
  state.view=C.fit(C.bounds(ns),vp.clientWidth||1000,vp.clientHeight||680,46);paintView();
 }
 function inspect(node){
  if(!node||node.type==='root'){inspector.hidden=true;shell.classList.remove('has-inspector');return;}
  const branch=R.branches.find(b=>b.letter===node.letter);
  inspector.hidden=false;shell.classList.add('has-inspector');
  const text=node.type==='rule'?node.text:'Выбери карточку правила. Цвет обозначает тему, статус — глубину подтверждения. Двойной клик по ветке вписывает её в окно.';
  inspector.innerHTML=`<button class="inspector-close" type="button" aria-label="Закрыть карточку">×</button><div class="section-label" style="color:${node.color}">${escape(node.type==='rule'?node.id:'ВЕТКА '+node.letter)}</div><h3>${escape(node.type==='rule'?branch.title:node.title)}</h3>${node.status?`<span class="pill ${escape(node.status.split('/')[0])}">${escape(node.status)}</span>`:''}<p>${escape(text)}</p><div class="inspector-path">Psyz0r → ${escape(node.letter)}${node.type==='rule'?' → '+escape(node.id):''}</div><p class="caption">${node.type==='rule'?'Полная формулировка из реестра. SPEC/DATA не означают, что функция работает в игре.':`${branch.items.length} правил. Тяни карточки — связи последуют за ними.`}</p><button type="button" class="inspector-branch">Показать всю ветку ${escape(node.letter)}</button>`;
  inspector.querySelector('.inspector-close').onclick=()=>{inspect(null);paintView();};
  inspector.querySelector('.inspector-branch').onclick=()=>focusBranch(node.letter);
 }
 function render(){
  model=C.graph(R,state);nodeMap=new Map(model.nodes.map(n=>[n.id,n]));buttons.clear();
  nodeHost.innerHTML=model.nodes.map(n=>`<button type="button" data-node="${escape(n.id)}" class="map-node map-${n.type}${n.dimmed?' is-dimmed':''}${state.selected===n.id?' is-selected':''}" style="left:${n.x}px;top:${n.y}px;width:${n.width}px;height:${n.height}px;--node-color:${n.color}" ${n.type==='branch'?`aria-expanded="${n.open}"`:''} aria-label="${escape(n.type==='rule'?n.id+' '+n.status+' '+n.text:n.title)}">${n.type==='root'?'<span class="root-eyebrow">TRAINING DUEL BOT</span><strong>Psyz0r</strong><small>Человечная игра · система решений</small>':n.type==='branch'?`<span class="branch-letter">${n.letter}</span><strong>${escape(n.title)}</strong><small>${n.count} правил <span>${n.open?'− свернуть':'+ раскрыть'}</span></small>`:`<span class="rule-head"><b>${escape(n.id)}</b><em>${escape(n.status)}</em></span><span class="rule-preview">${escape(n.text)}</span>`}</button>`).join('');
  for(const button of nodeHost.querySelectorAll('[data-node]')){
   buttons.set(button.dataset.node,button);
   button.addEventListener('click',e=>{if(e.detail===0)select(button.dataset.node);});
   button.addEventListener('dblclick',()=>{const n=nodeMap.get(button.dataset.node);if(n?.letter)focusBranch(n.letter);});
  }
  paintEdges();paintView();
  const filtering=state.query||state.status;
  host.querySelector('.map-empty').hidden=!(filtering&&!model.visibleRules);
  message.textContent=`${model.visibleRules} правил раскрыто из ${model.totalRules} · ${R.branches.length} веток · положения сохраняются в этом браузере`;
 }
 function select(id){
  const n=nodeMap.get(id);if(!n)return;state.selected=id;
  if(n.type==='root'){overview();return;}
  if(n.type==='branch'){
   if(state.expanded.has(n.letter))state.expanded.delete(n.letter);else state.expanded.add(n.letter);
   render();inspect(n);fitNodes(new Set(model.nodes.filter(x=>x.letter===n.letter).map(x=>x.id)));persist();
  }else{
   for(const [nodeId,b]of buttons)b.classList.toggle('is-selected',nodeId===id);
   inspect(n);paintEdges();paintMini();
  }
 }
 function overview(){state.query='';state.status='';search.value='';status.value='';state.expanded.clear();state.selected=null;inspect(null);render();fitNodes();persist();}
 function focusBranch(letter){
  state.query='';state.status='';search.value='';status.value='';state.expanded=new Set([letter]);state.selected='branch:'+letter;
  render();inspect(nodeMap.get(state.selected));fitNodes(new Set(model.nodes.filter(n=>n.letter===letter).map(n=>n.id)));persist();
 }
 function applySearch(){state.query=search.value;state.status=status.value;state.selected=null;inspect(null);render();const matching=model.nodes.filter(n=>n.type==='rule'||(n.type==='branch'&&n.matching));fitNodes(matching.length?new Set(matching.map(n=>n.id)):null);}
 search.addEventListener('input',()=>{clearTimeout(saveTimer);saveTimer=setTimeout(applySearch,120);});status.addEventListener('change',applySearch);
 function changeZoom(factor,point={x:vp.clientWidth/2,y:vp.clientHeight/2}){state.view=C.zoom(state.view,factor,point);paintView();}
 vp.addEventListener('wheel',e=>{e.preventDefault();const r=vp.getBoundingClientRect();changeZoom(Math.exp(-C.clamp(e.deltaY,-100,100)*.002),{x:e.clientX-r.left,y:e.clientY-r.top});},{passive:false});
 vp.addEventListener('pointerdown',e=>{
  if(e.button!==0||e.target.closest('.map-zoom,.map-mini'))return;
  const button=e.target.closest('[data-node]'),node=button?nodeMap.get(button.dataset.node):null;
  drag={pointer:e.pointerId,startX:e.clientX,startY:e.clientY,node,origin:node?{x:node.x,y:node.y}:{x:state.view.x,y:state.view.y},moved:false};
  vp.setPointerCapture(e.pointerId);vp.classList.add('is-grabbing');
 });
 vp.addEventListener('pointermove',e=>{
  if(!drag||drag.pointer!==e.pointerId)return;const dx=e.clientX-drag.startX,dy=e.clientY-drag.startY;
  if(Math.hypot(dx,dy)<4&&!drag.moved)return;drag.moved=true;
  if(drag.node){
   const n=drag.node;n.x=drag.origin.x+dx/state.view.scale;n.y=drag.origin.y+dy/state.view.scale;state.positions[n.id]={x:n.x,y:n.y};
   const button=buttons.get(n.id);button.style.left=n.x+'px';button.style.top=n.y+'px';button.classList.add('is-dragging');
   if(!frame)frame=requestAnimationFrame(()=>{frame=0;paintEdges();paintMini();});
  }else{state.view.x=drag.origin.x+dx;state.view.y=drag.origin.y+dy;paintView();}
 });
 function finish(e){
  if(!drag||drag.pointer!==e.pointerId)return;const d=drag;drag=null;vp.classList.remove('is-grabbing');
  if(vp.hasPointerCapture(e.pointerId))vp.releasePointerCapture(e.pointerId);
  if(d.node){buttons.get(d.node.id)?.classList.remove('is-dragging');if(d.moved){state.selected=d.node.id;inspect(d.node);persist();paintEdges();}else if(e.type!=='pointercancel')select(d.node.id);}
 }
 vp.addEventListener('pointerup',finish);vp.addEventListener('pointercancel',finish);
 vp.addEventListener('keydown',e=>{
  if(e.target.closest('input,select'))return;
  if(e.key==='+'||e.key==='='){e.preventDefault();changeZoom(1.2);}else if(e.key==='-'){e.preventDefault();changeZoom(1/1.2);}
  else if(e.key.toLowerCase()==='f'){e.preventDefault();fitNodes();}
  else if(['ArrowUp','ArrowDown','ArrowLeft','ArrowRight'].includes(e.key)){e.preventDefault();state.view.x+=e.key==='ArrowLeft'?60:e.key==='ArrowRight'?-60:0;state.view.y+=e.key==='ArrowUp'?60:e.key==='ArrowDown'?-60:0;paintView();}
  else if(e.key==='Escape'){inspect(null);paintView();}
 });
 mini.addEventListener('pointerdown',e=>{
  e.stopPropagation();const r=mini.getBoundingClientRect(),b=mini.viewBox.baseVal;
  const x=b.x+(e.clientX-r.left)/r.width*b.width,y=b.y+(e.clientY-r.top)/r.height*b.height;
  state.view.x=vp.clientWidth/2-x*state.view.scale;state.view.y=vp.clientHeight/2-y*state.view.scale;paintView();
 });
 for(const control of host.querySelectorAll('[data-map]'))control.addEventListener('click',async()=>{
  switch(control.dataset.map){
   case'overview':overview();break;
   case'expand':state.expanded=new Set(R.branches.map(b=>b.letter));state.query='';state.status='';search.value=status.value='';inspect(null);render();fitNodes();persist();break;
   case'fit':fitNodes();break;
   case'plus':changeZoom(1.2);break;
   case'minus':changeZoom(1/1.2);break;
   case'full':try{if(document.fullscreenElement)await document.exitFullscreen();else await shell.requestFullscreen();}catch(_){shell.classList.toggle('map-maximized');}requestAnimationFrame(()=>fitNodes());break;
   case'reset':state.positions={};overview();break;
   case'layout':{
    const blob=new Blob([JSON.stringify({version:R.version,expanded:[...state.expanded],positions:state.positions},null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='Psyz0r_mindmap_layout.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);break;
   }
  }
 });
 if(typeof ResizeObserver!=='undefined')new ResizeObserver(()=>paintView()).observe(vp);
 document.addEventListener('fullscreenchange',()=>requestAnimationFrame(()=>fitNodes()));
 render();requestAnimationFrame(()=>fitNodes());
 window.PsyzMindmap={focusBranch:letter=>{host.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'start'});focusBranch(letter);},overview,getSnapshot:()=>({visibleRules:model.visibleRules,totalRules:model.totalRules,expanded:[...state.expanded],positions:JSON.parse(JSON.stringify(state.positions)),view:{...state.view}})};
})();
