'use strict';
window.VIVID_EMBED=new URLSearchParams(location.search).get('embed')==='1';
const $=id=>document.getElementById(id), clone=v=>JSON.parse(JSON.stringify(v));
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let project,spec,templates,palettes,sampleProject,historyStack=[],redoStack=[],page=0,selected={row:0,col:0},editingCell=false,rendering=false,lastRender=null,zoom=0,importedFile=null,saveTimer,toastTimer;
const PAGE=50;
function is3D(){return /3d|surface|cone_vortex|isosurface|volume|feature_importance/.test(project.template);}
function toast(text){$('editor-toast').textContent=text;$('editor-toast').hidden=false;clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('editor-toast').hidden=true,2800);}
async function api(path,data){const response=await fetch(path,{method:data?'POST':'GET',headers:data?{'Content-Type':'application/json'}:{},body:data?JSON.stringify(data):undefined});const result=await response.json();if(!response.ok){const e=new Error(result.error?.message||'请求失败');e.detail=result.error;throw e;}return result;}
function signature(){if(project.tables)project.tables[project.active_table]=project.table;return JSON.stringify(window.VIVID_EMBED?project:[project.template,project.tables||project.table,project.mapping,project.column_mappings,project.settings,project.object_edits,project.plotly_view]);}
function remember(){historyStack.push(clone(project));if(historyStack.length>30)historyStack.shift();redoStack=[];updateUndo();}
function updateUndo(){$('undo').disabled=!historyStack.length;$('redo').disabled=!redoStack.length;}
function setStatus(text,kind='dirty'){$('status').textContent=text;$('status').className='status-'+kind;}
function changed(){
  if(project.tables)project.tables[project.active_table]=project.table;
  $('data-error').hidden=true;document.querySelectorAll('.invalid-cell').forEach(c=>c.classList.remove('invalid-cell'));
  const fresh=lastRender&&lastRender.signature===signature();$('export-toggle').disabled=!fresh||rendering;
  if(!rendering)setStatus(fresh?'当前结果已更新':'数据或设置已修改 · 待更新',fresh?'ready':'dirty');
  $('render-info').textContent=lastRender?(fresh?'当前数据与设置对应的实际结果':'当前显示上一次结果 · 请更新预览'):'预览来自实际绘图结果';
  scheduleAutosave();
  DirectEdit.sync();
  window.Studio?.sync();
}
function tableRender(){gridRender();}
function options(value,exclude=[]){return (Number(value)<0||Number(value)>=project.table.headers.length?'<option value="-1" selected>请选择对应列（原列已删除）</option>':'')+project.table.headers.map((h,i)=>exclude.includes(i)?'':`<option value="${i}" ${Number(value)===i?'selected':''}>${esc(h)} · ${esc(project.table.rows[0]?.[i]??'空')}</option>`).join('');}
function requirementsRender(){
  const t=spec.tables?.find(t=>t.key===project.active_table);
  const fieldHelp=t?(t.kind==='columns'?'此表所需字段：'+t.headers.join('、')+'。可在右侧对应导入文件中的列。':'首列为行标签或坐标，其余列为数值；关联矩阵需要同步调整。'):'';
  const lines=[fieldHelp,...(spec.requirements||[])].filter(Boolean);
  $('requirements-content').innerHTML=lines.map(s=>`<p>${esc(s)}</p>`).join('');
  $('data-requirements').hidden=!lines.length;
}
function mappingRender(){
  const m=project.mapping,h=project.table.headers;
  let html='';
  if(spec.family==='catalog'){
    const tableSpec=spec.tables.find(t=>t.key===project.active_table);
    if(tableSpec.kind==='columns'){
      const bindings=project.column_mappings?.[project.active_table]||tableSpec.headers.map((_,i)=>i);
      html=tableSpec.headers.map((field,i)=>`<label>${esc(field)}<select data-column-role="${i}">${options(bindings[i])}</select></label>`).join('');
    }else html='<p class="mapping-note">第一列是行标签，后续列为数值。表头用作变量名称；可直接修改标签与数值。</p>';
  }else if(['wide','matrix'].includes(spec.family)){
    html=`<label>${project.template==='basic.line'?'横轴列':'分类 / 行标签'}<select data-mapping="category">${options(m.category)}</select></label><div class="mapping-label">数值系列（勾选需要绘制的列）</div><div class="value-list">${h.map((name,c)=>c===m.category?'':`<label><input type="checkbox" data-value-col="${c}" ${m.values.includes(c)?'checked':''}>${esc(name)}</label>`).join('')}</div>`;
    if(['basic.grouped_bar','basic.line'].includes(project.template))html+=`<details class="error-mapping"><summary>可选：对称误差列</summary><p class="mapping-note">先取消误差列的数值系列勾选，再将它对应到目标系列。空缺表示不画误差。</p>${m.values.map(c=>`<label>${esc(h[c])}<select data-error-col="${c}"><option value="">不提供误差</option>${h.map((name,i)=>i===m.category||m.values.includes(i)?'':`<option value="${i}" ${String(m.errors?.[c])===String(i)?'selected':''}>${esc(name)}</option>`).join('')}</select></label>`).join('')}</details>`;
  }else{
    const fields=spec.family==='samples'?[['group','分组列'],['value','样本数值列']]:[['x','X 坐标'],['y','Y 坐标'],...(spec.family==='xyz'?[['z','Z 数值']]:[])];
    html=fields.map(([key,label])=>`<label>${label}<select data-mapping="${key}">${options(m[key])}</select></label>`).join('');
  }
  $('mapping-fields').innerHTML=html;
  let specific='';
  if(spec.layout_growth)specific+='<label><input data-setting="auto_layout" type="checkbox">数据增多时自动扩展画布</label>';
  if(['basic.grouped_bar','basic.line','competition.radar'].includes(project.template))specific+=`<label>重点系列<select data-setting="highlight">${m.values.map((c,i)=>`<option value="${i}">${esc(h[c])}</option>`).join('')}</select></label>`;
  if(project.template==='advanced.grouped_radial_bar'){
    const scores=project.active_table==='scores'?project.table:project.tables?.scores;
    // Matrix bindings already project/reorder the stored score columns; do not apply their original indices again.
    specific+=`<label>重点模型<select data-setting="highlight">${(scores?.headers||[]).slice(1).map((name,i)=>`<option value="${i}">${esc(name)}</option>`).join('')}</select></label>`;
  }
  if(project.template==='competition.radar')specific+='<label>径向上限（不自动归一化）<input data-setting="radar_max" type="number" min="0.000001" step="any"></label>';
  if(project.template==='advanced.ridgeline')specific+='<label>山脊基线间距<input data-setting="overlap" type="number" min=".25" max="1.5" step=".05"></label>';
  if(project.template==='advanced.radar_ridgeline')specific+='<label>数值后缀，例如 %<input data-setting="suffix" placeholder="无单位时留空"></label><p class="mapping-note">峰高使用统一最小值与最大值归一化，标签显示输入原值。</p>';
  if(is3D())specific+='<label><input data-setting="view_template" type="checkbox">使用模板视角</label><label>俯仰角<input data-setting="elev" type="number" min="-80" max="85"></label><label>方位角<input data-setting="azim" type="number" min="-180" max="180"></label>';
  if(project.template==='advanced.grouped_bar_3d')specific+='<label><input data-setting="avoid_label_overlap" type="checkbox">密集时避让重叠数值标注</label>';
  $('specific-fields').innerHTML=specific;$('specific-settings').hidden=!specific;fillSettings();requirementsRender();fieldChips();window.Studio?.mappingStatus();
}
function fillSettings(){
  document.querySelectorAll('[data-setting]').forEach(el=>{const v=project.settings[el.dataset.setting]??(el.dataset.setting==='language'?'zh':['auto_layout','avoid_label_overlap'].includes(el.dataset.setting)?true:undefined);if(el.type==='checkbox')el.checked=v;else el.value=v??'';});
  $('zlabel-row').hidden=!is3D();
  $('palette-swatches').innerHTML=(palettes[project.settings.palette]?.colors||[]).map(c=>`<i style="background:${c}"></i>`).join('');
}
function refresh(){
  hideInteractive(true);
  spec=templates.find(t=>t.id===project.template);$('project-name').value=project.name||spec.name;$('template-name').textContent=spec.name+' / '+spec.id;
  $('dataset-row').hidden=spec.family!=='catalog';if(spec.family==='catalog')$('dataset-select').innerHTML=spec.tables.map(t=>`<option value="${t.key}" ${t.key===project.active_table?'selected':''}>${esc(t.title)}</option>`).join('');
  $('table-help').textContent=spec.family==='samples'?'每行是一条真实样本：分组＋数值。支持多格粘贴。':spec.family==='xyz'?'每行一个 X、Y、Z 组合；需要完整矩形网格。':spec.family==='matrix'?'每行一个对象，每列一个数值变量。首列默认作行标签。':'直接修改表格；从 Excel 复制后，可在单元格中粘贴多行多列。';
  tableRender();mappingRender();changed();refreshObjectPanel();
  if(!lastRender)$('method-notes').textContent=(spec.notes||[]).join(' ');
}
function errorDisplay(e){
  const d=e.detail||{};$('data-error').hidden=false;$('data-error').textContent=e.message;
  if(d.table&&project.tables?.[d.table]){project.tables[project.active_table]=project.table;project.active_table=d.table;project.table=project.tables[d.table];$('dataset-select').value=d.table;mappingRender();}
  if(d.row!==null&&d.row!==undefined){const row=dataGrid?.getRow(d.row);if(row){row.scrollTo();const cell=row.getCell('c'+(d.col??0));cell.getElement().classList.add('invalid-cell');}}
  setStatus('请检查数据或设置','error');
}
async function render(){
  if(rendering)return;rendering=true;$('render').disabled=true;$('export-toggle').disabled=true;$('data-error').hidden=true;
  clearTimeout(liveRenderTimer);liveRenderPending=false;
  const sig=signature(),frozen=clone(project);setStatus('正在检查数据…','working');
  try{
    const {job}=await api('/api/render',frozen);let result;
    for(let tries=0;tries<300;tries++){
      result=await api('/api/jobs/'+job);
      if(result.state==='done')break;
      if(result.state==='error')throw new Error(result.message);
      setStatus(result.message||'正在绘图…','working');await new Promise(r=>setTimeout(r,800));
    }
    if(result.state!=='done')throw new Error('任务仍在运行，请稍后再次更新预览。');
    while(DirectEdit.isDragging())await new Promise(resolve=>setTimeout(resolve,60));
    if(sig!==signature()&&liveRenderPending)return;
    lastRender={signature:sig,base:result.base,job};$('output-image').src=result.base+'preview.png';$('output-image').hidden=false;$('preview-placeholder').hidden=true;
    $('open-image').href=result.base+'figure.png';$('open-image').hidden=false;$('method-notes').textContent=result.notes.join(' ');applyZoom(0);await loadObjects(result.base);
  }catch(e){errorDisplay(e);}
  finally{rendering=false;$('render').disabled=false;const failed=!$('data-error').hidden;if(failed){setStatus('请检查数据或设置','error');$('export-toggle').disabled=true;}else changed();if(liveRenderPending)queueLiveRender(30);}
}
function applyZoom(value){zoom=value;$('canvas').classList.toggle('zoomed',zoom>0);$('output-image').style.width=zoom?zoom+'%':'';$('zoom-level').textContent=zoom?zoom+'%':'适应';}
function download(content,name,type='application/json'){const url=URL.createObjectURL(new Blob([content],{type}));const a=document.createElement('a');a.href=url;a.download=name;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),30000);}
function csv(table){return '\ufeff'+[table.headers,...table.rows].map(row=>row.map(v=>'"'+String(v??'').replaceAll('"','""')+'"').join(',')).join('\r\n');}
function mappingFor(table){const family=spec.family;return ['wide','matrix'].includes(family)?{category:0,values:table.headers.slice(1).map((_,i)=>i+1),errors:{}}:family==='samples'?{group:0,value:1}:{x:0,y:1,...(family==='xyz'?{z:2}:{})};}
async function importData(file,sheet){
  try{
    if(file.size>12*1024*1024)throw new Error('文件最大为 12 MB。');
    setStatus('正在读取文件…','working');const content=await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(reader.result.split(',')[1]);reader.onerror=reject;reader.readAsDataURL(file);});
    const result=await api('/api/import',{name:file.name,content,sheet});remember();const oldTable=project.table;project.table=result.table;Studio.remap(oldTable);if(spec.family==='catalog')project.tables[project.active_table]=project.table;project.settings.highlight=0;importedFile=file;page=0;refresh();Studio.showData();Studio.inspect('data');
    $('sheet-row').hidden=result.sheets.length<2;$('sheet-select').innerHTML=result.sheets.map(s=>`<option ${s===result.sheet?'selected':''}>${esc(s)}</option>`).join('');
    toast('数据已导入，请核对右侧数据列对应');
  }catch(e){errorDisplay(e);}
}
// Clipboard parser handles quoted spreadsheet cells and embedded line breaks.
function parsePaste(text){const out=[[]];let v='',quoted=false;for(let i=0;i<text.length;i++){const c=text[i];if(c==='"'){if(quoted&&text[i+1]==='"'){v+='"';i++;}else if(quoted||v==='')quoted=!quoted;else v+=c;}else if(!quoted&&(c==='\t'||c==='\n'||c==='\r')){out[out.length-1].push(v);v='';if(c!=='\t'){if(c==='\r'&&text[i+1]==='\n')i++;out.push([]);}}else v+=c;}out[out.length-1].push(v);if(out.length>1&&out.at(-1).every(v=>v===''))out.pop();return out;}
function uniqueHeader(){let n=project.table.headers.length+1;while(project.table.headers.includes('新列'+n))n++;return '新列'+n;}
function addColumn(){if(project.table.headers.length>=256){toast('最多支持 256 列');return;}const c=project.table.headers.length;project.table.headers.push(uniqueHeader());project.table.rows.forEach(r=>r.push(''));if(project.mapping.values)project.mapping.values.push(c);}
function deleteDataColumn(columnIndex){
    if(project.table.headers.length<=1){toast('至少保留一列');return;}remember();const c=columnIndex;project.table.headers.splice(c,1);project.table.rows.forEach(r=>r.splice(c,1));const m=project.mapping;
    if(spec.family==='catalog'){
      const t=spec.tables.find(t=>t.key===project.active_table);
      if(t.kind==='columns'){
        project.column_mappings??={};
        const bindings=project.column_mappings[project.active_table]||t.headers.map((_,i)=>i);
        project.column_mappings[project.active_table]=bindings.map(v=>v===c?-1:v>c?v-1:v);
      }
    }
    for(const key of ['category','group','value','x','y','z'])if(m[key]!==undefined)m[key]=m[key]===c?-1:m[key]>c?m[key]-1:m[key];
    if(m.values){m.values=m.values.filter(v=>v!==c).map(v=>v>c?v-1:v).filter(v=>v!==m.category);m.errors={};project.settings.highlight=0;}
 tableRender();mappingRender();changed();
}
$('add-row').onclick=()=>{if(project.table.rows.length>=20000)return toast('最多支持 20000 行');remember();project.table.rows.push(project.table.headers.map(()=>''));page=Math.floor((project.table.rows.length-1)/PAGE);tableRender();changed();};
$('add-column').onclick=()=>{remember();addColumn();tableRender();mappingRender();changed();};
$('rows-prev').onclick=()=>{page--;tableRender();};$('rows-next').onclick=()=>{page++;tableRender();};
$('undo').onclick=()=>{if(!historyStack.length)return;redoStack.push(clone(project));project=historyStack.pop();refresh();queueLiveRender(600);};
$('redo').onclick=()=>{if(!redoStack.length)return;historyStack.push(clone(project));project=redoStack.pop();refresh();queueLiveRender(600);};
document.addEventListener('keydown',e=>{if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='z'){e.preventDefault();(e.shiftKey?$('redo'):$('undo')).click();}});
document.querySelector('.settings-panel').addEventListener('change',e=>{
  const el=e.target;if(!Object.keys(el.dataset).some(k=>['setting','columnRole','mapping','valueCol','errorCol'].includes(k)))return;if(el.dataset.setting&&el.tagName==='INPUT'&&el.type!=='checkbox')return;remember();
  if(el.dataset.columnRole!==undefined){project.column_mappings??={};project.column_mappings[project.active_table]??=spec.tables.find(t=>t.key===project.active_table).headers.map((_,i)=>i);project.column_mappings[project.active_table][Number(el.dataset.columnRole)]=Number(el.value);}
  if(el.dataset.setting){const key=el.dataset.setting;project.settings[key]=el.type==='checkbox'?el.checked:el.type==='number'||key==='highlight'?Number(el.value):el.value;if(key==='view_template')project.plotly_view={};fillSettings();if(['palette','language'].includes(key))queueLiveRender();}
  if(el.dataset.mapping){project.mapping[el.dataset.mapping]=Number(el.value);if(el.dataset.mapping==='category'){project.mapping.values=project.mapping.values.filter(c=>c!==Number(el.value));project.settings.highlight=0;}mappingRender();}
  if(el.dataset.valueCol!==undefined){const c=Number(el.dataset.valueCol);project.mapping.values=el.checked?[...project.mapping.values,c].sort((a,b)=>a-b):project.mapping.values.filter(x=>x!==c);project.settings.highlight=0;mappingRender();}
  if(el.dataset.errorCol!==undefined){project.mapping.errors??={};project.mapping.errors[el.dataset.errorCol]=el.value===''?null:Number(el.value);}
  changed();
});
document.querySelector('.settings-panel').addEventListener('focusin',e=>{e.target._checkpoint=false;});
document.querySelector('.settings-panel').addEventListener('input',e=>{const el=e.target;if(el.dataset.setting&&el.tagName==='INPUT'&&el.type!=='checkbox'){if(!el._checkpoint){remember();el._checkpoint=true;}project.settings[el.dataset.setting]=el.type==='number'?Number(el.value):el.value;if(['elev','azim'].includes(el.dataset.setting)){project.plotly_view={};project.settings.view_template=false;document.querySelector('[data-setting="view_template"]').checked=false;}changed();}});
$('project-name').onchange=e=>{remember();project.name=e.target.value;changed();};
$('reset-style').onclick=()=>{remember();project.settings=clone(sampleProject.settings);project.object_edits={};project.plotly_view={};refresh();queueLiveRender();};
$('load-example').onclick=()=>{remember();if(project.tables){project.tables=clone(sampleProject.tables);project.table=project.tables[project.active_table];project.column_mappings={};}else project.table=clone(sampleProject.table);project.mapping=clone(sampleProject.mapping);project.settings.highlight=0;page=0;$('sheet-row').hidden=true;refresh();};
$('example-file').onclick=()=>download(csv(sampleProject.tables?.[project.active_table]||sampleProject.table),project.template+'.example.csv','text/csv;charset=utf-8');
$('dataset-select').onchange=e=>{project.tables[project.active_table]=project.table;project.active_table=e.target.value;project.table=project.tables[project.active_table];page=0;tableRender();mappingRender();scheduleAutosave();window.Studio?.sync();};
$('import-file').onchange=e=>{if(e.target.files[0])importData(e.target.files[0]);e.target.value='';};
$('sheet-select').onchange=e=>{if(importedFile)importData(importedFile,e.target.value);};
$('render').onclick=render;
$('zoom-in').onclick=()=>applyZoom(Math.min(400,(zoom||100)+25));$('zoom-out').onclick=()=>applyZoom(Math.max(25,(zoom||100)-25));$('fit').onclick=()=>applyZoom(0);
$('fold-data').onclick=()=>{$('editor-shell').classList.add('data-folded');$('show-data').hidden=false;};$('show-data').onclick=()=>{$('editor-shell').classList.remove('data-folded');$('show-data').hidden=true;};
$('fold-settings').onclick=()=>{$('editor-shell').classList.add('settings-folded');$('show-settings').hidden=false;};$('show-settings').onclick=()=>{$('editor-shell').classList.remove('settings-folded');$('show-settings').hidden=true;};
$('save-project').onclick=()=>{flushAutosave();project.source_version='workbench-editor-2';download(JSON.stringify(project,null,2),(project.name||'绘图项目').replace(/[\\/:*?"<>|]/g,'_')+'.vivid.json');toast('项目已保存，包含当前数据与设置');};
$('open-project').onclick=()=>$('project-file').click();
$('project-file').onchange=async e=>{
  const file=e.target.files[0];if(!file)return;
  try{const loaded=JSON.parse(await file.text());await api('/api/validate',loaded);remember();project=loaded;sampleProject=await api('/api/sample?id='+encodeURIComponent(project.template));lastRender=null;objectManifest=null;projectId=crypto.randomUUID();hideInteractive();page=0;$('output-image').hidden=true;$('preview-placeholder').hidden=false;$('open-image').hidden=true;$('method-notes').textContent='';history.replaceState(null,'','editor.html?template='+encodeURIComponent(project.template));refresh();toast('项目已恢复，点击更新预览重新出图');}catch(err){errorDisplay(err);}e.target.value='';
};
$('export-toggle').onclick=()=>{if(!lastRender||lastRender.signature!==signature())return toast('请先更新预览');$('export-links').innerHTML=[['figure.png','PNG 图片 · 300 DPI'],['figure.pdf','PDF 图片'],['figure.svg','SVG 图片'],['data.csv','当前数据表 CSV'],['plot.py','绘图源码（配合复现包运行）'],['reproduce.zip','完整复现包 .zip']].map(([file,label])=>`<a href="${lastRender.base+file}" download>${label}<span>↓</span></a>`).join('');$('export-dialog').showModal();};
$('export-close').onclick=()=>$('export-dialog').close();
async function init(){
  try{
    const params=new URLSearchParams(location.search),tid=params.get('template');
    if(!tid){location.replace('index.html'+(['zh','en'].includes(params.get('language'))?'?language='+params.get('language'):''));return;}
    const meta=await api('/api/templates');templates=meta.templates;palettes=meta.palettes;
    sampleProject=await api('/api/sample?id='+encodeURIComponent(tid));project=clone(sampleProject);
    // URL language initializes new projects. Restoring a draft below retains its saved settings.
    if(['zh','en'].includes(params.get('language')))project.settings.language=params.get('language');
    $('palette-select').innerHTML=Object.entries(palettes).map(([id,p])=>`<option value="${id}">${esc(p.name)}</option>`).join('');
    if(!window.VIVID_EMBED)await restoreLocalDraft(tid);
    sampleProject.settings.language=project.settings.language||'zh';installInteractions();
    refresh();
    if(window.VIVID_EMBED)window.VividBridge.ready();else await render();
  }catch(e){$('connection-error').hidden=false;$('editor-shell').hidden=true;document.querySelectorAll('.editor-actions button').forEach(b=>b.disabled=true);}
}
init();
