/* Черновой векторный спортсмен: заменить форму по референсу владельца.
   Координаты ракеты берутся из реальной раскладки, а не из ширины монитора. */
(() => {
  const heading = document.querySelector('.headline h1');
  const target = document.querySelector('.headline .release');
  if (!heading || !target || !document.body?.animate) return;
  heading.classList.add('mascot-heading');
  const bot = document.createElement('span');
  bot.className = 'bot-mascot';
  bot.setAttribute('aria-hidden', 'true');
  bot.innerHTML = `<svg viewBox="0 0 72 96" fill="none" xmlns="http://www.w3.org/2000/svg"><g stroke="#bcecff" stroke-width="2" stroke-linejoin="round"><path fill="#edfaff" d="M27 6h17l5 8-3 14H28l-5-14z"/><path fill="#238ad0" d="M25 14h23l-3 8H29z"/><path fill="#268ed0" d="M27 30h18l7 26-9 8H29l-8-10z"/><path fill="#eefaff" d="M27 32l7 13h8l3-13M29 62l-5 19-9 7 3 5h14l7-25M42 63l8 16 2 13h12v-6l-5-11-7-21"/><path fill="#e6f6ff" d="M25 33L13 48l6 7 15-9M46 34l7 10 11-2 3 8-19 5-10-11"/><path fill="#306988" d="M43 36h26v10H43z"/><path stroke="#59d8ff" d="M48 39h16"/></g></svg>`;
  heading.prepend(bot);
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  let busy = false;
  // Один цикл: прыжок → выстрел → попадание → контур гаснет за 1.3 секунды.
  async function play() {
    if (busy || reduced.matches || document.hidden) return;
    busy = true;
    let rocket;
    let flash;
    try {
      const jump = bot.animate([{transform:'translateY(0)'},{transform:'translateY(-62px)',offset:.38},{transform:'translateY(-62px)',offset:.58},{transform:'translateY(0)'}],{duration:1100,easing:'ease-in-out'});
      await new Promise(resolve => setTimeout(resolve, 420));
      if (reduced.matches || document.hidden) { jump.cancel(); return; }
      const b = bot.getBoundingClientRect(), t = target.getBoundingClientRect();
      const start = {x:b.right-5,y:b.top+b.height*.43};
      const end = {x:t.left,y:Math.max(t.top+16,Math.min(t.bottom-16,start.y))};
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
      await Promise.all([
        flash.animate([{opacity:1,transform:'translate(-50%,-50%) scale(.2)'},{opacity:0,transform:'translate(-50%,-50%) scale(1.5)'}],{duration:420}).finished,
        target.animate([{borderColor:'#e9fbff',boxShadow:'0 0 22px #65dcff99, inset 0 0 14px #65dcff33'},{borderColor:'#564174',boxShadow:'0 0 0 transparent'}],{duration:1300,easing:'ease-out'}).finished,
        jump.finished
      ]);
    } catch (_) { /* Смена вкладки или отмена анимации не ломает дашборд. */ }
    finally { rocket?.remove(); flash?.remove(); busy = false; }
  }
  setTimeout(play, 1500);
  setInterval(play, 12000);
})();
