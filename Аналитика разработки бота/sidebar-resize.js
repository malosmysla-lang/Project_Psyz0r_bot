/* Ширина меню меняется отдельно от содержимого: диапазон 150 px, настройка локальна. */
(() => {
  if(!document.body?.append)return;
  const rail=document.querySelector('.rail');if(!rail)return;
  const root=document.documentElement,key='pracc-sidebar-width',min=240,max=390,initial=300;
  const handle=document.createElement('div');handle.className='sidebar-resizer';handle.tabIndex=0;
  handle.setAttribute('role','separator');handle.setAttribute('aria-orientation','vertical');
  handle.setAttribute('aria-label','Ширина бокового меню');handle.setAttribute('aria-valuemin',min);handle.setAttribute('aria-valuemax',max);
  handle.title='Потяни для изменения ширины · стрелки ← → · двойной щелчок для сброса';
  handle.innerHTML='<span>⋮</span>';document.body.append(handle);
  let width=initial,dragging=false;
  function apply(value,persist=false){
    width=Math.max(min,Math.min(max,Math.round(Number(value)||initial)));
    root.style.setProperty('--rail-width',width+'px');handle.setAttribute('aria-valuenow',width);
    if(persist)try{localStorage.setItem(key,String(width));}catch(_){}
  }
  try{apply(localStorage.getItem(key)||initial);}catch(_){apply(initial);}
  handle.addEventListener('pointerdown',event=>{
    if(event.button!==0)return;dragging=true;handle.setPointerCapture(event.pointerId);
    document.body.classList.add('resizing-sidebar');event.preventDefault();
  });
  handle.addEventListener('pointermove',event=>{if(dragging)apply(event.clientX);});
  function finish(){if(!dragging)return;dragging=false;document.body.classList.remove('resizing-sidebar');apply(width,true);}
  handle.addEventListener('pointerup',finish);handle.addEventListener('pointercancel',finish);handle.addEventListener('lostpointercapture',finish);
  handle.addEventListener('dblclick',()=>apply(initial,true));
  handle.addEventListener('keydown',event=>{
    if(!['ArrowLeft','ArrowRight','Home','End'].includes(event.key))return;
    event.preventDefault();apply(event.key==='Home'?min:event.key==='End'?max:width+(event.key==='ArrowLeft'?-10:10),true);
  });
})();
