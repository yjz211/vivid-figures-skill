'use strict';
const el=id=>document.getElementById(id),escapeHTML=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const state={token:'',session:null,chart:null,catalog:null,view:'',frame:null,selected:'',run:null,events:null,pending:null,saveChain:Promise.resolve(),saveTimer:null,conflict:false,ready:false,viewData:null,config:null,saving:false,openRequest:0,sessionRequest:0,sessionLoading:false,submissionRequest:0,dataset:'',target:'new',submitting:false};
let toastTimer;
function toast(message){el('toast').textContent=message;el('toast').hidden=false;clearTimeout(toastTimer);toastTimer=setTimeout(()=>el('toast').hidden=true,6000);}
async function api(path,data){
  const r=await fetch(path,{method:data===undefined?'GET':'POST',headers:data===undefined?{}:{'Content-Type':'application/json','X-Vivid-Token':state.token},body:data===undefined?undefined:JSON.stringify(data)});
  const value=await r.json();if(!r.ok){const error=new Error(value.error?.message||'请求未完成');error.status=r.status;throw error;}return value;
}
function safely(fn){return async(...args)=>{try{return await fn(...args);}catch(e){toast(e.message);}};}
function bridge(){return state.frame?.contentWindow?.VividBridge;}
function status(text){el('save-state').textContent=text;bridge()?.status(text);}
function showDialog(id){el(id).showModal();}
function workspaceContext(){return {id:state.session?.id,request:state.sessionRequest};}
function sameWorkspace(context){return !state.sessionLoading&&context.id===state.session?.id&&context.request===state.sessionRequest;}
function workspaceLoading(value){
  state.sessionLoading=value;
  for(const id of ['datasets','charts','messages','composer','editor-host','empty-state'])el(id).inert=value;
  for(const id of ['upload','import-main','gallery-open','new-session'])el(id).disabled=value;
  for(const id of ['version-open','branch-chart'])el(id).disabled=value||!state.chart;
  paintRun(state.run);
}
document.querySelectorAll('[data-close]').forEach(b=>b.onclick=()=>el(b.dataset.close).close());
document.querySelectorAll('dialog').forEach(d=>d.addEventListener('click',e=>{if(e.target===d){const r=d.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)d.close();}}));

async function sessionList(){
  const {items}=await api('/api/agent/sessions');el('sessions').innerHTML=items.map(s=>`<option value="${s.id}">${escapeHTML(s.name)}</option>`).join('');
  if(state.session)el('sessions').value=state.session.id;return items;
}
function paintWorkspace(){
  const s=state.session;if(!s)return;
  el('datasets').innerHTML=s.datasets.map(d=>`<button class="rail-item ${d.id===state.dataset?'active':''}" data-dataset="${d.id}">▤ ${escapeHTML(d.name)}<small>${d.table.rows.length} 行 × ${d.table.headers.length} 列</small></button>`).join('')||'<small class="dialog-hint">还没有导入数据</small>';
  el('charts').innerHTML=s.charts.map(c=>`<button class="rail-item ${state.chart?.id===c.id?'active':''}" data-chart="${c.id}">▧ ${escapeHTML(c.name)}<small>版本 ${c.head}</small></button>`).join('')||'<small class="dialog-hint">从模板或对话创建</small>';
  el('datasets').querySelectorAll('[data-dataset]').forEach(b=>b.onclick=()=>openDataset(b.dataset.dataset));
  el('charts').querySelectorAll('[data-chart]').forEach(b=>b.onclick=safely(()=>openChart(b.dataset.chart)));
  el('chart-heading').textContent=state.chart?.name||'开始一张新图';el('revision-badge').textContent=state.chart?'v'+state.chart.revision:'';
  for(const id of ['version-open','branch-chart'])el(id).disabled=state.sessionLoading||!state.chart;
  el('dataset-summary').textContent=s.datasets.length?`${s.datasets.length} 张数据表 · ${s.charts.length} 张图表`:`${state.catalog?.cards?.length??148} 个模板 · 7 套配色`;
  if(state.dataset&&!s.datasets.some(d=>d.id===state.dataset))state.dataset='';
  if(!state.chart)state.target='new';
  el('task-target').value=state.target;el('task-target').querySelector('[value="current"]').disabled=!state.chart;
  el('task-dataset').innerHTML='<option value="">'+(state.target==='current'?'沿用图中数据':'工作区全部数据')+'</option>'+s.datasets.map(d=>`<option value="${d.id}">${escapeHTML(d.name)}</option>`).join('');el('task-dataset').value=state.dataset;
  el('context-chip').textContent=state.target==='new'?'＋ 另存一张新图':state.selected?'⌖ '+state.selected:'▧ '+state.chart?.name;
  el('clear-selection').hidden=!state.selected||state.target==='new';
}
function paintMessages(){
  const messages=state.session.messages;
  el('messages').innerHTML=messages.length?messages.map(m=>{
    const b=m.body,review=b.review,rev=b.result?.revision;return `<article class="message ${m.role}"><span class="message-label">${m.role==='user'?'YOU / 你':'VIVID'}</span><p>${escapeHTML(b.text)}</p>${review?`<div class="review-summary">${review.visual?'◈ 图片检查':'✓ 数据与执行检查'}${rev?' · 当时版本 v'+rev:''} · ${escapeHTML(review.summary)}${review.issues?.length?'<br>'+review.issues.map(escapeHTML).join('<br>'):''}</div>`:''}${b.result?.chart_id?`<button class="result-link" data-result-chart="${b.result.chart_id}">▧ 打开此图（当前版本）</button>`:''}${b.result?.conflict?`<button class="result-link" data-candidate="${b.run_id}">⑂ 保留候选图为新图</button>`:''}</article>`;
  }).join(''):'<div class="assistant intro-message"><span class="message-label">VIVID</span><p>告诉我你想表达什么。\n我会沿用现有模板绘图；你也可以随时直接编辑画布。</p></div>';
  el('messages').querySelectorAll('[data-result-chart]').forEach(b=>b.onclick=safely(()=>openChart(b.dataset.resultChart)));
  el('messages').querySelectorAll('[data-candidate]').forEach(b=>b.onclick=safely(async()=>{const context=workspaceContext(),c=await api('/api/agent/runs/'+b.dataset.candidate+'/candidate',{});await showCreatedChart(c,context);}));
  el('messages').scrollTop=el('messages').scrollHeight;
}
async function refreshSession(){const context=workspaceContext(),s=await api('/api/agent/sessions/'+context.id);if(!sameWorkspace(context))return;state.session=s;paintWorkspace();paintMessages();}
async function showCreatedChart(chart,context,options){if(!sameWorkspace(context))return;await refreshSession();if(sameWorkspace(context))await openChart(chart.id,options);}
async function openSession(id){
  const request=++state.sessionRequest;let switched=false;
  state.openRequest++;state.submissionRequest++;state.submitting=false;workspaceLoading(true);
  for(const name of ['dataset-dialog','gallery-dialog','binding-dialog','versions-dialog','sheet-dialog'])if(el(name).open)el(name).close();
  try{
    await flush();if(state.conflict)throw Error('请先保留当前手动修改。');
    if(request!==state.sessionRequest)return;
    // Keep the old editor intact until the requested workspace is available.
    const session=await api('/api/agent/sessions/'+id);if(request!==state.sessionRequest)return;
    state.events?.close();state.events=null;state.run=null;state.chart=null;state.selected='';state.frame=null;state.pending=null;state.ready=false;state.dataset='';state.target='new';state.viewData=null;
    el('editor-host').replaceChildren();el('editor-host').hidden=true;el('empty-state').hidden=false;el('activity').hidden=true;el('run-notice').hidden=true;
    state.session=session;switched=true;localStorage.setItem('vivid-agent-session',id);history.replaceState(null,'','agent.html?session='+encodeURIComponent(id));el('sessions').value=id;paintWorkspace();paintMessages();
    workspaceLoading(false);
    const last=state.session.charts.at(-1);if(last)await openChart(last.id);
    if(request!==state.sessionRequest)return;
    const run=state.session.runs.find(r=>['queued','running','waiting','interrupted'].includes(r.status));
    if(run){state.run=run;connectEvents(run.id);paintRun(run);}else paintRun(null);
  }finally{if(request===state.sessionRequest){workspaceLoading(false);if(state.session)el('sessions').value=state.session.id;if(!switched&&state.run&&['queued','running'].includes(state.run.status))connectEvents(state.run.id);}}
}
async function openChart(id,{skipFlush=false}={}){
  if(state.sessionLoading)return;
  const request=++state.openRequest,context=workspaceContext();
  el('editor-host').inert=true;
  try{
    if(!skipFlush)await flush();if(state.conflict)throw Error('请先将尚未保存的手动修改另存。');
    if(!sameWorkspace(context)||request!==state.openRequest)return;
    const c=await api('/api/agent/charts/'+id);if(!sameWorkspace(context)||request!==state.openRequest||c.session!==context.id)return;
    state.ready=false;state.pending=null;state.selected='';state.chart=c;state.target='current';state.view=crypto.randomUUID();
    el('empty-state').hidden=true;el('editor-host').hidden=false;const frame=document.createElement('iframe');frame.title='可交互绘图编辑器';
    frame.src='editor.html?embed=1&template='+encodeURIComponent(state.chart.project.template)+'&view='+state.view;
    state.frame=frame;el('editor-host').replaceChildren(frame);paintWorkspace();status('正在载入图表…');
  }finally{if(request===state.openRequest&&!state.sessionLoading)el('editor-host').inert=false;}
}
window.addEventListener('message',safely(async e=>{
  if(e.origin!==location.origin||e.source!==state.frame?.contentWindow||!e.data?.vivid||e.data.view!==state.view)return;
  const m=e.data;
  if(m.type==='ready'){await bridge().load(state.chart);return;}
  if(m.type==='loaded'){state.ready=true;status('已保存到本机');return;}
  if(m.type==='selection'){state.selected=m.name;paintWorkspace();return;}
  if(m.type==='change'&&state.ready){state.pending={project:m.project,job:m.job};status('正在保存…');clearTimeout(state.saveTimer);state.saveTimer=setTimeout(()=>flush().catch(e=>toast(e.message)),650);}
}));
async function flush(){
  clearTimeout(state.saveTimer);
  if(state.ready&&state.chart&&!state.conflict){const snap=bridge()?.snapshot();if(snap&&(JSON.stringify(snap.project)!==JSON.stringify(state.chart.project)||snap.job!==state.chart.job))state.pending={project:snap.project,job:snap.job};}
  state.saveChain=state.saveChain.catch(()=>{}).then(async()=>{
    if(!state.pending||state.conflict||!state.chart)return;
    const value=state.pending;state.pending=null;const cid=state.chart.id;
    state.saving=true;
    try{
      const c=await api('/api/agent/charts/'+cid+'/save',{...value,base_revision:state.chart.revision});
      if(state.chart?.id===cid){state.chart=c;const item=state.session.charts.find(c=>c.id===cid);if(item){item.head=c.revision;item.name=c.name;}status('已保存到本机');paintWorkspace();}
    }catch(e){state.pending??=value;if(e.status===409){state.conflict=true;el('local-conflict').hidden=false;status('修改待保留');}throw e;}finally{state.saving=false;}
  });return state.saveChain;
}
window.VividAgent={flush};
el('keep-manual').onclick=safely(async()=>{const context=workspaceContext(),value=bridge().snapshot();const c=await api('/api/agent/sessions/'+context.id+'/charts',{project:value.project});if(!sameWorkspace(context))return;state.pending=null;state.conflict=false;el('local-conflict').hidden=true;await showCreatedChart(c,context,{skipFlush:true});});
el('sessions').onchange=safely(e=>openSession(e.target.value));
el('new-session').onclick=safely(async()=>{const context=workspaceContext();await flush();if(!sameWorkspace(context))return;const s=await api('/api/agent/sessions',{name:'绘图项目 '+new Date().toLocaleString('zh-CN',{month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit'})});await sessionList();if(sameWorkspace(context))await openSession(s.id);});

function gallery(){
  const q=el('gallery-search').value.trim().toLowerCase(),category=el('gallery-category').value;
  const cards=state.catalog.cards.filter(c=>(!category||c.categories.includes(category))&&(!q||JSON.stringify([c.id,c.display_name,c.tags,c.aliases,c.purpose,c.data_requirements]).toLowerCase().includes(q)));
  el('gallery-count').textContent=cards.length+' 个模板';
  el('gallery-grid').innerHTML=cards.map(c=>`<article class="template-card"><img loading="lazy" src="${escapeHTML(c.previews[0].thumb||c.previews[0].full)}" alt="${escapeHTML(c.display_name)}"><h3>${escapeHTML(c.display_name)}</h3><p>${escapeHTML(c.purpose)}</p><div class="template-actions"><button data-example="${c.id}">打开示例</button><button data-choose="${c.id}">用我的数据</button></div></article>`).join('');
  el('gallery-grid').querySelectorAll('[data-example]').forEach(b=>b.onclick=safely(async()=>{const context=workspaceContext();await flush();if(!sameWorkspace(context))return;const c=await api('/api/agent/sessions/'+context.id+'/charts',{template:b.dataset.example});if(sameWorkspace(context))el('gallery-dialog').close();await showCreatedChart(c,context);}));
  el('gallery-grid').querySelectorAll('[data-choose]').forEach(b=>b.onclick=safely(()=>VividBinding.open(b.dataset.choose)));
}
for(const id of ['gallery-open','empty-gallery'])el(id).onclick=()=>{gallery();showDialog('gallery-dialog');};
el('gallery-search').oninput=gallery;el('gallery-category').onchange=gallery;

async function encodeFile(file){if(file.size>12*1024*1024)throw Error('数据文件最大 12 MB。');return {name:file.name,content:await new Promise((resolve,reject)=>{const r=new FileReader();r.onload=()=>resolve(r.result.split(',')[1]);r.onerror=reject;r.readAsDataURL(file);})};}
async function importFiles(files){
  if(state.sessionLoading)return;
  const context=workspaceContext(),sid=context.id;let last;
  for(const file of files){
    const data=await encodeFile(file),xlsx=/\.xlsx$/i.test(data.name);let result=await api('/api/import',xlsx?{...data,list_sheets:true}:data);
    if(result.sheets.length>1){if(!sameWorkspace(context))return;el('sheet-choice').innerHTML=result.sheets.map(s=>`<option>${escapeHTML(s)}</option>`).join('');showDialog('sheet-dialog');const sheet=await new Promise(resolve=>{el('sheet-confirm').onclick=()=>{resolve(el('sheet-choice').value);el('sheet-dialog').close();};el('sheet-dialog').addEventListener('close',()=>resolve(null),{once:true});});if(!sheet)continue;result=await api('/api/import',{...data,sheet});}
    else if(xlsx)result=await api('/api/import',{...data,sheet:result.sheets[0]});
    const d=await api('/api/agent/sessions/'+sid+'/datasets',{name:file.name+(result.sheet?' / '+result.sheet:''),table:result.table});last=d;
  }
  if(sameWorkspace(context)&&last){state.dataset=last.id;await refreshSession();if(!sameWorkspace(context))return;toast('已导入 '+files.length+' 个文件，可选模板或让助手绘图。');openDataset(last.id);}
}
for(const id of ['upload','import-main','empty-import'])el(id).onclick=()=>el('file-input').click();
el('file-input').onchange=safely(async e=>{await importFiles([...e.target.files]);e.target.value='';});
document.addEventListener('dragover',e=>{if(e.dataTransfer.types.includes('Files')){e.preventDefault();document.body.classList.add('drop-target');}});
document.addEventListener('dragleave',e=>{if(!e.relatedTarget)document.body.classList.remove('drop-target');});
document.addEventListener('drop',safely(async e=>{if(e.dataTransfer.files.length){e.preventDefault();document.body.classList.remove('drop-target');await importFiles([...e.dataTransfer.files]);}}));
function openDataset(id){
  if(state.sessionLoading)return;
  const d=state.session.datasets.find(d=>d.id===id);if(!d)return;state.viewData=structuredClone(d);
  el('data-title').textContent=d.name;el('data-meta').textContent=d.table.rows.length+' 行 × '+d.table.headers.length+' 列 · 原始表在本机保留';
  el('data-preview').innerHTML='<table><thead><tr>'+d.table.headers.map(h=>'<th>'+escapeHTML(h)+'</th>').join('')+'</tr></thead><tbody>'+d.table.rows.slice(0,50).map((r,i)=>'<tr>'+r.map((v,j)=>`<td contenteditable="true" data-row="${i}" data-col="${j}">${escapeHTML(v)}</td>`).join('')+'</tr>').join('')+'</tbody></table>';
  el('data-preview').oninput=e=>{const t=e.target.closest('[data-row]');if(t)state.viewData.table.rows[Number(t.dataset.row)][Number(t.dataset.col)]=t.textContent;};
  showDialog('dataset-dialog');
}
el('data-save').onclick=safely(async()=>{const context=workspaceContext(),d=state.viewData;await api('/api/agent/sessions/'+context.id+'/datasets',{name:d.name+' · 修改版',table:d.table});if(!sameWorkspace(context))return;el('dataset-dialog').close();await refreshSession();if(sameWorkspace(context))toast('已保存为一张新数据表。');});
el('data-use').onclick=()=>{state.dataset=state.viewData.id;state.target='new';el('dataset-dialog').close();paintWorkspace();document.body.classList.remove('agent-hidden');el('prompt').value='请使用数据表「'+state.viewData.name+'」，';el('prompt').focus();};
el('data-template').onclick=()=>{state.dataset=state.viewData.id;el('dataset-dialog').close();paintWorkspace();gallery();showDialog('gallery-dialog');};
el('task-target').onchange=e=>{state.target=e.target.value;paintWorkspace();};
el('task-dataset').onchange=e=>{state.dataset=e.target.value;paintWorkspace();};
el('clear-selection').onclick=()=>{bridge()?.clearSelection();state.selected='';paintWorkspace();};
el('demo-data').onclick=safely(async()=>{
  const context=workspaceContext();
  const rows=Array.from({length:12},(_,i)=>[String(i+1)+' 月',Math.round(105+18*Math.sin(i*.7)+i*2),Math.round(91+15*Math.sin(i*.7+.4)+i*1.5),Math.round(76+11*Math.sin(i*.7+.8)+i)]);
  const d=await api('/api/agent/sessions/'+context.id+'/datasets',{name:'园区能耗对比 · 模拟数据',table:{headers:['月份','常规调度 (MWh)','分时调度 (MWh)','协同优化 (MWh)'],rows}});if(!sameWorkspace(context))return;state.dataset=d.id;state.target='new';
  await refreshSession();if(!sameWorkspace(context))return;el('prompt').value='使用园区能耗对比的模拟数据，画一张三种调度方案的全年趋势图，采用粉彩少女配色，中文标题和坐标轴。保留原模板特点。';el('prompt').focus();toast('模拟数据已载入，发送后会实际调用模型绘图。');
});

async function versions(){
  const context=workspaceContext(),cid=state.chart?.id,view=state.openRequest;await flush();if(!sameWorkspace(context)||view!==state.openRequest)return;const {items}=await api('/api/agent/charts/'+cid+'/revisions');if(!sameWorkspace(context)||view!==state.openRequest)return;
  el('versions').innerHTML=items.map(r=>`<article class="revision"><b>v${r.rev} · ${escapeHTML(r.label)}${r.rev===state.chart.revision?' · 当前':''}</b><p>${r.actor==='agent'?'绘图助手':'手动操作'} · ${new Date(r.created*1000).toLocaleString('zh-CN')} · ${JSON.parse(r.diff).length} 处数据或设置变更</p>${r.job?`<button data-preview-job="${escapeHTML(r.job)}">查看当时的图</button>`:'<span class="revision-unrendered">此版本未出图</span>'}<button data-restore="${r.rev}" ${r.rev===state.chart.revision?'disabled':''}>恢复此版本</button><button data-branch="${r.rev}">另存为新图</button><div class="revision-preview" hidden></div></article>`).join('');
  el('versions').querySelectorAll('[data-preview-job]').forEach(b=>b.onclick=safely(async()=>{const box=b.parentElement.querySelector('.revision-preview');if(!box.children.length){const job=await api('/api/jobs/'+b.dataset.previewJob),img=document.createElement('img');img.src=job.base+'preview.png';img.alt='此历史版本的实际绘图';box.append(img);}box.hidden=!box.hidden;b.textContent=box.hidden?'查看当时的图':'收起图片';}));
  el('versions').querySelectorAll('[data-restore]').forEach(b=>b.onclick=safely(async()=>{await flush();if(!sameWorkspace(context)||view!==state.openRequest)return;const c=await api('/api/agent/charts/'+cid+'/restore',{revision:Number(b.dataset.restore),base_revision:state.chart.revision});if(sameWorkspace(context))el('versions-dialog').close();await showCreatedChart(c,context,{skipFlush:true});}));
  el('versions').querySelectorAll('[data-branch]').forEach(b=>b.onclick=safely(async()=>{if(!sameWorkspace(context))return;const c=await api('/api/agent/charts/'+cid+'/branch',{revision:Number(b.dataset.branch)});if(sameWorkspace(context))el('versions-dialog').close();await showCreatedChart(c,context);}));showDialog('versions-dialog');
}
el('version-open').onclick=safely(versions);
el('branch-chart').onclick=safely(async()=>{const context=workspaceContext(),cid=state.chart?.id,view=state.openRequest;await flush();if(!sameWorkspace(context)||view!==state.openRequest)return;const c=await api('/api/agent/charts/'+cid+'/branch',{});await showCreatedChart(c,context);});

const names={search_templates:'检索模板',inspect_template:'读取模板契约',inspect_data:'检查数据',inspect_objects:'读取图形对象',transform_data:'整理数据',bind_template:'绑定真实数据',update_settings:'调整图表设置',edit_object:'修改图形对象',render:'调用原模板绘图'};
function toolLine(text,error=false){const d=document.createElement('div');d.className='tool-item'+(error?' error':'');d.textContent=text;el('tool-feed').appendChild(d);while(el('tool-feed').children.length>12)el('tool-feed').firstChild.remove();el('tool-feed').scrollTop=el('tool-feed').scrollHeight;}
function paintRun(run){
  const active=run&&['running','queued'].includes(run.status),waiting=run?.status==='waiting';
  el('activity').hidden=!active;el('send').disabled=state.sessionLoading||state.submitting||!!active;el('agent-status').textContent=state.sessionLoading?'切换工作区…':active?'执行中':waiting?'等待补充':'就绪';el('stop-run').disabled=state.sessionLoading;
  el('task-target').disabled=state.sessionLoading||state.submitting||!!active||waiting;el('task-dataset').disabled=state.sessionLoading||state.submitting||!!active||waiting;
  if(!waiting)el('prompt').placeholder='例如：比较各地区的三种方案，用粉彩少女配色…';
  el('run-notice').hidden=true;el('run-notice').replaceChildren();
  if(waiting||['interrupted','error'].includes(run?.status)){
    el('run-notice').hidden=false;const p=document.createElement('div');p.textContent=waiting?run.body.question:run.body.message||'服务上次退出时任务未完成，可以从检查点继续。';el('run-notice').appendChild(p);
    if(waiting){const b=document.createElement('button');b.textContent='取消此次任务';b.onclick=safely(()=>stopRun());el('run-notice').appendChild(b);el('prompt').placeholder='补充这个问题后发送…';}
    else {const b=document.createElement('button');b.textContent='从检查点重试';b.onclick=safely(async()=>{const context=workspaceContext();await api('/api/agent/runs/'+run.id+'/resume',{});if(!sameWorkspace(context))return;state.run={...run,status:'running'};paintRun(state.run);connectEvents(run.id);});el('run-notice').appendChild(b);}
  }
}
function connectEvents(rid){
  const context=workspaceContext();
  state.events?.close();el('tool-feed').replaceChildren();const stream=new EventSource('/api/agent/runs/'+rid+'/events');state.events=stream;
  stream.onmessage=e=>{if(state.events!==stream||!sameWorkspace(context))return;const event=JSON.parse(e.data);if(event.type==='CUSTOM'){
    if(event.name==='progress')el('activity-title').textContent=event.value.message;
    if(event.name==='plan'){toolLine(event.value.message);}
    if(event.name==='tool_result')toolLine((event.value.ok?'✓ ':'! ')+(names[event.value.tool]||event.value.tool)+(event.value.ok?'':'：'+event.value.summary),!event.value.ok);
    if(event.name==='review')toolLine('◈ '+event.value.summary);
  }else if(event.type==='STEP_STARTED')el('activity-title').textContent=names[event.stepName]||event.stepName;
  else if(event.type==='RUN_ERROR')toolLine(event.message,true);};
  stream.addEventListener('settled',safely(async()=>{
    stream.close();if(state.events!==stream||!sameWorkspace(context))return;
    const run=await api('/api/agent/runs/'+rid);if(state.events!==stream||!sameWorkspace(context))return;state.run=run;paintRun(run);
    // Save pending hand edits BEFORE displaying an agent result. On conflict keep both.
    try{await flush();}catch(e){toast(e.message);}
    if(state.events!==stream||!sameWorkspace(context))return;await refreshSession();if(state.events!==stream||!sameWorkspace(context))return;const result=run.body.result;
    if(result?.chart_id&&!state.conflict&&(!state.chart||state.chart.id===result.chart_id||state.chart.id===run.body.view_chart_id))await openChart(result.chart_id);
    if(result?.conflict)toast('手动修改已保留。助手结果可在对话中另存为新图。');
  }));
  stream.onerror=()=>{if(state.events===stream&&sameWorkspace(context))el('agent-status').textContent='重连中';};
}
el('composer').onsubmit=safely(async e=>{
  e.preventDefault();const prompt=el('prompt').value.trim();if(!prompt||state.sessionLoading||state.submitting||['queued','running'].includes(state.run?.status))return;
  const context=workspaceContext(),submission=++state.submissionRequest,view=state.openRequest,waiting=state.run?.status==='waiting'?state.run:null;
  const payload={prompt,chart_id:state.chart?.id,target:state.target,dataset_ids:state.dataset?[state.dataset]:[],selected_object:bridge()?.snapshot().selectedObject};
  state.submitting=true;paintRun(state.run);
  try{
    await flush();if(!sameWorkspace(context)||view!==state.openRequest)return;if(state.conflict)throw Error('请先保留手动修改，再开始任务。');
    const run=waiting?(await api('/api/agent/runs/'+waiting.id+'/resume',{response:prompt}),{...waiting,status:'running'}):await api('/api/agent/sessions/'+context.id+'/runs',payload);
    if(!sameWorkspace(context))return;state.run=run;
    if(el('prompt').value.trim()===prompt)el('prompt').value='';await refreshSession();if(!sameWorkspace(context))return;paintRun(run);connectEvents(run.id);
  }finally{if(submission===state.submissionRequest){state.submitting=false;paintRun(state.run);}}
});
el('prompt').onkeydown=e=>{if(e.key==='Enter'&&!e.shiftKey&&!e.isComposing){e.preventDefault();if(!el('send').disabled)el('composer').requestSubmit();}};
async function stopRun(){if(!state.run||state.sessionLoading)return;const context=workspaceContext(),run=state.run;el('stop-run').disabled=true;await api('/api/agent/runs/'+run.id+'/stop',{});if(!sameWorkspace(context)||state.run?.id!==run.id)return;if(run.status==='waiting'){const stopped=await api('/api/agent/runs/'+run.id);if(!sameWorkspace(context)||state.run?.id!==run.id)return;state.run=stopped;paintRun(stopped);}else el('activity-title').textContent='正在停止模型与绘图进程…';}
el('stop-run').onclick=safely(stopRun);
el('toggle-agent').onclick=()=>{document.body.classList.toggle('agent-hidden');el('toggle-agent').setAttribute('aria-pressed',String(!document.body.classList.contains('agent-hidden')));};
el('toggle-sidebar').onclick=()=>document.body.classList.toggle('sidebar-hidden');
setInterval(()=>{if(state.run&&['queued','running'].includes(state.run.status)){const sec=Math.max(0,Math.floor(Date.now()/1000-state.run.created));el('run-elapsed').textContent=sec<60?sec+' 秒':Math.floor(sec/60)+' 分 '+sec%60+' 秒';el('run-elapsed').title='模型响应和本机绘图累计用时';}else el('run-elapsed').textContent='';},1000);

function providerFields(){el('api-fields').hidden=el('provider').value!=='api';el('cli-hint').hidden=el('provider').value!=='codex';}
function configForm(c){state.config=c;el('provider').value=c.provider;el('api-url').value=c.base_url;el('model-name').value=c.model;el('api-key').value='';el('api-key').placeholder=c.has_key?'已保存密钥；留空保持':'请输入 API Key';el('visual-review').checked=c.review;el('model-badge').textContent=c.provider==='codex'?(c.codex_available?'● Codex CLI 已找到':'○ Codex CLI 待安装'):'● '+(c.model||'API 待配置');providerFields();}
async function saveConfig(){const data={provider:el('provider').value,base_url:el('api-url').value,model:el('model-name').value,review:el('visual-review').checked};if(el('api-key').value)data.api_key=el('api-key').value;const c=await api('/api/agent/config',data);configForm(c);return c;}
el('provider').onchange=providerFields;el('model-open').onclick=safely(async()=>{configForm(await api('/api/agent/config'));el('model-result').textContent='';showDialog('model-dialog');});
el('model-form').onsubmit=safely(async e=>{e.preventDefault();await saveConfig();el('model-dialog').close();toast('模型设置已保存。');});
el('model-test').onclick=safely(async()=>{el('model-test').disabled=true;el('model-result').textContent='正在实际调用所选模型…';try{await saveConfig();const r=await api('/api/agent/config/test',{});el('model-result').textContent=r.message+' · '+r.usage.seconds+' 秒';}catch(e){el('model-result').textContent=e.message;}finally{el('model-test').disabled=false;}});
window.addEventListener('beforeunload',e=>{if(state.pending||state.conflict||state.saving){e.preventDefault();e.returnValue='';}});
async function init(){
  if(innerWidth<=1050){document.body.classList.add('agent-hidden');el('toggle-agent').setAttribute('aria-pressed','false');}
  if(innerWidth<=700)document.body.classList.add('sidebar-hidden');
  const b=await api('/api/bootstrap');state.token=b.token;configForm(b.model);
  state.catalog=await api('/api/agent/catalog');const categories=[...new Set(state.catalog.cards.flatMap(c=>c.categories))];
  el('gallery-category').innerHTML='<option value="">全部类型</option>'+categories.map(c=>{const item=state.catalog.categories.find(x=>x.id===c);return `<option value="${escapeHTML(c)}">${escapeHTML(item?.label||item?.name||c)}</option>`;}).join('');
  let items=await sessionList();if(!items.length){await api('/api/agent/sessions',{name:'我的绘图工作区'});items=await sessionList();}
  const requested=new URLSearchParams(location.search).get('session'),saved=requested||localStorage.getItem('vivid-agent-session'),id=items.find(s=>s.id===saved)?.id||items[0].id;await openSession(id);
}
init().catch(e=>{toast(e.message);el('agent-status').textContent='连接失败';el('model-badge').textContent='请使用「启动Agent工作台.cmd」启动';});
