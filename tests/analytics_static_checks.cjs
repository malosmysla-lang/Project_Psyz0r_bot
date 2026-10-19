// Exercise the offline UI renderer without a browser or external dependency.
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.join(__dirname,'..','Аналитика разработки бота'),nodes={};
const context={window:{},document:{querySelector(s){return nodes[s]??=( {value:'',innerHTML:'',textContent:'',addEventListener(){}} );},querySelectorAll(){return []}}};
vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(root,'data.js'),'utf8'),context);
vm.runInContext(fs.readFileSync(path.join(root,'app.js'),'utf8'),context);
vm.runInContext(fs.readFileSync(path.join(root,'research079.js'),'utf8'),context);
vm.runInContext(fs.readFileSync(path.join(root,'version-history.js'),'utf8'),context);
vm.runInContext(fs.readFileSync(path.join(root,'mindmap-core.js'),'utf8'),context);
vm.runInContext(fs.readFileSync(path.join(root,'mindmap.js'),'utf8'),context);
vm.runInContext(fs.readFileSync(path.join(root,'duels.js'),'utf8'),context);
const data=context.window.PSYZ_ANALYTICS;
if(data.duelLedger){
 assert(data.duelLedger.matches.filter(r=>r.actor==='Psyz0r').length>=7,'published ledger preserves historical matches and accepts new completed matches');
 assert(nodes['#duelRows'].innerHTML.includes('4:9'));
 assert.equal(context.window.PsyzDuelModel.comparable(context.window.PsyzDuelModel.select('Psyz0r','')).automatic_learning,false);
}
if(data.research079){
 assert.equal(data.research079.parsed,200);
 assert(nodes['#reserveSummary'].textContent.includes('700'));
 assert(nodes['#cohortRows'].innerHTML.includes('27.46%'));
 for(const bins of Object.values(data.research079.histograms))assert.equal(bins.length,10);
}
if(data.versionHistory){
 assert.equal(data.versionHistory.length,4);
 vm.runInContext("$('#versionSelect').value='0.7.7';$('#metricSelect').value='rules';renderHistory()",context);
 assert(nodes['#versionTitle'].textContent.includes('0.7.7'));
 assert(nodes['#versionNote'].textContent.includes('live'));
}
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
const exported=path.join(root,fs.existsSync(path.join(root,'Pracc_Room_Server_Analytics.html'))?'Pracc_Room_Server_Analytics.html':'Psyz0r_Analytics_0_7_8.html');
if(fs.existsSync(exported)){
 const html=fs.readFileSync(exported,'utf8');
 assert(!html.includes('<script src=')&&!html.includes('<link rel="stylesheet"'));
 const standalone={window:{},document:context.document};vm.createContext(standalone);
 for(const match of html.matchAll(/<script>([\s\S]*?)<\/script>/g))vm.runInContext(match[1],standalone);
 assert.equal(standalone.window.PSYZ_ANALYTICS.registry.rule_count,data.registry.rule_count);
 assert.equal(standalone.window.PSYZ_ANALYTICS.winnerAccuracy.table.find(x=>x.weapon_id===2).mean_match_accuracy,29.9);
 console.log('Standalone HTML: embedded scripts executed; current rules and MG statistic verified');
}
const portable=path.join(root,'Поделиться','Pracc_Room_Server_BOT.html');
if(fs.existsSync(portable)){
 const html=fs.readFileSync(portable,'utf8'),mobile={window:{},document:context.document};vm.createContext(mobile);
 for(const match of html.matchAll(/<script>([\s\S]*?)<\/script>/g))vm.runInContext(match[1],mobile);
 assert.equal(mobile.window.PSYZ_ANALYTICS.registry.rule_count,data.registry.rule_count);
 assert.equal(mobile.window.PSYZ_ANALYTICS.versionHistory.length,4);
 assert.deepEqual(Object.keys(mobile.window.PSYZ_ANALYTICS.deployment),['version']);
 for(const src of [...html.matchAll(/\bsrc="([^"]+)"/g)].map(x=>x[1]))assert(src.startsWith('data:'),src);
 console.log('Portable phone HTML: scripts, four releases, embedded assets and stripped admin state passed');
}
