"use strict";
// Exercise the actual settings handler: language switching updates settings,
// schedules a render and leaves uploaded data intact.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname, '../frontend/editor.js'), 'utf8');
const html = fs.readFileSync(path.join(__dirname, '../editor.html'), 'utf8');
const beginning = source.indexOf("document.querySelector('.settings-panel').addEventListener('change'");
const ending = source.indexOf("document.querySelector('.settings-panel').addEventListener('focusin'", beginning);
const data = {headers:['地区','销量'],rows:[['North',12],['South',20]]};
let change, renders=0, checkpoints=0;
const env = {project:{settings:{language:'zh',palette:'pastel-girl'},table:structuredClone(data)},
  document:{querySelector(){return {addEventListener(type,handler){assert.equal(type,'change');change=handler;}};}},
  remember(){checkpoints++;},fillSettings(){},queueLiveRender(){renders++;},changed(){}};
vm.createContext(env);vm.runInContext(source.slice(beginning, ending),env);
change({target:{dataset:{setting:'language'},tagName:'SELECT',value:'en'}});
assert.equal(env.project.settings.language,'en');assert.equal(renders,1);
assert.deepEqual(env.project.table,data);assert.equal(checkpoints,1);
change({target:{dataset:{setting:'language'},tagName:'SELECT',value:'zh'}});
assert.equal(env.project.settings.language,'zh');assert.equal(renders,2);assert.deepEqual(env.project.table,data);
assert.match(html, /data-setting="language"[^>]*>[\s\S]*?<option value="zh">中文（默认）<\/option><option value="en">English<\/option>/);

const language={dataset:{setting:'language'},tagName:'SELECT',value:''};
const elements={'zlabel-row':{},'palette-swatches':{}};
env.document.querySelectorAll=()=>[language];env.$=id=>elements[id];env.is3D=()=>false;env.palettes={};
delete env.project.settings.language;
vm.runInContext(source.slice(source.indexOf('function fillSettings(){'),source.indexOf('function refresh(){')),env);
env.fillSettings();assert.equal(language.value,'zh');
console.log('Editor language checks passed: switching, live render, source data preservation and old-draft defaults.');
