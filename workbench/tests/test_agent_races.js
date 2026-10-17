'use strict';
// Run actual frontend functions with controlled network timing, without a server,
// model calls or persistent files. These cases protect workspace isolation.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const source=fs.readFileSync(path.join(__dirname,'../frontend/agent.js'),'utf8');
const tick=()=>new Promise(resolve=>setImmediate(resolve));
const deferred=()=>{let resolve,reject;const promise=new Promise((a,b)=>{resolve=a;reject=b;});return {promise,resolve,reject};};
const workspace=(id,extra={})=>({id,name:id,datasets:[],charts:[],messages:[],runs:[],...extra});
const chart=(id,session)=>({id,session,name:id,revision:1,job:null,project:{template:'basic.line',settings:{}}});
function setup(){
  const elements=new Map(),streams=[];
  function element(){return {value:'',textContent:'',hidden:false,disabled:false,inert:false,open:false,children:[],dataset:{},style:{},classList:{add(){},remove(){},toggle(){}},replaceChildren(...nodes){this.children=nodes;},append(...nodes){this.children.push(...nodes);},appendChild(node){this.children.push(node);},querySelectorAll(){return [];},querySelector(){return element();},setAttribute(){},addEventListener(){},close(){this.open=false;},showModal(){this.open=true;},focus(){},getBoundingClientRect(){return {};}};}
  const el=id=>{if(!elements.has(id))elements.set(id,element());return elements.get(id);};
  const env={console,crypto:require('node:crypto'),URLSearchParams,structuredClone,setTimeout,clearTimeout,setInterval(){},location:{origin:'http://127.0.0.1:8766',search:''},localStorage:{setItem(){},getItem(){}},history:{replaceState(){}},window:{addEventListener(){}},document:{getElementById:el,querySelectorAll:()=>[],createElement:element,addEventListener(){},body:element()},EventSource:class{constructor(url){this.url=url;this.handlers={};streams.push(this);}close(){this.closed=true;}addEventListener(name,fn){this.handlers[name]=fn;}}};
  vm.createContext(env);vm.runInContext(fs.readFileSync(path.join(__dirname,'../frontend/model-settings.js'),'utf8'),env);vm.runInContext(source.slice(0,source.lastIndexOf('init().catch')),env);
  const state=vm.runInContext('state',env);state.session=workspace('A');state.chart=chart('A1','A');
  env.paintWorkspace=()=>{};env.paintMessages=()=>{};env.paintRun=()=>{};env.status=()=>{};
  env.api=async()=>{throw Error('unexpected API call');};
  return {env,state,el,streams};
}
async function run(){
  let count=0;
  {
    const {env,state,el}=setup(),pending=deferred();let chartReads=0;
    el('binding-dialog').open=true;el('model-dialog').open=true;
    env.api=async url=>{if(url==='/api/agent/sessions/B')return pending.promise;chartReads++;throw Error(url);};
    const switching=env.openSession('B');await tick();
    assert.equal(state.sessionLoading,true);assert.equal(el('charts').inert,true);assert.equal(el('binding-dialog').open,false);assert.equal(el('model-dialog').open,true);
    assert.equal(state.chart.id,'A1','old editor is preserved until new workspace loads');
    await env.openChart('A1');assert.equal(chartReads,0,'old chart cannot open during switch');
    pending.resolve(workspace('B'));await switching;
    assert.equal(state.session.id,'B');assert.equal(state.chart,null);assert.equal(el('editor-host').hidden,true);assert.equal(state.sessionLoading,false);count++;
  }
  {
    const {env,state,el}=setup(),pending=deferred();
    env.api=async url=>url.includes('/charts/')?pending.promise:workspace(url.split('/').at(-1));
    const opening=env.openChart('A1');await tick();
    assert.equal(el('editor-host').inert,true,'freeze old canvas after save while another chart is loading');
    await env.openSession('B');await env.openSession('A');pending.resolve(chart('A1','A'));await opening;
    assert.equal(state.session.id,'A');assert.equal(state.chart,null,'late chart response must not cross a leave-and-return');assert.equal(el('editor-host').inert,false);count++;
  }
  {
    const {env,state,el,streams}=setup(),pending=deferred();let payload;
    env.api=async(url,data)=>{if(url==='/api/agent/sessions/A/runs'){payload=data;return pending.promise;}return workspace(url.split('/').at(-1));};
    el('prompt').value='修改 A 图';state.target='current';
    const submit=el('composer').onsubmit({preventDefault(){}});await tick();
    assert.equal(payload.chart_id,'A1');await env.openSession('B');el('prompt').value='B 的新要求';
    pending.resolve({id:'run-A',session:'A',status:'running',body:{}});await submit;
    assert.equal(state.session.id,'B');assert.equal(state.run,null);assert.equal(el('prompt').value,'B 的新要求');assert.equal(streams.length,0);assert.equal(state.submitting,false);count++;
  }
  {
    const {env,state,el}=setup(),pending=deferred();let first=true,posts=0;
    env.flush=()=>{if(first){first=false;return pending.promise;}return Promise.resolve();};
    env.api=async(url,data)=>{if(data)posts++;return workspace(url.split('/').at(-1));};
    el('prompt').value='修改 A 图';const submit=el('composer').onsubmit({preventDefault(){}});await tick();
    await env.openSession('B');pending.resolve();await submit;
    assert.equal(state.session.id,'B');assert.equal(posts,0,'switch during save must not submit old text to new workspace');count++;
  }
  {
    const {env,state}=setup(),pending=deferred();let first=true;
    env.api=async url=>{if(first){first=false;return pending.promise;}return workspace(url.split('/').at(-1));};
    const refresh=env.refreshSession();await tick();await env.openSession('B');await env.openSession('A');
    pending.resolve(workspace('A',{name:'stale'}));await refresh;
    assert.equal(state.session.name,'A','old refresh must not replace a later visit to same workspace');count++;
  }
  {
    const {env,state}=setup(),pending=deferred();
    state.pending={project:{version:'first'},job:null};env.api=()=>pending.promise;
    const saving=env.flush();await tick();state.pending={project:{version:'latest'},job:null};pending.reject(Error('offline'));
    await assert.rejects(saving,/offline/);assert.equal(state.pending.project.version,'latest','failed save must not overwrite newer unsaved edits');count++;
  }
  {
    const {env,state}=setup(),pending=deferred();
    env.api=async url=>url.endsWith('/B')?pending.promise:workspace('C');
    const first=env.openSession('B');await tick();await env.openSession('C');pending.resolve(workspace('B'));await first;
    assert.equal(state.session.id,'C');assert.equal(state.sessionLoading,false);count++;
  }
  {
    const {env,state,el}=setup();env.api=async()=>{throw Error('offline');};
    await assert.rejects(env.openSession('B'),/offline/);
    assert.equal(state.session.id,'A');assert.equal(state.chart.id,'A1');assert.equal(el('sessions').value,'A');assert.equal(el('editor-host').inert,false);count++;
  }
  console.log(`Agent asynchronous workspace checks: ${count} passed.`);
}
run().catch(error=>{console.error(error);process.exitCode=1;});
