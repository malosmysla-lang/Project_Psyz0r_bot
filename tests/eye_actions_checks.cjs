const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
let reloads=0,animations=[],timers=new Map(),next=0;
class El{constructor(){this.events={};}append(){}setAttribute(){}addEventListener(n,f){this.events[n]=f;}querySelector(){return new El();}animate(keys,options){animations.push({keys,options});return{finished:Promise.resolve(),cancel(){}};}}
const eye=new El(),home=new El();
const context=vm.createContext({document:{body:{animate(){}},hidden:false,querySelector:s=>s==='#brandHome'?home:eye,createElement:()=>new El(),addEventListener(){}},window:{location:{reload:()=>reloads++}},matchMedia:()=>({matches:false,addEventListener(){}}),setTimeout:(f,d)=>{timers.set(++next,{f,d});return next;},clearTimeout:id=>timers.delete(id),Math,Promise});
(async()=>{
 vm.runInContext(fs.readFileSync(path.resolve(__dirname,'../Аналитика разработки бота/eye-blink.js'),'utf8'),context);
 assert.equal(timers.size,1);assert.ok([...timers.values()][0].d>=6000&&[...timers.values()][0].d<=8000);
 const blink=eye.events.click();eye.events.click();assert.equal(animations.length,2,'Repeated clicks must not overlap');
 await blink;assert.ok(animations.every(a=>a.keys.length===12));assert.equal(reloads,0,'Eye must not navigate');assert.equal(timers.size,1);
 let prevented=false;home.events.click({preventDefault(){prevented=true;}});assert.equal(reloads,1);assert.ok(prevented);
 console.log('Eye actions: click blink, 12 positions, overlap guard, 6–8s scheduling and separate brand reload passed');
})().catch(e=>{console.error(e);process.exitCode=1;});
