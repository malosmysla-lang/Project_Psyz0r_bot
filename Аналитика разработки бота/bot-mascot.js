/* Тридцать поз персонажа. Прыжок по кнопке; дым и ракета имеют собственные часы. */
(() => {
  const heading=document.querySelector('.headline h1'),target=document.querySelector('.headline .release');
  if(!heading||!target||!document.body?.animate)return;
  heading.classList.add('mascot-heading');
  const bot=document.createElement('button');bot.type='button';bot.className='bot-mascot';bot.disabled=true;
  bot.setAttribute('aria-label','Прыгнуть и выстрелить ракетой');bot.title='Нажми: прыжок и выстрел';
  // Единая текстовая обёртка сохраняет переносы названия и его вертикальное выравнивание.
  const title=document.createElement('span');title.className='mascot-title';
  while(heading.firstChild)title.append(heading.firstChild);
  heading.append(title);
  bot.innerHTML='<canvas class="marine-sprite" width="280" height="360"></canvas><span class="barrel-smoke"><i></i><i></i><i></i><i></i><i></i><i></i></span>';
  heading.prepend(bot);
  const sprite=bot.querySelector('.marine-sprite');
  const reduced=matchMedia('(prefers-reduced-motion: reduce)');
  // Атлас имеет неравномерные поля: реальные границы каждой позы исключают соседние фигуры.
  const rects=[[43,10,196,245],[275,18,188,236],[495,40,192,213],[723,59,196,194],[942,13,204,239],[1163,9,203,242],[26,267,209,240],[260,262,210,247],[506,266,189,223],[726,266,191,216],[954,265,181,204],[1167,262,189,203],[31,516,186,204],[264,515,189,200],[497,515,184,201],[716,513,202,206],[936,515,201,206],[1178,512,176,215],[42,728,172,209],[271,737,175,204],[499,733,184,210],[724,742,178,201],[958,731,177,212],[1185,727,176,216],[41,954,182,183],[277,958,180,180],[504,943,182,195],[730,943,182,195],[954,943,180,195],[1181,943,183,195]];
  const context=sprite.getContext('2d');
  const frame=n=>{
    if(!ready.complete||!ready.naturalWidth)return;
    const [x,y,w,h]=rects[n],scale=Math.min(264/w,340/h);
    context.clearRect(0,0,280,360);context.imageSmoothingEnabled=true;context.imageSmoothingQuality='high';
    context.drawImage(ready,x,y,w,h,8+(264-w*scale)/2,350-h*scale,w*scale,h*scale);
  };
  let busy=false,raf=0,cancelJump=null;
  const effects=new Set();
  // Частицы остаются в точке следа и рассеиваются: дым не приклеен к ракете.
  function puff(x,y,index,barrel=false){
    const el=document.createElement('span');el.className='rocket-smoke-puff';el.setAttribute('aria-hidden','true');
    const size=barrel?5:7+index%4;
    el.style.cssText=`left:${x}px;top:${y}px;width:${size}px;height:${size}px`;
    document.body.append(el);effects.add(el);
    const drift=(index%2?1:-1)*(5+index%7);
    el.animate([{opacity:.34,transform:'translate(-50%,-50%) scale(.4)'},{opacity:.2,offset:.2},{opacity:0,transform:`translate(${drift}px,${-18-index%16}px) scale(3.5)`}],{duration:850+index%5*90,easing:'ease-out'}).finished.finally(()=>{el.remove();effects.delete(el);});
  }
  async function shoot(){
    if(reduced.matches)return;
    const b=bot.getBoundingClientRect(),t=target.getBoundingClientRect();
    const start={x:b.right-3,y:b.top+b.height*.25},end={x:t.left+2,y:t.top+18};
    const dx=end.x-start.x,dy=end.y-start.y,angle=Math.atan2(dy,dx)*180/Math.PI;
    // Постоянная скорость полёта; длительность зависит от расстояния в текущей раскладке.
    const duration=Math.min(1100,Math.max(450,Math.hypot(dx,dy)/1.35));
    const rocket=document.createElement('span');rocket.className='mascot-rocket';rocket.setAttribute('aria-hidden','true');
    rocket.style.cssText=`left:${start.x}px;top:${start.y}px`;document.body.append(rocket);effects.add(rocket);
    sprite.animate([{transform:'translateX(0)'},{transform:'translateX(-4px)',offset:.2},{transform:'translateX(0)'}],{duration:180});
    const begin=performance.now();let last=-1;
    function trail(now){
      if(!rocket.isConnected)return;
      const p=Math.min(1,(now-begin)/duration),segment=Math.floor(p*24);
      if(segment!==last){puff(start.x+dx*p,start.y+dy*p,segment);last=segment;}
      if(p<1)requestAnimationFrame(trail);
    }
    requestAnimationFrame(trail);
    await rocket.animate([{transform:`translate(0,-50%) rotate(${angle}deg)`},{transform:`translate(${dx}px,${dy}px) rotate(${angle}deg)`}],{duration,easing:'linear',fill:'forwards'}).finished;
    rocket.remove();effects.delete(rocket);if(reduced.matches)return;
    const flash=document.createElement('span');flash.className='mascot-impact';flash.setAttribute('aria-hidden','true');
    flash.style.cssText=`left:${end.x}px;top:${end.y}px`;document.body.append(flash);effects.add(flash);
    // Несколько слоёв взрыва: горячее ядро, ударное кольцо, обломки и тяжёлый дым.
    const ring=document.createElement('span');ring.className='explosion-ring';ring.setAttribute('aria-hidden','true');
    ring.style.cssText=`left:${end.x}px;top:${end.y}px`;document.body.append(ring);effects.add(ring);
    ring.animate([{opacity:.95,transform:'translate(-50%,-50%) scale(.15)'},{opacity:0,transform:'translate(-50%,-50%) scale(2.5)'}],{duration:650,easing:'ease-out'}).finished.finally(()=>{ring.remove();effects.delete(ring);});
    for(let i=0;i<18;i++){
      const a=i*Math.PI*2/18,reach=28+(i%5)*12;
      const shard=document.createElement('span');shard.className='explosion-shard';shard.setAttribute('aria-hidden','true');
      shard.style.cssText=`left:${end.x}px;top:${end.y}px;width:${2+i%3}px;height:${i%2?2:5}px`;
      document.body.append(shard);effects.add(shard);
      shard.animate([{opacity:1,transform:'translate(0,0) rotate(0deg)'},{opacity:.9,offset:.45},{opacity:0,transform:`translate(${Math.cos(a)*reach}px,${Math.sin(a)*reach+22}px) rotate(${i*73}deg)`}],{duration:480+i%5*85,easing:'cubic-bezier(.1,.5,.3,1)'}).finished.finally(()=>{shard.remove();effects.delete(shard);});
    }
    for(let i=0;i<18;i++)puff(end.x+(i%6-2.5)*9,end.y+(Math.floor(i/6)-1)*11,i);
    const glow=target.animate([{borderColor:'#effdff',boxShadow:'0 0 25px #65dcffbb,inset 0 0 16px #b18aff44'},{borderColor:'#564174',boxShadow:'0 0 0 transparent'}],{duration:1300,easing:'ease-out'});
    await flash.animate([{opacity:1,transform:'translate(-50%,-50%) scale(.2)'},{opacity:.8,offset:.18},{opacity:0,transform:'translate(-50%,-50%) scale(1.7)'}],{duration:480,easing:'ease-out'}).finished;
    flash.remove();effects.delete(flash);await glow.finished;
  }
  async function play(){
    if(busy||reduced.matches||document.hidden)return;
    busy=true;bot.disabled=true;bot.classList.remove('has-fired');
    const duration=2400/1.2,begin=performance.now();let fired=false,shot=Promise.resolve();
    // Те же 30 поз, прыжок быстрее на 20%. Скорость снаряда/частиц не масштабируется.
    try{
      await new Promise(resolve=>{
        cancelJump=resolve;
        function tick(now){
          const p=Math.min(1,(now-begin)/duration),n=Math.min(29,Math.floor(p*30));frame(n);
          const air=Math.min(1,Math.max(0,(p-.13)/.73));
          bot.style.transform=`translateY(${-86*4*air*(1-air)}px)`;
          if(n>=16&&!fired){fired=true;shot=shoot().catch(()=>{});}
          if(p<1&&!reduced.matches)raf=requestAnimationFrame(tick);
          else{frame(29);bot.style.transform='';if(fired)bot.classList.add('has-fired');resolve();}
        }
        raf=requestAnimationFrame(tick);
      });
      await shot;
    }finally{cancelJump=null;busy=false;bot.disabled=reduced.matches;bot.style.transform='';}
  }
  reduced.addEventListener('change',()=>{if(reduced.matches){cancelAnimationFrame(raf);cancelJump?.();frame(0);bot.style.transform='';effects.forEach(el=>el.remove());effects.clear();}bot.disabled=busy||reduced.matches;});
  bot.addEventListener('click',play);
  // Секунда спокойной стойки после загрузки, затем доступен клик, Enter и пробел.
  const ready=new Image();ready.onload=()=>{frame(0);setTimeout(()=>{bot.disabled=reduced.matches;bot.classList.add('is-ready');},1000);};ready.src='assets/doom-marine-30.png';
})();
