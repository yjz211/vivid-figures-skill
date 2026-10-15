'use strict';
// Data binding uses the same contracts and renderer as the manual editor and Agent.
window.VividBinding=(()=>{
  let info=null,sessionId='',bindings=new Map(),request=0,context=null;
  const norm=v=>String(v).trim().toLowerCase().replace(/[\s_（）()\-]/g,'');
  const numeric=(table,c)=>{const a=table.rows.map(r=>r[c]).filter(v=>v!==null&&String(v).trim()!=='');return a.length>0&&a.every(v=>Number.isFinite(Number(v)));};
  const specs=()=>info.contract.tables||[{key:'data',title:'绘图数据',kind:info.contract.family}];
  const dataset=id=>state.session.datasets.find(d=>d.id===id);
  function defaultFields(spec,d){
    const t=d.table,number=t.headers.map((_,i)=>i).filter(i=>numeric(t,i)),text=t.headers.map((_,i)=>i).filter(i=>!numeric(t,i));
    const exact=name=>{const hits=t.headers.map((h,i)=>norm(h)===norm(name)?i:-1).filter(i=>i>=0);return hits.length===1?hits[0]:-1;};
    if(spec.kind==='columns')return {columns:spec.headers.map(h=>exact(h))};
    if(['wide','matrix'].includes(spec.kind)){const category=text.length===1?text[0]:0;return {category,values:number.filter(i=>i!==category&&!/误差|标准差|标准误|error|stderr|^sd$|^se$/i.test(t.headers[i])),errors:{}};}
    if(spec.kind==='samples')return {group:text.length===1?text[0]:0,value:number[0]??-1};
    return {x:number[0]??-1,y:number[1]??-1,...(spec.kind==='xyz'?{z:number[2]??-1}:{})};
  }
  function options(t,value,empty='请选择列'){return `<option value="-1">${empty}</option>`+t.headers.map((h,i)=>`<option value="${i}" ${i===value?'selected':''}>${escapeHTML(h)}</option>`).join('');}
  function field(label,key,t,value){return `<label>${escapeHTML(label)}<select data-role="${key}">${options(t,value)}</select></label>`;}
  function draw(){
    el('binding-error').hidden=true;
    el('binding-tables').innerHTML=specs().map((spec,i)=>{
      const b=bindings.get(spec.key),d=dataset(b?.id),t=d?.table;
      let fields='';
      if(t){
        if(spec.kind==='columns')fields=spec.headers.map((h,i)=>field(h,String(i),t,b.fields.columns[i])).join('');
        else if(['wide','matrix'].includes(spec.kind)){
          fields=field('标签 / 横轴','category',t,b.fields.category)+`<fieldset class="binding-values"><legend>数值系列</legend>${t.headers.map((h,j)=>`<label class="binding-check"><input type="checkbox" data-value="${j}" ${b.fields.values.includes(j)?'checked':''} ${j===b.fields.category?'disabled':''}>${escapeHTML(h)}</label>`).join('')}</fieldset>`;
          if(['basic.grouped_bar','basic.line'].includes(info.contract.id))fields+=`<details class="binding-errors"><summary>误差列（可选；沿用提供的误差值）</summary>${b.fields.values.map(c=>`<label>${escapeHTML(t.headers[c])}<select data-error="${c}">${options(t,b.fields.errors[c]??-1,'无误差列')}</select></label>`).join('')}</details>`;
        }else{const labels={group:'分组列',value:'样本值',x:'X 数值',y:'Y 数值',z:'Z 数值'};fields=Object.entries(b.fields).map(([role,v])=>field(labels[role],role,t,v)).join('');}
      }
      return `<section class="binding-table" data-key="${escapeHTML(spec.key)}"><h3>${i+1}. ${escapeHTML(spec.title)}</h3><label>使用数据表<select data-source><option value="">请选择已导入的数据</option>${state.session.datasets.map(d=>`<option value="${d.id}" ${d.id===b?.id?'selected':''}>${escapeHTML(d.name)} · ${d.table.rows.length} 行</option>`).join('')}</select></label>${t?`<div class="binding-fields">${fields}</div><p class="binding-sample">首行：${t.rows[0].slice(0,8).map(escapeHTML).join(' · ')}${t.headers.length>8?' …':''}</p>`:''}</section>`;
    }).join('');
    el('binding-tables').querySelectorAll('[data-key]').forEach(section=>{
      const key=section.dataset.key,spec=specs().find(t=>t.key===key);
      section.querySelector('[data-source]').onchange=e=>{const d=dataset(e.target.value);bindings.set(key,{id:d?.id||'',fields:d?defaultFields(spec,d):{}});draw();};
      section.querySelectorAll('[data-role]').forEach(input=>input.onchange=e=>{
        const fields=bindings.get(key).fields,role=input.dataset.role,value=Number(e.target.value);
        if(spec.kind==='columns')fields.columns[Number(role)]=value;else fields[role]=value;
        if(role==='category'){fields.values=fields.values.filter(c=>c!==value);draw();}
      });
      section.querySelectorAll('[data-value]').forEach(input=>input.onchange=()=>{const f=bindings.get(key).fields,c=Number(input.dataset.value);f.values=input.checked?[...f.values,c].sort((a,b)=>a-b):f.values.filter(v=>v!==c);draw();});
      section.querySelectorAll('[data-error]').forEach(input=>input.onchange=()=>{const f=bindings.get(key).fields,c=input.dataset.error;if(Number(input.value)<0)delete f.errors[c];else f.errors[c]=Number(input.value);});
    });
    el('binding-create').disabled=!state.session.datasets.length;
  }
  async function open(tid){
    const current=++request,workspace=workspaceContext();sessionId=workspace.id;context=workspace;
    const fetched=await api('/api/agent/templates/'+encodeURIComponent(tid));
    if(current!==request||!sameWorkspace(workspace))return;
    const meta=await api('/api/templates');if(current!==request||!sameWorkspace(workspace))return;
    info=fetched;bindings=new Map();
    for(const spec of specs()){
      const d=dataset(state.dataset)||(state.session.datasets.length===1?state.session.datasets[0]:null);
      bindings.set(spec.key,{id:d?.id||'',fields:d?defaultFields(spec,d):{}});
    }
    el('gallery-dialog').close();el('binding-title').textContent=info.card.display_name;
    el('binding-purpose').textContent=state.session.datasets.length?'选好数据和字段后直接生成新图。不同数据表可以分别用于组合图的各个部分。':'请先从左侧导入 CSV / Excel，再用此模板绘图。';
    el('binding-name').value=info.card.display_name;
    el('binding-palette').innerHTML=Object.entries(meta.palettes).map(([id,p])=>`<option value="${id}">${escapeHTML(p.name)}</option>`).join('');el('binding-palette').value='pastel-girl';
    el('binding-requirements').innerHTML=(info.contract.requirements||[]).map(t=>`<li>${escapeHTML(t)}</li>`).join('');
    draw();showDialog('binding-dialog');
  }
  function payload(){
    let mapping;const result=[];
    for(const spec of specs()){
      const b=bindings.get(spec.key);if(!b?.id)throw Error('请选择「'+spec.title+'」使用的数据表。');
      const entry={table_key:spec.key,dataset_id:b.id},f=b.fields;
      if(spec.kind==='columns'){if(f.columns.some(c=>c<0))throw Error('请补全「'+spec.title+'」的字段对应。');entry.columns=f.columns;}
      else if(['wide','matrix'].includes(spec.kind)){if(f.category<0||!f.values.length)throw Error('请选择标签列和至少一个数值系列。');if(info.contract.family==='catalog')entry.columns=[f.category,...f.values];else mapping=f;}
      else{if(Object.values(f).some(v=>v<0))throw Error('请补全数据字段。');mapping=f;}
      result.push(entry);
    }
    const name=el('binding-name').value.trim()||info.card.display_name;
    return {template_id:info.contract.id,name,bindings:result,mapping,settings:{palette:el('binding-palette').value,title:name}};
  }
  document.addEventListener('DOMContentLoaded',()=>{
    el('binding-form').onsubmit=async e=>{
      e.preventDefault();el('binding-create').disabled=true;el('binding-error').hidden=true;
      const workspace=context;
      try{
        if(!sameWorkspace(workspace))throw Error('工作区已经切换，请重新选择模板。');
        const data=payload();await flush();if(state.conflict)throw Error('请先保留当前手动修改。');
        if(!sameWorkspace(workspace))return;
        const c=await api('/api/agent/sessions/'+workspace.id+'/bind',data);if(!sameWorkspace(workspace))return;
        el('binding-dialog').close();await refreshSession();if(sameWorkspace(workspace))await openChart(c.id);
      }catch(e){el('binding-error').textContent=e.message;el('binding-error').hidden=false;}finally{el('binding-create').disabled=false;}
    };
    el('binding-agent').onclick=()=>{
      if(!sameWorkspace(context))return;
      const ids=[...new Set([...bindings.values()].map(b=>b.id).filter(Boolean))];
      state.target='new';state.dataset=ids.length===1?ids[0]:'';paintWorkspace();
      const tables=ids.map(id=>'「'+dataset(id).name+'」').join('、');
      el('prompt').value='请使用'+(tables||'已导入的数据')+'，新建一张'+info.card.display_name+'（'+info.contract.id+'），配色用'+el('binding-palette').selectedOptions[0].textContent+'。请检查并对应数据字段后绘图。';
      el('binding-dialog').close();document.body.classList.remove('agent-hidden');el('prompt').focus();
    };
  });
  return {open};
})();
