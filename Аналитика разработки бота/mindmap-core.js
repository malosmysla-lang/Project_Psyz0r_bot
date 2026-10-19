/* Pure layout/math shared by the interactive mind map, charts and tests. */
(function(root){
 'use strict';
 const palette=['#42e8dc','#b18aff','#42e8dc','#b18aff','#42e8dc','#b18aff','#42e8dc','#b18aff','#42e8dc','#b18aff','#42e8dc','#b18aff','#42e8dc','#b18aff','#42e8dc'];
 const clamp=(v,a,b)=>Math.min(b,Math.max(a,v));
 function bounds(nodes){
  if(!nodes.length)return{x:-120,y:-75,width:240,height:150};
  const left=Math.min(...nodes.map(n=>n.x-n.width/2)),top=Math.min(...nodes.map(n=>n.y-n.height/2));
  return{x:left,y:top,width:Math.max(...nodes.map(n=>n.x+n.width/2))-left,height:Math.max(...nodes.map(n=>n.y+n.height/2))-top};
 }
 function fit(rect,width,height,pad=48){
  const scale=clamp(Math.min(Math.max(50,width-2*pad)/Math.max(1,rect.width),Math.max(50,height-2*pad)/Math.max(1,rect.height)),.035,1.2);
  return{scale,x:width/2-(rect.x+rect.width/2)*scale,y:height/2-(rect.y+rect.height/2)*scale};
 }
 function zoom(view,factor,point){
  const scale=clamp(view.scale*factor,.035,2.5),wx=(point.x-view.x)/view.scale,wy=(point.y-view.y)/view.scale;
  return{scale,x:point.x-wx*scale,y:point.y-wy*scale};
 }
 function graph(registry,options={}){
  const expanded=new Set(options.expanded||[]),query=(options.query||'').trim().toLocaleLowerCase('ru'),status=options.status||'',positions=options.positions||{};
  const nodes=[{id:'root',type:'root',title:'Psyz0r',text:'Training Duel Bot',x:0,y:0,width:230,height:132,color:'#a5dce8'}],edges=[];
  const groups=registry.branches.map((b,index)=>{
   const matches=b.items.filter(r=>(!status||r.status.split('/')[0]===status)&&(!query||`${r.id} ${r.text} ${b.title}`.toLocaleLowerCase('ru').includes(query)));
   const open=(query||status)?matches.length>0:expanded.has(b.letter);
   return{b,index,matches,open,side:index<Math.ceil(registry.branches.length/2)?1:-1,height:open&&matches.length?Math.min(8,matches.length)*110+40:144};
  });
  for(const side of [-1,1]){
   const sideGroups=groups.filter(g=>g.side===side);let cursor=-sideGroups.reduce((n,g)=>n+g.height,0)/2;
   for(const g of sideGroups){
    const y=cursor+g.height/2,x=side*(540+Math.min(140,Math.abs(y)*.055)),color=palette[g.index%palette.length];
    const branch={id:'branch:'+g.b.letter,type:'branch',letter:g.b.letter,title:g.b.title,text:g.b.title,x,y,width:320,height:96,color,side,open:g.open,count:g.b.items.length,matching:g.matches.length,dimmed:!!(query||status)&&!g.matches.length};
    nodes.push(branch);edges.push({from:'root',to:branch.id,color});
    if(g.open)g.matches.forEach((r,i)=>{
     nodes.push({id:r.id,type:'rule',letter:g.b.letter,title:r.id,text:r.text,status:r.status,x:x+side*(480+Math.floor(i/8)*400),y:cursor+70+(i%8)*110,width:356,height:94,color,side,parent:branch.id});
     edges.push({from:branch.id,to:r.id,color});
    });
    cursor+=g.height;
   }
  }
  for(const n of nodes){const p=positions[n.id];if(p&&Number.isFinite(p.x)&&Number.isFinite(p.y)&&Math.abs(p.x)<1e6&&Math.abs(p.y)<1e6){n.x=p.x;n.y=p.y;}}
  return{nodes,edges,bounds:bounds(nodes),totalRules:registry.branches.reduce((n,b)=>n+b.items.length,0),visibleRules:nodes.filter(n=>n.type==='rule').length};
 }
 function edgePath(a,b){
  const direction=b.x>=a.x?1:-1,x1=a.x+direction*a.width/2,x2=b.x-direction*b.width/2;
  const bend=Math.max(85,Math.abs(x2-x1)*.48);
  return`M ${x1} ${a.y} C ${x1+direction*bend} ${a.y}, ${x2-direction*bend} ${b.y}, ${x2} ${b.y}`;
 }
 function histogram(values,limits){
  const bins=limits.slice(0,-1).map((lo,i)=>({lo,hi:limits[i+1],count:0}));
  for(const v of values){if(typeof v!=='number'||!Number.isFinite(v))continue;const index=bins.findIndex((b,i)=>v>=b.lo&&(v<b.hi||(i===bins.length-1&&v===b.hi)));if(index>=0)bins[index].count++;}
  return bins;
 }
 const api={palette,clamp,bounds,fit,zoom,graph,edgePath,histogram};root.PsyzMapCore=api;
 if(typeof module!=='undefined'&&module.exports)module.exports=api;
})(typeof window!=='undefined'?window:globalThis);
