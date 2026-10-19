// Exercise the offline UI renderer without a browser or external dependency.
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.join(__dirname,'..','Аналитика разработки бота'),nodes={};
const context={window:{},document:{querySelector(s){return nodes[s]??=( {value:'',innerHTML:'',textContent:'',addEventListener(){}} );},querySelectorAll(){return []}}};
vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(root,'data.js'),'utf8'),context);
vm.runInContext(fs.readFileSync(path.join(root,'app.js'),'utf8'),context);
const data=context.window.PSYZ_ANALYTICS;
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
