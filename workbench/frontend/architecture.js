'use strict';
(() => {
  const $ = id => document.getElementById(id);
  const data = window.VIVID_ARCHITECTURE;
  const base = window.VIVID_ARCHITECTURE_BASE ?? 'architecture-assets/';
  if (!data || !Array.isArray(data.assets)) { $('result-count').textContent='资源索引未加载，请确认 architecture-data.js 在本地包内。'; return; }
  const assets=data.assets, byCode=new Map(assets.map(a=>[a.code,a]));
  const families={'composite':'组合总览','comparison':'方案对照','layered':'分层结构','deployment':'部署拓扑','hierarchical-control':'层级控制','control-loop':'反馈闭环','pipeline':'串行流水线','matrix':'矩阵组织','parallel-fusion':'并行与融合','offline-online':'离线与在线','artifact-pipeline':'阶段与产物','control-data':'控制与数据','network':'网络关系','hub-spoke':'中心与分支','host-device':'主机与设备'};
  const familyName=f=>families[f]||f, kindName=k=>k==='code'?'代码构图':'矢量编辑';
  const escape=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const url=path=>base+String(path||'').split('/').map(encodeURIComponent).join('/');
  const state={family:'',query:'',kind:'',sort:'number',page:1,favorites:false};
  const pageSize=24;
  let favorites=new Set(),current=null,returnFocus=null;
  try{favorites=new Set(JSON.parse(localStorage.getItem('vivid-architecture-favorites')||'[]').filter(c=>byCode.has(c)));}catch{}
  const searchIndex=new Map(assets.map(a=>[a.code,(JSON.stringify(a)+' '+familyName(a.family)+' '+kindName(a.kind)).toLocaleLowerCase()]));
  const list=(title,items,ordered=false)=>!items?.length?'':`<h3>${escape(title)}</h3><${ordered?'ol':'ul'}>${items.map(x=>`<li>${escape(x)}</li>`).join('')}</${ordered?'ol':'ul'}>`;
  const paragraph=(title,text)=>text?`<h3>${escape(title)}</h3><p>${escape(text)}</p>`:'';
  function filtered(){let out=assets.filter(a=>(!state.family||a.family===state.family)&&(!state.kind||a.kind===state.kind)&&(!state.favorites||favorites.has(a.code))&&state.query.trim().toLocaleLowerCase().split(/\s+/).every(q=>searchIndex.get(a.code).includes(q)));out.sort((a,b)=>state.sort==='name'?a.title.localeCompare(b.title,'zh'):state.sort==='newest'?b.code.localeCompare(a.code):a.code.localeCompare(b.code));return out;}
  function favoriteButton(code,cls='card-favorite'){const active=favorites.has(code);return `<button class="${cls}${active?' selected':''}" data-favorite="${escape(code)}" aria-label="${active?'取消收藏':'收藏'} ${escape(code)}" aria-pressed="${active}">${active?'★':'☆'}</button>`;}
  function render(){
    const matches=filtered(),pages=Math.max(1,Math.ceil(matches.length/pageSize));state.page=Math.min(state.page,pages);
    $('favorite-count').textContent=favorites.size;$('favorites-tab').classList.toggle('active',state.favorites);$('favorites-tab').setAttribute('aria-pressed',String(state.favorites));
    $('result-title').textContent=state.favorites?'我的架构收藏':state.family?familyName(state.family):'全部架构图';$('result-count').textContent=`${matches.length} 套`;
    const hasFilter=!!(state.family||state.kind||state.query||state.favorites);$('reset').hidden=!hasFilter;$('clear-search').hidden=!state.query;$('active-query').hidden=!hasFilter;
    $('active-query').textContent=[state.query&&`关键词：${state.query}`,state.family&&familyName(state.family),state.kind&&kindName(state.kind),state.favorites&&'已收藏'].filter(Boolean).join(' / ');
    document.querySelectorAll('[data-family]').forEach(b=>{const active=b.dataset.family===state.family;b.classList.toggle('active',active);b.setAttribute('aria-pressed',String(active));});
    $('gallery').innerHTML=matches.slice((state.page-1)*pageSize,state.page*pageSize).map(a=>`<article class="chart-card"><span class="card-number">${escape(a.code)}</span>${favoriteButton(a.code)}<button class="card-open" data-open="${escape(a.code)}" aria-label="查看 ${escape(a.code)} ${escape(a.title)}"><div class="card-preview"><img loading="lazy" src="${escape(url(a.preview))}" alt="${escape(a.title)}"></div><div class="card-body"><h3>${escape(a.title)}</h3><p class="card-purpose">${escape(a.guide?.summary)}</p><div class="card-bottom"><span class="tag">${escape(familyName(a.family))}</span><span class="tag">${kindName(a.kind)}</span><span class="card-arrow" aria-hidden="true">↗</span></div></div></button></article>`).join('');
    $('empty').hidden=!!matches.length;
    $('pagination').innerHTML=matches.length?`<span class="page-summary">第 ${state.page} / ${pages} 页 · 每页 ${pageSize} 套</span><button data-page="${state.page-1}" ${state.page===1?'disabled':''} aria-label="上一页">←</button>${Array.from({length:pages},(_,i)=>`<button data-page="${i+1}" class="${state.page===i+1?'active':''}" ${state.page===i+1?'aria-current="page"':''}>${i+1}</button>`).join('')}<button data-page="${state.page+1}" ${state.page===pages?'disabled':''} aria-label="下一页">→</button>`:'';
  }
  function reset(){Object.assign(state,{family:'',query:'',kind:'',page:1,favorites:false});$('search').value='';$('kind').value='';render();}
  function toggleFavorite(code){if(favorites.has(code))favorites.delete(code);else favorites.add(code);try{localStorage.setItem('vivid-architecture-favorites',JSON.stringify([...favorites]));}catch{}render();if(current)syncDetailFavorite();}
  function syncDetailFavorite(){const active=favorites.has(current.code);$('detail-favorite').textContent=active?'★':'☆';$('detail-favorite').setAttribute('aria-pressed',String(active));$('detail-favorite').setAttribute('aria-label',active?'取消收藏架构图':'收藏架构图');}
  function selectTab(name,focus=false){['overview','editing','parts'].forEach(n=>{const active=n===name;$(n+'-panel').hidden=!active;$(n+'-tab').setAttribute('aria-selected',String(active));$(n+'-tab').tabIndex=active?0:-1;});if(focus)$(name+'-tab').focus();}
  function showDetail(code,updateHash=true){
    const a=byCode.get(code);if(!a)return;current=a;const g=a.guide||{};
    $('detail-number').textContent=a.code;$('detail-title').textContent=a.title;$('detail-kind').textContent=`${familyName(a.family)} / ${kindName(a.kind)}`;$('detail-image').src=url(a.preview);$('detail-image').alt=a.title;$('full-image').href=url(a.preview);
    $('detail-tags').innerHTML=(a.tags||[]).map(t=>`<span class="tag">${escape(t)}</span>`).join('');
    $('overview-panel').innerHTML=paragraph('这张图表达什么',g.summary)+list('适合的场景',g.suitable_for)+`<div class="boundary">${list('使用边界',g.not_suitable_for)}</div>`+list('阅读顺序',g.reading_order,true)+Object.entries(g.design||{}).map(([k,v])=>paragraph(({layout:'布局',shapes:'图元',connectors:'连接关系',color:'配色语义',typography:'文字与层级'})[k]||k,v)).join('');
    $('editing-panel').innerHTML=list('改写步骤',g.adaptation,true)+Object.entries(g.editing||{}).map(([k,v])=>paragraph(({entry:'从哪里开始',configurable:'可以配置什么',code_required:'需要修改代码的部分',fonts:'字体与尺寸'})[k]||k,v)).join('')+Object.entries(g.example||{}).map(([k,v])=>paragraph(({scenario:'情景示例',mapping:'语义映射',structural_changes:'结构改动'})[k]||k,v)).join('')+list('完成后检查',g.checks);
    $('parts-tab').textContent=`部件 ${g.parts?.length||0}`;
    $('parts-panel').innerHTML=`<p>按部件语义改写；移动后检查跨部件连线与标签位置。</p>`+(g.parts||[]).map(p=>`<article class="part-card">${p.image?`<a href="${escape(url(p.image))}" target="_blank" rel="noopener" aria-label="打开 ${escape(p.name)} SVG"><img loading="lazy" src="${escape(url(p.image))}" alt="${escape(p.name)}"></a>`:''}<div class="part-info"><h3>${escape(p.name)}</h3><span class="mono">${escape(p.id)}</span><p>${escape(p.meaning)}</p><p class="part-adaptation">${escape(p.adaptation)}</p>${!p.image?'<p>此部件由构图代码生成，参见使用说明。</p>':''}</div></article>`).join('');
    $('resource-links').innerHTML=Object.entries(a.links||{}).map(([name,path])=>`<a href="${escape(url(path))}" target="_blank" rel="noopener">${escape(name)}<span aria-hidden="true">↗</span></a>`).join('');
    if(location.protocol!=='file:'){const edit=document.createElement('a');edit.href='architecture-editor.html?asset='+encodeURIComponent(a.code);edit.textContent='打开模块编辑工作台 →';edit.style.background='var(--green)';$('resource-links').prepend(edit);const agent=document.createElement('a');agent.href='architecture-agent.html?asset='+encodeURIComponent(a.code);agent.textContent='交给架构图 Agent →';agent.style.background='var(--pink)';$('resource-links').prepend(agent);}
    syncDetailFavorite();selectTab('overview');
    const matching=filtered(),sequence=matching.some(x=>x.code===code)?matching:assets,index=sequence.findIndex(x=>x.code===code);
    $('detail-position').textContent=`${index+1} / ${sequence.length}`;$('prev-chart').disabled=index===0;$('next-chart').disabled=index===sequence.length-1;
    $('prev-chart').onclick=()=>showDetail(sequence[index-1]?.code);$('next-chart').onclick=()=>showDetail(sequence[index+1]?.code);
    if(!$('detail').open){returnFocus=document.activeElement;$('detail').showModal();document.body.style.overflow='hidden';} $('detail').scrollTop=0;
    if(updateHash&&location.hash!=='#'+code){try{history.replaceState(null,'','#'+code);}catch{location.hash=code;}}
  }
  function clearHash(){try{history.replaceState(null,'',location.pathname+location.search);}catch{location.hash='';}}
  $('close-detail').onclick=()=>$('detail').close();$('detail').addEventListener('close',()=>{document.body.style.overflow='';current=null;clearHash();if(returnFocus?.isConnected)returnFocus.focus();});
  $('detail').addEventListener('click',e=>{if(e.target===$('detail')){const r=$('detail').getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)$('detail').close();}});
  document.addEventListener('click',e=>{const f=e.target.closest('[data-favorite]');if(f){toggleFavorite(f.dataset.favorite);return;}const open=e.target.closest('[data-open]');if(open){showDetail(open.dataset.open);return;}const family=e.target.closest('[data-family]');if(family){state.family=family.dataset.family;state.page=1;render();return;}const page=e.target.closest('[data-page]');if(page&&!page.disabled){state.page=Number(page.dataset.page);render();$('gallery').scrollIntoView({block:'start'});return;}const query=e.target.closest('[data-query]');if(query){state.query=query.dataset.query;$('search').value=state.query;state.page=1;render();}});
  $('search').addEventListener('input',e=>{state.query=e.target.value;state.page=1;render();});$('clear-search').onclick=()=>{state.query='';$('search').value='';state.page=1;render();$('search').focus();};
  $('kind').onchange=e=>{state.kind=e.target.value;state.page=1;render();};$('sort').onchange=e=>{state.sort=e.target.value;state.page=1;render();};$('reset').onclick=reset;$('empty-reset').onclick=reset;$('favorites-tab').onclick=()=>{state.favorites=!state.favorites;state.page=1;render();};$('detail-favorite').onclick=()=>current&&toggleFavorite(current.code);
  ['overview','editing','parts'].forEach((n,i,all)=>{$(n+'-tab').onclick=()=>selectTab(n);$(n+'-tab').onkeydown=e=>{if(['ArrowLeft','ArrowRight','Home','End'].includes(e.key)){e.preventDefault();const next=e.key==='Home'?0:e.key==='End'?all.length-1:(i+(e.key==='ArrowRight'?1:-1)+all.length)%all.length;selectTab(all[next],true);}};});
  document.addEventListener('keydown',e=>{if(e.key==='/'&&!$('detail').open&&!['INPUT','TEXTAREA','SELECT'].includes(document.activeElement.tagName)){e.preventDefault();$('search').focus();}});
  window.addEventListener('hashchange',()=>{const code=decodeURIComponent(location.hash.slice(1));if(byCode.has(code))showDetail(code,false);else if($('detail').open)$('detail').close();});
  $('total-count').textContent=assets.length;$('hero-count').textContent=assets.length;$('parts-count').textContent=`${data.parts_count??assets.reduce((n,a)=>n+(a.guide?.parts?.length||0),0)} 条部件说明 · ${data.preview_parts_count??0} 个导出预览`;
  $('workflow-link').href=url('WORKFLOW.md');$('attribution-link').href=url('ATTRIBUTION.md');
  const counts=new Map();assets.forEach(a=>counts.set(a.family,(counts.get(a.family)||0)+1));
  $('categories').innerHTML=`<button class="category active" data-family="" aria-pressed="true"><span class="cat-icon" aria-hidden="true">▦</span>全部结构<span>${assets.length}</span></button>`+[...counts].sort((a,b)=>b[1]-a[1]).map(([f,n])=>`<button class="category" data-family="${escape(f)}" aria-pressed="false"><span class="cat-icon" aria-hidden="true">${f==='pipeline'?'→':f==='control-loop'?'↻':'▧'}</span>${escape(familyName(f))}<span>${n}</span></button>`).join('');
  render();const code=decodeURIComponent(location.hash.slice(1));if(byCode.has(code))showDetail(code,false);
})();
