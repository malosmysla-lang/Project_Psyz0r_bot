/* Green means a recent live test-engine check, not simply that the page loaded. */
(() => {
 if(!document.body?.append || !window.fetch)return;
 const row=document.querySelector('.connect-topline');if(!row)return;
 const lamp=row.querySelector('.led'),label=document.createElement('span');label.className='server-online-label';label.setAttribute('role','status');label.textContent='Проверяем сервер';row.append(label);
 const check=async()=>{
   try{
     const response=await fetch('/api/server-status.json',{cache:'no-store',credentials:'omit',signal:AbortSignal.timeout(4000)});
     if(!response.ok)throw Error('status');const data=await response.json();
     if(typeof data.online!=='boolean'||Date.now()-Date.parse(data.checked_at)>30000)throw Error('stale');
     lamp.classList.toggle('server-online',data.online);lamp.classList.toggle('server-offline',!data.online);
     label.textContent=data.online?'Сервер онлайн':'Сервер недоступен';
     row.title='Последняя проверка: '+new Date(data.checked_at).toLocaleTimeString();
   }catch(_){lamp.classList.remove('server-online');lamp.classList.add('server-offline');label.textContent='Статус не получен';}
 };
 if(location.protocol==='http:'||location.protocol==='https:'){check();setInterval(()=>{if(!document.hidden)check();},15000);}
 else{label.textContent='Офлайн-снимок';lamp.classList.add('server-offline');}
})();
