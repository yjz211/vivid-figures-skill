'use strict';
let objectManifest=null,selectedObject='',projectId='',autosaveChain=Promise.resolve(),autosaveRevision=0,viewTimer;
const objectLabels={text:'文字',label:'轴名称',fontsize:'字号（pt）',color:'颜色',rotation:'旋转（度）',visible:'显示',min:'范围起点',max:'范围终点',loc:'图例位置',ncols:'图例列数',frame:'图例边框',linewidth:'线宽',alpha:'不透明度'};
const locations={'best':'自动','upper right':'右上','upper left':'左上','lower right':'右下','lower left':'左下','center right':'右中','center left':'左中','upper center':'上中','lower center':'下中','center':'居中'};
objectLabels.offset_x='水平偏移（pt）';objectLabels.offset_y='向下偏移（pt）';
let liveRenderTimer,liveRenderPending=false;
function queueLiveRender(delay=300){
  liveRenderPending=true;clearTimeout(liveRenderTimer);
  liveRenderTimer=setTimeout(()=>{if(!rendering){liveRenderPending=false;render();}},delay);
}
async function restoreLocalDraft(tid){
  const params=new URLSearchParams(location.search);projectId=params.get('project')||localStorage.getItem('vivid-last-'+tid)||crypto.randomUUID();
  let saved=null;
  try{saved=(await api('/api/library?kind=projects&id='+encodeURIComponent(projectId))).value;}catch{}
  try{const recovery=JSON.parse(localStorage.getItem('vivid-recovery-'+projectId)||'null');if(recovery)saved=recovery;}catch{}
  if(!saved){try{saved=JSON.parse(sessionStorage.getItem('vivid-editor-draft-'+tid)||'null');}catch{}}
  if(saved?.template===tid){project=saved;toast('已恢复本机项目草稿');}
}
function scheduleAutosave(){
  if(window.VIVID_EMBED){window.VividBridge?.changed();return;}
  if(!projectId)return;
  clearTimeout(saveTimer);$('autosave-status').textContent='正在自动保存…';
  try{localStorage.setItem('vivid-recovery-'+projectId,JSON.stringify(project));localStorage.setItem('vivid-last-'+project.template,projectId);}catch{}
  saveTimer=setTimeout(flushAutosave,650);
}
function flushAutosave(){
  if(window.VIVID_EMBED)return window.parent.VividAgent?.flush()||Promise.resolve();
  clearTimeout(saveTimer);if(!projectId||!project)return Promise.resolve();
  signature();const id=projectId,value=clone(project),revision=++autosaveRevision;
  autosaveChain=autosaveChain.catch(()=>{}).then(()=>api('/api/library',{kind:'projects',id,value})).then(()=>{if(revision===autosaveRevision&&id===projectId)$('autosave-status').textContent='已自动保存到本机';}).catch(()=>{$('autosave-status').textContent='保存失败 · 请下载项目备份';});
  return autosaveChain;
}
function hideInteractive(keepObjects=false){
  if(keepObjects&&!$('object-preview').hidden&&DirectEdit.compatible()){DirectEdit.sync();return;}
  DirectEdit.hide();
  $('object-preview').hidden=true;$('plotly-preview').hidden=true;$('static-preview').hidden=true;
  $('output-image').hidden=!lastRender;
}
async function loadObjects(base){
  objectManifest=await (await fetch(base+'objects.json')).json();
  hideInteractive();$('native-preview').hidden=objectManifest.renderer!=='plotly';$('pick-objects').hidden=objectManifest.renderer==='plotly';
  refreshObjectPanel();
  if(objectManifest.renderer==='matplotlib'&&DirectEdit.compatible())openObjectPreview();
}
function refreshObjectPanel(){
  if(!$('object-select'))return;
  const objects=objectManifest?.objects||[];
  if(!objects.some(o=>o.id===selectedObject))selectedObject=window.VIVID_EMBED?'':objects[0]?.id||'';
  $('object-select').innerHTML=objects.length?(window.VIVID_EMBED?'<option value="">点选图形或选择对象</option>':'')+objects.map(o=>`<option value="${esc(o.id)}" ${o.id===selectedObject?'selected':''}>${esc(o.name)}</option>`).join(''):'<option>更新预览后可编辑对象</option>';
  $('clear-stale').hidden=!objectManifest?.skipped?.length;objectFields();
  DirectEdit.sync();
}
function objectFields(){
  const obj=objectManifest?.objects.find(o=>o.id===selectedObject);
  $('reset-object').disabled=!project?.object_edits?.[selectedObject];
  if(!obj){$('object-fields').innerHTML='';return;}
  const edit=project.object_edits?.[obj.id];const props={...obj.props,...(edit?.guard===objectManifest.guard?edit.props:{})};
  // Plotly automatic axes may not have explicit limits until a user supplies them.
  if(obj.kind==='axis'){props.min??='';props.max??='';}
  $('object-fields').innerHTML=Object.entries(props).map(([key,v])=>{
    const type=key==='color'?'color':typeof v==='boolean'?'checkbox':['text','label'].includes(key)?'text':'number';
    let control=key==='loc'?`<select data-object-prop="${key}">${Object.entries(locations).map(([k,l])=>`<option value="${k}" ${v===k?'selected':''}>${l}</option>`).join('')}</select>`:`<input data-object-prop="${key}" type="${type}" ${type==='checkbox'?(v?'checked':''):`value="${esc(v)}"`} ${type==='number'?'step="any"':''} ${key==='fontsize'?'min="4" max="72"':key==='alpha'?'min="0" max="1" step="0.05"':key==='ncols'?'min="1" max="12"':''}>`;
    return `<label>${objectLabels[key]||key}${control}</label>`;
  }).join('');
  $('object-fields').querySelectorAll('[data-object-prop]').forEach(input=>input.onchange=()=>{
    const key=input.dataset.objectProp;
    if(input.type==='number'&&(input.value===''||!Number.isFinite(Number(input.value))))return;
    remember();project.object_edits??={};
    if(project.object_edits[obj.id]?.guard!==objectManifest.guard)project.object_edits[obj.id]={guard:objectManifest.guard,props:{}};
    project.object_edits[obj.id].props[key]=input.type==='checkbox'?input.checked:input.type==='number'?Number(input.value):input.value;
    if(objectManifest.renderer==='plotly'&&['min','max'].includes(key)){
      const path=obj.id.slice(6).replaceAll('-','.');delete project.plotly_view?.[path+'.range'];delete project.plotly_view?.[path+'.autorange'];
    }
    changed();$('reset-object').disabled=false;DirectEdit.sync();queueLiveRender(650);
  });
}
function selectObject(id){
  if(!id){DirectEdit.clearSelection();objectFields();return;}
  DirectEdit.activate();
  selectedObject=id;$('object-select').value=id;objectFields();
  const keepCanvas=window.VIVID_EMBED&&$('editor-shell').classList.contains('settings-folded');
  if(!keepCanvas)window.Studio?.inspect('object');
  window.VividBridge?.selection(id);
  const doc=$('object-preview').contentDocument;
  doc?.querySelectorAll('.vivid-picked').forEach(el=>el.classList.remove('vivid-picked'));
  const obj=objectManifest.objects.find(o=>o.id===id);doc?.getElementById(obj?.dom_id)?.classList.add('vivid-picked');
  document.querySelector('.settings-panel').classList.remove('unused');if(!keepCanvas){$('editor-shell').classList.remove('settings-folded');$('show-settings').hidden=true;}
  document.querySelector('.settings-scroll').scrollTop=0;
  DirectEdit.updateToolbar();DirectEdit.position();
}
function openObjectPreview(){
  if(!DirectEdit.compatible())return toast('数据或全局设置已变化，请先更新预览');
  $('output-image').hidden=true;$('plotly-preview').hidden=true;$('static-preview').hidden=false;
  const frame=$('object-preview');frame.hidden=false;
  frame.style.visibility='hidden';
  frame.onload=()=>{
    frame.style.visibility='';DirectEdit.bind(frame);
  };
  frame.src=lastRender.base+'figure.svg';
}
async function listProjects(){
  await flushAutosave();const {items}=await api('/api/library?kind=projects');
  $('library-list').innerHTML=items.map(item=>`<button data-project="${esc(item.id)}" data-template="${esc(item.template)}"><b>${esc(item.name)}</b><span>${esc(item.template)} · ${new Date(item.updated).toLocaleString('zh-CN')}</span></button>`).join('')||'<p>还没有保存的项目</p>';
  $('library-list').querySelectorAll('button').forEach(b=>b.onclick=()=>{location.href='editor.html?template='+encodeURIComponent(b.dataset.template)+'&project='+encodeURIComponent(b.dataset.project);});
  $('library-dialog').showModal();
}
async function refreshStyles(){
  const {items}=await api('/api/library?kind=styles');$('style-select').innerHTML='<option value="">选择样式</option>'+items.map(i=>`<option value="${esc(i.id)}">${esc(i.name)}</option>`).join('');
}
function installInteractions(){
  DirectEdit.init();
  installGridEvents();$('match-fields').onclick=()=>window.Studio?Studio.suggest():matchFields();
  const copyButton=document.createElement('button');copyButton.className='small-button';copyButton.textContent='将当前项目存为副本';copyButton.style.margin='12px 15px 0';
  $('library-dialog').insertBefore(copyButton,$('library-list'));
  copyButton.onclick=async()=>{await flushAutosave();projectId=crypto.randomUUID();project.name=(project.name||spec.name)+' · 副本';history.replaceState(null,'','editor.html?template='+encodeURIComponent(project.template)+'&project='+projectId);refresh();await flushAutosave();$('library-dialog').close();toast('已创建独立副本，原项目保留');};
  $('object-select').onchange=e=>selectObject(e.target.value);
  $('reset-object').onclick=()=>{remember();delete project.object_edits?.[selectedObject];objectFields();changed();DirectEdit.sync();queueLiveRender();};
  $('clear-stale').onclick=()=>{remember();(objectManifest.skipped||[]).forEach(id=>delete project.object_edits?.[id]);objectManifest.skipped=[];refreshObjectPanel();changed();};
  $('pick-objects').onclick=openObjectPreview;$('static-preview').onclick=hideInteractive;
  $('native-preview').onclick=()=>{if(!lastRender||lastRender.signature!==signature())return toast('请先更新预览，再进入交互');$('output-image').hidden=true;$('object-preview').hidden=true;$('static-preview').hidden=false;$('plotly-preview').hidden=false;$('plotly-preview').src=lastRender.base+'interactive.html';};
  window.addEventListener('message',e=>{
    if(e.origin!==location.origin||e.source!==$('plotly-preview').contentWindow||!e.data?.vivid)return;
    if($('plotly-preview').hidden)return;
    if(e.data.type==='trace'){const obj=objectManifest?.objects.filter(o=>o.kind==='trace')[e.data.data];if(obj)selectObject(obj.id);return;}
    if(e.data.type==='view'){
      const view=e.data.data;if(JSON.stringify(project.plotly_view||{})===JSON.stringify(view))return;
      if(!viewTimer)remember();clearTimeout(viewTimer);project.plotly_view=view;changed();
      viewTimer=setTimeout(()=>{viewTimer=null;toast('视角已保存；更新预览后可导出相同视角');},200);
    }
  });
  $('recent-projects').onclick=()=>listProjects().catch(e=>toast(e.message));$('library-close').onclick=()=>$('library-dialog').close();
  $('save-style').onclick=async()=>{
    const name=$('style-name').value.trim();if(!name)return toast('先给样式起个名字');
    const settings=Object.fromEntries(['palette','width','height','font_size','legend','labels'].map(k=>[k,project.settings[k]]));
    const edits={};for(const [id,entry] of Object.entries(project.object_edits||{})){
      const props=Object.fromEntries(Object.entries(entry.props).filter(([k])=>!['text','label','min','max','offset_x','offset_y'].includes(k)));
      if(Object.keys(props).length)edits[id]={guard:entry.guard,props};
    }
    try{const saved=await api('/api/library',{kind:'styles',value:{name,template:project.template,settings,object_edits:edits}});await refreshStyles();$('style-select').value=saved.id;toast('外观已保存');}catch(e){toast(e.message);}
  };
  $('apply-style').onclick=async()=>{
    if(!$('style-select').value)return;
    try{const {value}=await api('/api/library?kind=styles&id='+encodeURIComponent($('style-select').value));remember();Object.assign(project.settings,value.settings);
      let skipped=0;if(value.template===project.template)for(const [id,entry] of Object.entries(value.object_edits||{})){
        if(entry.guard===objectManifest?.guard){project.object_edits??={};const prior=project.object_edits[id];project.object_edits[id]={guard:entry.guard,props:{...(prior?.guard===entry.guard?prior.props:{}),...entry.props}};}else skipped++;
      }
      refresh();queueLiveRender();toast(skipped?'已应用通用外观；数据结构不同的对象样式未套用':'已应用样式，可撤销');
    }catch(e){toast(e.message);}
  };
  refreshStyles().catch(()=>{});
  window.addEventListener('pagehide',()=>{if(projectId&&project){signature();navigator.sendBeacon('/api/library',new Blob([JSON.stringify({kind:'projects',id:projectId,value:project})],{type:'application/json'}));}});
}
