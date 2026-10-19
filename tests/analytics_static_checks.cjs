// Exercise the offline UI renderer without a browser or external dependency.
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.join(__dirname,'..','Аналитика разработки бота'),nodes={};
const context={window:{},document:{querySelector(s){return nodes[s]??=( {value:'',innerHTML:'',textContent:'',addEventListener(){}} );},querySelectorAll(){return []}}};
vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(root,'data.js'),'utf8'),context);
vm.runInContext(fs.readFileSync(path.join(root,'app.js'),'utf8'),context);
const data=context.window.PSYZ_ANALYTICS;
// Проверяем настоящие HTML-цели: mock DOM не должен скрывать опечатку в id.
const html=fs.readFileSync(path.join(root,'index.html'),'utf8');
for(const selector of Object.keys(nodes))if(/^#[\w-]+$/.test(selector))assert(html.includes(`id="${selector.slice(1)}"`),selector);
if(data.tactical){
 assert.equal(data.tactical.parsed,500);
 assert(nodes['#comboCharts'].innerHTML.includes(String(data.tactical.multi_weapon_before_kill)));
 assert(nodes['#anchorRows'].innerHTML.includes(String(data.tactical.aim_anchors[0].yaw_deg)));
 assert(nodes['#cycleCharts'].innerHTML.includes('red'));
}
for(const b of data.registry.branches)for(const r of b.items)assert(nodes['#branches'].innerHTML.includes(`<code>${r.id}</code>`),r.id);
assert(nodes['#ruleCount'].textContent.includes(String(data.registry.rule_count)));
vm.runInContext("$('#search').value='A01';renderRules()",context);
assert(nodes['#branches'].innerHTML.includes('<code>A01</code>'));
assert(!nodes['#branches'].innerHTML.includes('<code>A02</code>'));
vm.runInContext("$('#search').value='';$('#status').value='LOCAL';renderRules()",context);
assert(!nodes['#branches'].innerHTML.includes('<code>A01</code>'));
assert(vm.runInContext("esc('<img src=x onerror=alert(1)>')",context).startsWith('&lt;img'));
for(const src of [...fs.readFileSync(path.join(root,'index.html'),'utf8').matchAll(/(?:src|href)="([^"]+)"/g)].map(x=>x[1]))if(!src.startsWith('#')&&!src.startsWith('http'))assert(fs.existsSync(path.resolve(root,decodeURI(src))),src);
console.log('Offline dashboard: full rule coverage, search, status filtering, escaping, asset links passed');
const exported=path.join(root,'Psyz0r_Analytics_0_7_8.html');
if(fs.existsSync(exported)){
 const html=fs.readFileSync(exported,'utf8');
 assert(!html.includes('<script src=')&&!html.includes('<link rel="stylesheet"'));
 const standalone={window:{},document:context.document};vm.createContext(standalone);
 for(const match of html.matchAll(/<script>([\s\S]*?)<\/script>/g))vm.runInContext(match[1],standalone);
 assert.equal(standalone.window.PSYZ_ANALYTICS.registry.rule_count,data.registry.rule_count);
 assert.equal(standalone.window.PSYZ_ANALYTICS.winnerAccuracy.table.find(x=>x.weapon_id===2).mean_match_accuracy,29.9);
 console.log('Standalone HTML: embedded scripts executed; current rules and MG statistic verified');
}
