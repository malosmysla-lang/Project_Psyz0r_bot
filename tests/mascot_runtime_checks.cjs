// Exercise the real scene with a deterministic animation clock, without a browser.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),path=require('node:path');
const root=path.resolve(__dirname,'../Аналитика разработки бота');
let now=0,id=0,queue=[],nodes=[],draws=new Set();
const schedule=(fn,delay)=>{queue.push({id:++id,t:now+delay,fn});return id;};
class Element{
 constructor(tag='span'){this.tag=tag;this.style={};this.listeners={};this.className='';this.isConnected=true;this.children=[];this.classes=new Set();this.classList={add:n=>this.classes.add(n),remove:n=>this.classes.delete(n)};nodes.push(this);}
 setAttribute(){} append(n){this.children.push(n);} prepend(n){this.children.unshift(n);}get firstChild(){return null;}
 set innerHTML(s){this.html=s;}querySelector(s){return this.cache?.[s]||(this.cache??={},this.cache[s]=new Element(s.includes('canvas')?'canvas':'span'));}
 addEventListener(n,f){this.listeners[n]=f;}remove(){this.isConnected=false;}
 getBoundingClientRect(){return this.className==='bot-mascot'?{left:300,right:405,top:80,height:140}:{left:1100,top:60};}
 getContext(){return{clearRect(){},drawImage:(image,x,y)=>draws.add(x+','+y)};}
 animate(keys,options){const a={keys,options,finished:new Promise(resolve=>schedule(resolve,options.duration)),cancel(){}};return a;}
}
const heading=new Element(),target=new Element(),body=new Element();
const document={hidden:false,body,querySelector:s=>s.includes('h1')?heading:target,createElement:t=>new Element(t),addEventListener(){}};
const context=vm.createContext({document,matchMedia:()=>({matches:false,addEventListener(){}}),performance:{now:()=>now},setTimeout:schedule,clearTimeout:i=>{queue=queue.filter(x=>x.id!==i);},requestAnimationFrame:f=>schedule(()=>f(now),16),cancelAnimationFrame:i=>{queue=queue.filter(x=>x.id!==i);},Image:class{set src(v){this.complete=true;this.naturalWidth=1374;schedule(()=>this.onload(),0);}}});
async function advance(until){for(let guard=0;guard<10000;guard++){queue.sort((a,b)=>a.t-b.t);if(!queue.length||queue[0].t>until)break;const task=queue.shift();now=task.t;task.fn();await Promise.resolve();await Promise.resolve();}now=until;await Promise.resolve();}
(async()=>{
 vm.runInContext(fs.readFileSync(path.join(root,'bot-mascot.js'),'utf8'),context);
 await advance(1200);const bot=nodes.find(n=>n.className==='bot-mascot');assert.equal(bot.disabled,false);
 assert.equal(nodes.filter(n=>n.className==='mascot-rocket').length,0,'No automatic shot');
 bot.listeners.click();await advance(6000);
 assert.equal(draws.size,30,'All 30 source poses shown');assert.equal(nodes.filter(n=>n.className==='mascot-rocket').length,1);
 assert.equal(nodes.filter(n=>n.className==='explosion-shard').length,18);assert.ok(nodes.filter(n=>n.className==='rocket-smoke-puff').length>30);
 assert.equal(bot.disabled,false);assert.ok(bot.classes.has('has-fired'));assert.ok(!nodes.some(n=>n.className==='mascot-rocket'&&n.isConnected));
 console.log('Scene runtime: click-only, 30 poses, rocket, smoke, 18 shards, cleanup and replay readiness passed');
})().catch(e=>{console.error(e);process.exitCode=1;});
