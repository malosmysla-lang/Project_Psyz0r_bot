/* Копирование работает и на HTTPS, и на HTTP-копии сайта на VPS. */
(() => {
  if(!document.body?.append)return;
  const button=document.querySelector('#copyServerConnect'),command=document.querySelector('#serverConnectCommand');
  if(!button||!command)return;
  button.addEventListener('click',async()=>{
    const text=command.textContent.trim();let copied=false;
    try{if(window.isSecureContext&&navigator.clipboard?.writeText){await navigator.clipboard.writeText(text);copied=true;}}catch(_){}
    if(!copied){
      const field=document.createElement('textarea');field.value=text;field.setAttribute('readonly','');
      field.style.cssText='position:fixed;left:-9999px;top:0';document.body.append(field);field.select();
      try{copied=document.execCommand('copy');}catch(_){}finally{field.remove();button.focus();}
    }
    const status=document.querySelector('#connectCopyStatus');
    status.textContent=copied?'Команда скопирована — вставь в консоль Quake Live.':'Выдели и скопируй команду вручную.';
  });
})();
