/* Тридцать поз персонажа. Прыжок по кнопке; дым и ракета имеют собственные часы. */
(() => {
  const heading=document.querySelector('.headline h1'),target=document.querySelector('.headline .release');
  if(!heading||!target||!document.body?.animate)return;
  heading.classList.add('mascot-heading');
  const bot=document.createElement('button');bot.type='button';bot.className='bot-mascot';bot.disabled=true;
  bot.setAttribute('aria-label','Запустить анимацию персонажа');
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
  function puff(x,y,index,heavy=false){
    const el=document.createElement('span');el.className='rocket-smoke-puff';el.setAttribute('aria-hidden','true');
    const size=heavy?15+index%7:10+index%5;
    el.style.cssText=`left:${x}px;top:${y}px;width:${size}px;height:${size}px`;
    document.body.append(el);effects.add(el);
    const drift=(index%2?1:-1)*(5+index%7);
    el.animate([{opacity:heavy?.6:.5,transform:'translate(-50%,-50%) scale(.4)'},{opacity:heavy?.45:.32,offset:.2},{opacity:0,transform:`translate(${drift*1.8}px,${-25-index%28}px) scale(${heavy?5:4})`}],{duration:(heavy?1550:1100)+index%5*110,easing:'ease-out'}).finished.finally(()=>{el.remove();effects.delete(el);});
  }
  async function shoot(){
    if(reduced.matches)return;
    const b=bot.getBoundingClientRect(),t=target.getBoundingClientRect();
    const start={x:b.right-3,y:b.top+b.height*.25},end={x:t.left+2,y:t.top+18};
    const dx=end.x-start.x,dy=end.y-start.y,angle=Math.atan2(dy,dx)*180/Math.PI;
    // Постоянная скорость полёта; длительность зависит от расстояния в текущей раскладке.
    const duration=Math.min(1100,Math.max(450,Math.hypot(dx,dy)/1.35));
    const rocket=document.createElement('span');rocket.className='mascot-rocket';rocket.setAttribute('aria-hidden','true');
    rocket.innerHTML='<i class="rocket-blue-core"></i>';
    rocket.style.cssText=`left:${start.x}px;top:${start.y}px`;document.body.append(rocket);effects.add(rocket);
    // Отдельный широкий источник света движется вместе со снарядом и освещает фон пути.
    const light=document.createElement('span');light.className='rocket-path-light';light.setAttribute('aria-hidden','true');
    light.style.cssText=`left:${start.x-22}px;top:${start.y}px`;document.body.append(light);effects.add(light);
    light.animate([{transform:'translate(-50%,-50%)'},{transform:`translate(calc(-50% + ${dx}px),calc(-50% + ${dy}px))`}],{duration,easing:'linear',fill:'forwards'});
    sprite.animate([{transform:'translateX(0)'},{transform:'translateX(-4px)',offset:.2},{transform:'translateX(0)'}],{duration:180});
    const begin=performance.now();let last=-1;
    function trail(now){
      if(!rocket.isConnected)return;
      const p=Math.min(1,(now-begin)/duration),segment=Math.floor(p*48);
      // Заполняем пропущенные сегменты при редком repaint — след остаётся непрерывным.
      for(let i=last+1;i<=segment;i++){const q=i/48;puff(start.x+dx*q,start.y+dy*q,i);}
      last=segment;
      if(p<1)requestAnimationFrame(trail);
    }
    requestAnimationFrame(trail);
    await rocket.animate([{transform:`translate(0,-50%) rotate(${angle}deg)`},{transform:`translate(${dx}px,${dy}px) rotate(${angle}deg)`}],{duration,easing:'linear',fill:'forwards'}).finished;
    rocket.remove();effects.delete(rocket);light.remove();effects.delete(light);if(reduced.matches)return;
    const flash=document.createElement('span');flash.className='mascot-impact';flash.setAttribute('aria-hidden','true');
    flash.style.cssText=`left:${end.x}px;top:${end.y}px`;document.body.append(flash);effects.add(flash);
    // Несколько слоёв взрыва: горячее ядро, ударное кольцо, обломки и тяжёлый дым.
    const ring=document.createElement('span');ring.className='explosion-ring';ring.setAttribute('aria-hidden','true');
    ring.style.cssText=`left:${end.x}px;top:${end.y}px`;document.body.append(ring);effects.add(ring);
    ring.animate([{opacity:.95,transform:'translate(-50%,-50%) scale(.15)'},{opacity:0,transform:'translate(-50%,-50%) scale(2.5)'}],{duration:650,easing:'ease-out'}).finished.finally(()=>{ring.remove();effects.delete(ring);});
    for(let i=0;i<36;i++){
      const a=i*2.399963,reach=42+(i%7)*14;
      const shard=document.createElement('span');shard.className='explosion-shard';shard.setAttribute('aria-hidden','true');
      shard.style.cssText=`left:${end.x}px;top:${end.y}px;width:${3+i%5}px;height:${i%2?3:8}px;clip-path:polygon(0 20%,70% 0,100% 65%,30% 100%)`;
      document.body.append(shard);effects.add(shard);
      const x=Math.cos(a)*reach,y=Math.sin(a)*reach;
      shard.animate([{opacity:1,backgroundColor:'#fff2b5',transform:'translate(0,0) rotate(0deg)'},{opacity:1,backgroundColor:'#ff9d47',offset:.3,transform:`translate(${x*.65}px,${y*.65}px) rotate(${i*31}deg)`},{opacity:.7,backgroundColor:'#616876',offset:.72},{opacity:0,backgroundColor:'#253140',transform:`translate(${x}px,${y+65}px) rotate(${i*113}deg)`}],{duration:750+i%7*95,easing:'ease-out'}).finished.finally(()=>{shard.remove();effects.delete(shard);});
    }
    for(let i=0;i<28;i++)puff(end.x+(i%7-3)*10,end.y+(Math.floor(i/7)-1.5)*12,i,true);
    // Огненный шар распадается на отдельные всплески, а не просто исчезает кругом.
    for(let i=0;i<8;i++){
      const lobe=document.createElement('span');lobe.className='explosion-lobe';lobe.setAttribute('aria-hidden','true');
      lobe.style.cssText=`left:${end.x}px;top:${end.y}px;width:${24+i%3*10}px;height:${24+i%3*10}px`;
      document.body.append(lobe);effects.add(lobe);const a=i*Math.PI/4;
      lobe.animate([{opacity:.9,transform:'translate(-50%,-50%) scale(.2)'},{opacity:.85,offset:.25},{opacity:0,transform:`translate(${Math.cos(a)*48-20}px,${Math.sin(a)*43-20}px) scale(1.6)`}],{duration:520+i%3*100,easing:'ease-out'}).finished.finally(()=>{lobe.remove();effects.delete(lobe);});
    }
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
