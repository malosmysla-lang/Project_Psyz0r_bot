/* Двенадцать положений механических век; корпус орба остаётся неподвижным. */
(() => {
  // Текст бренда перезагружает документ; глаз — отдельная кнопка без навигации.
  document.querySelector('#brandHome')?.addEventListener('click',event=>{event.preventDefault();window.location.reload();});
  if(!document.body?.animate)return;
  const eye=document.querySelector('.eye-mark');if(!eye)return;
  const glint=document.createElement('span');glint.className='eye-glint';glint.setAttribute('aria-hidden','true');eye.append(glint);
  const mask=document.createElement('span');mask.className='eye-shutter';mask.setAttribute('aria-hidden','true');
  mask.innerHTML='<i class="upper-lid"></i><i class="lower-lid"></i>';eye.append(mask);
  const upper=mask.querySelector('.upper-lid'),lower=mask.querySelector('.lower-lid');
  const reduced=matchMedia('(prefers-reduced-motion: reduce)');
  let timer=null,animations=[];
  const openness=[0,.12,.38,.7,.94,1,1,.88,.63,.35,.12,0];
  function schedule(){clearTimeout(timer);if(!reduced.matches&&!document.hidden)timer=setTimeout(blink,6000+Math.random()*2000);}
  async function blink(){
    if(reduced.matches||document.hidden||animations.length)return;
    clearTimeout(timer);
    const keys=direction=>openness.map((closed,i)=>({offset:i/11,transform:`translateY(${direction*(1-closed)*100}%)`}));
    animations=[upper.animate(keys(-1),{duration:420,easing:'linear'}),lower.animate(keys(1),{duration:420,easing:'linear'})];
    await Promise.allSettled(animations.map(a=>a.finished));animations=[];schedule();
  }
  eye.addEventListener('click',blink);
  function refresh(){clearTimeout(timer);animations.forEach(a=>a.cancel());schedule();}
  document.addEventListener('visibilitychange',refresh);reduced.addEventListener('change',refresh);schedule();
})();
