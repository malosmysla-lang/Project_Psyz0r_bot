/* Детальный Doom Marine: четыре согласованные позы и плавная дуга прыжка.
   Координаты ракеты берутся из реальной раскладки, а не из ширины монитора. */
(() => {
  const heading = document.querySelector('.headline h1');
  const target = document.querySelector('.headline .release');
  if (!heading || !target || !document.body?.animate) return;
  heading.classList.add('mascot-heading');
  const bot = document.createElement('span');
  bot.className = 'bot-mascot';
  bot.setAttribute('aria-hidden', 'true');
  heading.prepend(bot);
  bot.innerHTML = '<span class="marine-sprite"></span><span class="barrel-smoke"><i></i><i></i><i></i><i></i></span>';
  const sprite=bot.querySelector('.marine-sprite');
  const frame=n=>{sprite.style.backgroundPosition=`${n*100/3}% 50%`;};
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  let busy = false;
  // Один цикл: прыжок → выстрел → попадание → контур гаснет за 1.3 секунды.
  async function play() {
    if (busy || reduced.matches || document.hidden) return;
    busy = true;
    let rocket;
    let flash;
    try {
      frame(1);await new Promise(resolve=>setTimeout(resolve,180));frame(2);
      // 20 опорных положений: браузер интерполирует движение без ограничения FPS.
      const arc=Array.from({length:20},(_,i)=>({offset:i/19,transform:`translateY(${-86*Math.sin(Math.PI*i/19)}px)`}));
      const jump = bot.animate(arc,{duration:1900,easing:'linear'});
      await new Promise(resolve => setTimeout(resolve, 700));frame(3);
      if (reduced.matches || document.hidden) { jump.cancel(); return; }
      const b = bot.getBoundingClientRect(), t = target.getBoundingClientRect();
      const start = {x:b.right-5,y:b.top+b.height*.25};
      const end = {x:t.left+2,y:t.top+18};
      const angle = Math.atan2(end.y-start.y,end.x-start.x)*180/Math.PI;
      rocket = document.createElement('span');
      rocket.className = 'mascot-rocket';
      rocket.setAttribute('aria-hidden','true');
      rocket.style.cssText = `left:${start.x}px;top:${start.y}px;--rocket-angle:${angle}deg`;
      document.body.append(rocket);
      await rocket.animate([{transform:`translate(0,-50%) rotate(${angle}deg)`},{transform:`translate(${end.x-start.x}px,${end.y-start.y}px) rotate(${angle}deg)`}],{duration:650,easing:'linear',fill:'forwards'}).finished;
      rocket.remove();
      flash = document.createElement('span');
      flash.className = 'mascot-impact';
      flash.setAttribute('aria-hidden','true');
      flash.style.cssText = `left:${end.x}px;top:${end.y}px`;
      document.body.append(flash);
      // Приземление не ждёт завершения свечения рамки.
      jump.finished.then(()=>{frame(0);bot.classList.add('has-fired');});
      await Promise.all([
        flash.animate([{opacity:1,transform:'translate(-50%,-50%) scale(.2)'},{opacity:0,transform:'translate(-50%,-50%) scale(1.5)'}],{duration:420}).finished,
        target.animate([{borderColor:'#e9fbff',boxShadow:'0 0 22px #65dcff99, inset 0 0 14px #65dcff33'},{borderColor:'#564174',boxShadow:'0 0 0 transparent'}],{duration:1300,easing:'ease-out'}).finished,
        jump.finished
      ]);
    } catch (_) { /* Смена вкладки или отмена анимации не ломает дашборд. */ }
    finally { rocket?.remove(); flash?.remove(); frame(0);busy = false; }
  }
  // Только один выстрел после reload. Никакого повторяющегося таймера.
  const ready=new Image();ready.onload=()=>setTimeout(play,1500);
  ready.src='assets/doom-marine-strip.png';
})();
