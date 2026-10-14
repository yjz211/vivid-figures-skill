'use strict';
/* Layout and data preparation share the existing project/undo/render pipeline. */
window.Studio=(()=>{
  let tab='chart',prepared=null,sourceSignature='',navigatorSignature='',drag=null;
  const normalize=s=>String(s).trim().toLowerCase().replace(/[\s_\-（）()]/g,'');
  const uniqueMatch=(headers,name)=>{const hits=headers.map((h,i)=>normalize(h)===normalize(name)?i:-1).filter(i=>i>=0);return hits.length===1?hits[0]:-1;};
  function sections(){document.querySelectorAll('[data-inspector-section]').forEach(s=>s.hidden=s.dataset.inspectorSection!==tab||(s.id==='specific-settings'&&!$('specific-fields').children.length));}
  function inspect(next){
    tab=next;document.querySelectorAll('[data-inspector-tab]').forEach(b=>{b.classList.toggle('active',b.dataset.inspectorTab===tab);b.setAttribute('aria-selected',String(b.dataset.inspectorTab===tab));});
    sections();
    $('inspector-title').textContent={chart:'整张图',data:'数据对应',object:'选中对象'}[tab];
    $('editor-shell').classList.remove('settings-folded');$('show-settings').hidden=true;
  }
  function showData(key){
    if(key&&project.tables&&project.active_table!==key){project.tables[project.active_table]=project.table;project.active_table=key;project.table=project.tables[key];$('dataset-select').value=key;tableRender();mappingRender();scheduleAutosave();}
    $('editor-shell').classList.remove('data-folded');$('show-data').hidden=true;if(gridReady)dataGrid.redraw(true);sync();
  }
  function sync(){
    if(!project||!spec||!$('studio-project-tree'))return;
    const keys=spec.tables||[{key:'main',title:'绘图数据'}];
    const sig=JSON.stringify([project.template,project.active_table,keys.map(t=>[t.key,(project.tables?.[t.key]||project.table).rows.length])]);
    if(sig!==navigatorSignature){navigatorSignature=sig;
      $('studio-project-tree').innerHTML='<h3>数据表</h3>'+keys.map(t=>`<button data-open-table="${esc(t.key)}" class="tree-item ${t.key===(project.active_table||'main')?'active':''}"><span>▤ ${esc(t.title)}</span><small>${(project.tables?.[t.key]||project.table).rows.length} 行</small></button>`).join('')+`<h3>当前图表</h3><button class="tree-item active" id="tree-chart">▧ ${esc(spec.name)}</button>`;
      $('studio-project-tree').querySelectorAll('[data-open-table]').forEach(b=>b.onclick=()=>{showData(b.dataset.openTable);inspect('data');});
      $('tree-chart').onclick=()=>inspect('chart');
    }
    $('data-caption').textContent=(spec.tables?.find(t=>t.key===project.active_table)?.title||'绘图数据');
    mappingStatus();
  }
  function mappingStatus(){
    if(!$('mapping-status')||!project)return;
    sections();
    const selects=[...$('mapping-fields').querySelectorAll('select[data-column-role],select[data-mapping]')];
    const missing=selects.filter(s=>Number(s.value)<0||s.value==='').length;
    const zero=project.mapping?.values&&['wide','matrix'].includes(spec.family)&&!project.mapping.values.length;
    $('mapping-status').textContent=missing||zero?`还有 ${missing+(zero?1:0)} 项需要对应。选好后点击更新预览。`:'字段已对应；请核对数据含义，再更新预览。';
    $('mapping-status').classList.toggle('needs-mapping',!!(missing||zero));
    $('match-fields').textContent='建议对应';
    $('match-fields').disabled=spec.family==='catalog'&&spec.tables.find(t=>t.key===project.active_table)?.kind!=='columns';
  }
  function remap(oldTable){
    const h=project.table.headers,old=oldTable.headers,match=c=>Number.isInteger(c)&&c>=0?uniqueMatch(h,old[c]):-1;
    if(spec.family==='catalog'){
      const t=spec.tables.find(t=>t.key===project.active_table);
      if(t.kind==='columns'){
        const prior=project.column_mappings?.[t.key]||t.headers.map((_,i)=>i);
        project.column_mappings??={};project.column_mappings[t.key]=t.headers.map((name,i)=>{const c=match(prior[i]);return c>=0?c:uniqueMatch(h,name);});
      }
    }else{
      const m=project.mapping;const next={...m};
      for(const key of ['category','group','value','x','y','z'])if(key in m)next[key]=match(m[key]);
      if(m.values){next.values=m.values.map(match).filter(c=>c>=0&&c!==next.category);next.errors={};for(const [k,v] of Object.entries(m.errors||{})){const c=match(Number(k)),e=match(v);if(c>=0&&e>=0)next.errors[c]=e;}}
      project.mapping=next;
    }
  }
  function suggest(){
    remember();const h=project.table.headers,rows=project.table.rows;
    const types=h.map((_,c)=>{const vs=rows.map(r=>r[c]).filter(v=>!VividTransform.empty(v));return vs.length&&vs.every(VividTransform.number)?'number':vs.length?'text':'empty';});
    const aliases={category:['分类','指标','年份','时间','日期','样本','类别','category','time','date','year','sample'],group:['分组','组别','系列','group','series'],value:['数值','值','value','values'],x:['x','x坐标','横轴','投入'],y:['y','y坐标','纵轴','产出'],z:['z','z数值','高度']};
    const role=(key,current)=>{if(Number.isInteger(current)&&current>=0&&current<h.length)return current;const names=[...(aliases[key]||[]),sampleProject.table?.headers[sampleProject.mapping?.[key]]].filter(v=>v!=null).map(normalize);const candidates=h.map((name,i)=>names.includes(normalize(name))?i:-1).filter(i=>i>=0);return candidates.length===1?candidates[0]:-1;};
    if(spec.family==='catalog'){
      const t=spec.tables.find(t=>t.key===project.active_table);if(t.kind==='columns'){project.column_mappings??={};project.column_mappings[t.key]=t.headers.map(field=>uniqueMatch(h,field));}
    }else if(['wide','matrix'].includes(spec.family)){
      let c=role('category',project.mapping.category);const text=types.map((t,i)=>t==='text'?i:-1).filter(i=>i>=0);if(c<0&&text.length===1)c=text[0];
      project.mapping={category:c,values:types.map((t,i)=>t==='number'&&i!==c&&!/误差|标准差|标准误|error|stderr|^sd$|^se$/i.test(h[i])?i:-1).filter(i=>i>=0),errors:{}};
    }else{
      const keys=spec.family==='samples'?['group','value']:spec.family==='xyz'?['x','y','z']:['x','y'];
      const m={};keys.forEach(k=>m[k]=role(k,project.mapping[k]));
      if(spec.family==='samples')for(const k of keys)if(m[k]<0){const candidates=types.map((t,i)=>t===(k==='group'?'text':'number')&&!Object.values(m).includes(i)?i:-1).filter(i=>i>=0);if(candidates.length===1)m[k]=candidates[0];}
      project.mapping=m;
    }
    project.settings.highlight=0;mappingRender();changed();mappingStatus();toast('已按列名和类型建议；含义不明确的字段需要手动对应');
  }
  const kinds={sort:'排序',filter:'筛选保留行',transpose:'行列转置',melt:'宽表 → 长表',pivot:'长表 → 宽表',aggregate:'分组汇总'};
  const hints={sort:'数字列按数值排序，文字列按名称排序，空值放在最后。',filter:'应用后仅保留符合条件的行；不会修改其他数据表，可撤销。',transpose:'首列作为新表头，原来的数值列表头成为首列。适合带行列标签的矩阵。',melt:'例如「时间、方案 A、方案 B」变为「时间、系列、数值」。',pivot:'将「行标识、系列、数值」展开成每个系列一列。重复组合需要先汇总；缺少的组合保留空白。',aggregate:'由你明确选择计算方式。样本标准差按 n−1 计算；空值和非数值会提示处理。'};
  function select(name,label,selected=0){return `<label>${label}<select name="${name}">${project.table.headers.map((h,i)=>`<option value="${i}" ${i===selected?'selected':''}>${esc(h)}</option>`).join('')}</select></label>`;}
  function transformFields(){
    const kind=$('transform-kind').value;prepared=null;$('transform-apply').disabled=true;$('transform-result').replaceChildren();$('transform-hint').textContent=hints[kind];
    const h=project.table.headers;
    $('transform-fields').innerHTML=kind==='sort'?select('column','排序依据')+'<label>顺序<select name="direction"><option value="asc">升序</option><option value="desc">降序</option></select></label>':
      kind==='filter'?select('column','筛选列')+'<label>条件<select name="operator"><option value="eq">等于</option><option value="ne">不等于</option><option value="contains">包含文字</option><option value="gt">大于</option><option value="gte">大于等于</option><option value="lt">小于</option><option value="lte">小于等于</option><option value="nonempty">非空</option><option value="empty">空白</option></select></label><label>条件值<input name="value" placeholder="空白 / 非空条件无需填写"></label>':
      kind==='melt'?select('id','保留的标识列')+'<fieldset><legend>转成长表的数值列</legend>'+h.map((name,i)=>`<label class="inline-check"><input type="checkbox" name="values" value="${i}" ${i?'checked':''}>${esc(name)}</label>`).join('')+'</fieldset>':
      kind==='pivot'?select('id','行标识')+select('group','系列列',Math.min(1,h.length-1))+select('value','数值列',Math.min(2,h.length-1)):
      kind==='aggregate'?select('group','分组列')+select('value','数值列',Math.min(1,h.length-1))+'<label>计算方式<select name="method"><option value="mean">均值</option><option value="std">样本标准差</option><option value="sum">合计</option><option value="count">有效数值个数</option></select></label>':'';
  }
  function previewTransform(){
    try{
      const form=$('transform-fields'),val=n=>form.querySelector(`[name="${n}"]`)?.value,kind=$('transform-kind').value;
      const op={kind};for(const key of ['column','id','group','value']){if(val(key)!==undefined)op[key]=kind==='filter'&&key==='value'?val(key):Number(val(key));}
      op.descending=val('direction')==='desc';op.operator=val('operator');op.method=val('method');op.values=[...form.querySelectorAll('[name="values"]:checked')].map(e=>Number(e.value));
      prepared=VividTransform.compute(project.table,op);sourceSignature=JSON.stringify([project.template,project.active_table,project.table]);
      const t=prepared.table;
      $('transform-result').innerHTML=`<p><b>${project.table.rows.length} 行 × ${project.table.headers.length} 列 → ${t.rows.length} 行 × ${t.headers.length} 列</b></p><p>${prepared.structural?'数据结构改变后，请核对右侧字段对应。':'当前字段对应将保留。'}${project.tables?'仅处理当前表，关联表需保持匹配。':''}</p><div class="transform-table"><table><thead><tr>${t.headers.slice(0,12).map(h=>`<th>${esc(h)}</th>`).join('')}</tr></thead><tbody>${t.rows.slice(0,8).map(r=>`<tr>${r.slice(0,12).map(v=>`<td>${esc(v)}</td>`).join('')}</tr>`).join('')}</tbody></table></div><p>预览最多显示 8 行、12 列；应用会保留完整结果。</p>`;
      $('transform-apply').disabled=false;
    }catch(e){prepared=null;$('transform-result').textContent=e.message;$('transform-apply').disabled=true;}
  }
  function applyTransform(){
    if(!prepared)return;if(sourceSignature!==JSON.stringify([project.template,project.active_table,project.table]))return toast('数据已变化，请重新预览整理结果');
    remember();const old=project.table;project.table=prepared.table;if(prepared.structural)remap(old);
    project.settings.highlight=0;page=0;refresh();inspect('data');$('transform-dialog').close();prepared=null;toast('已应用到当前表，可撤销；更新预览后出图');
  }
  function init(){
    const shell=$('editor-shell'),aside=document.createElement('aside');aside.className='project-panel';aside.innerHTML='<div class="panel-heading"><h2>项目</h2><button id="fold-project" aria-label="收起项目栏">⇤</button></div><div id="studio-project-tree"></div><div class="project-bottom"><a href="index.html">＋ 从图表库选图 ↗</a><p>数据 → 对应字段 → 更新预览</p></div>';shell.prepend(aside);
    const navButton=document.createElement('button');navButton.id='show-project';navButton.textContent='▧ 项目';navButton.hidden=true;document.querySelector('.canvas-toolbar>div').prepend(navButton);
    $('fold-project').onclick=()=>{shell.classList.add('project-folded');navButton.hidden=false;};navButton.onclick=()=>{shell.classList.remove('project-folded');navButton.hidden=true;};
    const heading=document.querySelector('.data-panel .panel-heading h2');heading.innerHTML='<span class="panel-index">▤</span><span id="data-caption">绘图数据</span>';
    $('fold-data').textContent='⌄';$('show-data').textContent='▤ 展开数据';
    const toolbar=document.querySelector('.data-tools');document.querySelector('.data-panel .panel-heading').insertBefore(toolbar,$('fold-data'));
    const organize=document.createElement('button');organize.id='organize-data';organize.className='small-button';organize.textContent='整理数据';toolbar.append(organize);
    const mapButton=document.createElement('button');mapButton.id='open-mapping';mapButton.className='small-button';mapButton.textContent='对应字段';toolbar.append(mapButton);mapButton.onclick=()=>inspect('data');
    const tools=document.createElement('div');tools.className='data-command-row';document.querySelector('.table-scroll').before(tools);tools.append(document.querySelector('.table-toolbar'),document.querySelector('.paste-options'));
    document.querySelector('.editor-actions').prepend($('undo'),$('redo'));
    const extra=document.createElement('details');extra.className='data-more';extra.innerHTML='<summary>更多操作 / 格式要求</summary><div class="data-more-body"></div>';tools.append(extra);
    const body=extra.querySelector('div');body.append($('table-help'),$('data-requirements'),document.querySelector('.table-toolbar.compact'));
    const examples=document.createElement('div');examples.className='data-example-tools';examples.append($('example-file'),$('load-example'));body.append(examples);
    const selectors=document.createElement('div');selectors.className='data-selectors';document.querySelector('.data-panel .panel-heading').after(selectors);selectors.append($('dataset-row'),$('sheet-row'));
    const settings=document.querySelector('.settings-scroll');const sections=[...settings.children];
    sections.forEach(s=>s.dataset.inspectorSection=s.classList.contains('object-section')?'object':s.contains($('mapping-fields'))?'data':'chart');
    document.querySelector('.settings-panel .panel-heading h2').innerHTML='<span id="inspector-title">整张图</span>';
    const tabs=document.createElement('div');tabs.className='inspector-tabs';tabs.setAttribute('role','tablist');tabs.innerHTML=['chart','data','object'].map((t,i)=>`<button role="tab" data-inspector-tab="${t}">${['图形','数据','对象'][i]}</button>`).join('');settings.before(tabs);tabs.querySelectorAll('button').forEach(b=>b.onclick=()=>inspect(b.dataset.inspectorTab));
    const status=document.createElement('p');status.id='mapping-status';status.className='mapping-note';$('mapping-fields').before(status);
    $('preview-placeholder').querySelector('p').textContent='修改下方数据，核对字段，然后更新预览。';
    const resize=document.createElement('div');resize.className='data-resizer';resize.tabIndex=0;resize.setAttribute('role','separator');resize.setAttribute('aria-label','调整数据面板高度');resize.setAttribute('aria-orientation','horizontal');resize.setAttribute('aria-valuemin','160');resize.setAttribute('aria-valuemax','600');resize.setAttribute('aria-valuenow','260');document.querySelector('.data-panel').prepend(resize);
    const height=n=>{n=Math.max(160,Math.min(n,Math.max(160,shell.clientHeight-260)));shell.style.setProperty('--data-height',n+'px');resize.setAttribute('aria-valuenow',String(Math.round(n)));if(gridReady)dataGrid.redraw();};
    resize.onpointerdown=e=>{if(e.button!==0)return;e.preventDefault();drag={y:e.clientY,height:document.querySelector('.data-panel').clientHeight};resize.setPointerCapture(e.pointerId);};resize.onpointermove=e=>{if(drag)height(drag.height+drag.y-e.clientY);};resize.onpointerup=resize.onpointercancel=()=>{drag=null;};resize.onkeydown=e=>{if(['ArrowUp','ArrowDown'].includes(e.key)){e.preventDefault();height(document.querySelector('.data-panel').clientHeight+(e.key==='ArrowUp'?20:-20));}};
    const dialog=document.createElement('dialog');dialog.id='transform-dialog';dialog.innerHTML='<div class="dialog-bar"><b>整理当前数据表</b><button id="transform-close" aria-label="关闭数据整理">×</button></div><div class="transform-content"><label>操作<select id="transform-kind">'+Object.entries(kinds).map(([k,v])=>`<option value="${k}">${v}</option>`).join('')+'</select></label><p id="transform-hint"></p><div id="transform-fields"></div><button id="transform-preview" class="small-button">预览处理结果</button><div id="transform-result" aria-live="polite"></div></div><div class="transform-footer"><span>应用前不会改变数据 · 应用后可以撤销</span><button id="transform-apply" class="button primary" disabled>应用到当前表</button></div>';document.body.append(dialog);
    organize.onclick=()=>{transformFields();dialog.showModal();};$('transform-kind').onchange=transformFields;$('transform-close').onclick=()=>dialog.close();$('transform-preview').onclick=previewTransform;$('transform-apply').onclick=applyTransform;
    $('transform-fields').addEventListener('input',()=>{prepared=null;$('transform-apply').disabled=true;$('transform-result').textContent='选项已变化，请重新预览。';});
    inspect('chart');
  }
  init();return {inspect,sync,remap,suggest,mappingStatus,showData};
})();
