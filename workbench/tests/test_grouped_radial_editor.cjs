'use strict';
// Exercise the actual editor mapping renderer, including its currently active sheet.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const source=fs.readFileSync(path.join(__dirname,'../frontend/editor.js'),'utf8');
const elements=new Map();
const el=id=>{if(!elements.has(id))elements.set(id,{innerHTML:'',hidden:false});return elements.get(id);};
const env={URLSearchParams,location:{search:''},window:{},document:{getElementById:el,querySelectorAll:()=>[]},fieldChips(){}};
vm.createContext(env);
vm.runInContext(source.slice(0,source.indexOf("$('add-row').onclick")),env);
env.inputSpec={family:'catalog',tables:[{key:'scores',kind:'matrix',headers:['任务','模型甲','模型乙']},{key:'labels',kind:'columns',headers:['任务','大类','说明']}]};
const p={template:'advanced.grouped_radial_bar',active_table:'scores',mapping:{},settings:{highlight:1,palette:'pastel-girl'},tables:{scores:{headers:['任务','旧名称甲','旧名称乙'],rows:[['任务一',1,2]]},labels:{headers:['任务','大类','说明'],rows:[['任务一','某类','说明']]}}};
p.table={headers:['任务','已改名甲','模型乙'],rows:[['任务一',1,2]]};
function render(input){env.input=input;vm.runInContext('project=input;spec=inputSpec;palettes={};mappingRender();',env);return el('specific-fields').innerHTML;}
let html=render(p);
assert.match(html,/<select data-setting="highlight">/);
assert.match(html,/<option value="0">已改名甲<\/option><option value="1">模型乙<\/option>/);
assert.doesNotMatch(html,/旧名称/,'active scores must use the current edited sheet');
p.tables.scores={headers:['任务','模型丙','模型甲','模型乙'],rows:[['任务一',3,1,2]]};
p.column_mappings={scores:[2,5,1,4],labels:[0,1,2]};
p.active_table='labels';p.table=p.tables.labels;
html=render(p);
assert.match(html,/<option value="0">模型丙<\/option><option value="1">模型甲<\/option><option value="2">模型乙<\/option>/);
assert.doesNotMatch(html,/>大类<|>说明</,'metadata columns are not model choices');
p.tables.scores.headers[1]='模型 <甲> & 乙';
assert.match(render(p),/模型 &lt;甲&gt; &amp; 乙/,'model names must be escaped');
console.log('Grouped radial editor: 3 checks passed (active sheet, projected order, escaping).');
