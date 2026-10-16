'use strict';
const $ = id => document.getElementById(id);
// Bump the app.js version in index.html when rebuilding previews in place.
const previewRevision=new URL(document.currentScript.src).searchParams.get('v')||'1';
const catalog = window.VIVID_CATALOG;
const cards = catalog.cards;
const editableIds=new Set(window.VIVID_EDITABLE_IDS||[]);
function editorURL(id){return (location.protocol==='file:'?'http://127.0.0.1:8766/':'')+'editor.html?template='+encodeURIComponent(id)+'&language='+state.language;}
const byId = new Map(cards.map(c => [c.id, c]));
const SIZE = 24;
let favorites;
try { favorites = new Set(JSON.parse(localStorage.getItem('vivid-workbench-favorites') || '[]').filter(id => byId.has(id))); }
catch { favorites = new Set(); }
function initialLanguage() {
  const requested=new URLSearchParams(location.search).get('language');
  if(['zh','en'].includes(requested))return requested;
  try {return localStorage.getItem('vivid-workbench-preview-language')==='en'?'en':'zh';}
  catch {return 'zh';}
}
let state = {category:'all', query:'', favorites:false, sort:'recommended', page:1, language:initialLanguage()};
function languageName(){return state.language==='en'?'英文':'中文';}
function previewURL(path){
  const localized=state.language==='en'?path.replace('assets/previews/','assets/previews-en/').replace('assets/thumbs/','assets/thumbs-en/'):path;
  return localized+(localized.includes('?')?'&':'?')+'v='+encodeURIComponent(previewRevision);
}
function syncLanguageControls(){
  document.querySelectorAll('[data-preview-language]').forEach(el=>el.value=state.language);
  $('preview-language-hint').textContent=`${languageName()}模板预览 · 选择模板后沿用此语言，界面保持中文。`;
  $('detail-preview-language').textContent=languageName()+'预览';
}
function setLanguage(value){
  if(!['zh','en'].includes(value))return;
  state.language=value;
  try {localStorage.setItem('vivid-workbench-preview-language',value);}catch{}
  const url=new URL(location.href);url.searchParams.set('language',value);
  history.replaceState(null,'',url);
  syncLanguageControls();render();
  if(current){showVariant(variant);$('use-template').href=editorURL(current.id);updateSource();}
}
let results = [], current = null, trigger = null, variant = 0, toastTimer;
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const normalize = s => s.toLocaleLowerCase().normalize('NFKC').replace(/[‐–—_]/g,' ').trim();
const synonyms = [['3d','三维','立体'],['heatmap','热力图','热图'],['ridge','ridgeline','山脊'],['violin','小提琴'],['scatter','散点'],['radar','雷达'],['correlation','相关性','相关'],['bar','柱状','柱形','条形'],['不确定性','置信区间','区间带'],['distribution','分布'],['trend','趋势','时序'],['network','网络'],['rose','玫瑰'],['回归','regression']];
for (const c of cards) {
  c._title = normalize([c.display_name,c.id,...c.aliases].join(' '));
  c._search = normalize([c._title,c.purpose,...c.tags,...c.data_requirements,...c.visual_features,c.composition,c.adaptation_notes].join(' '));
}
function toast(message) { $('toast').textContent=message; $('toast').hidden=false; clearTimeout(toastTimer); toastTimer=setTimeout(()=>$('toast').hidden=true,2300); }
function persistFavorites() {
  try { localStorage.setItem('vivid-workbench-favorites',JSON.stringify([...favorites])); }
  catch { toast('浏览器未允许保存，收藏仅保留在本次打开期间'); }
}
function toggleFavorite(id) {
  favorites.has(id) ? favorites.delete(id) : favorites.add(id);
  persistFavorites(); render(); if(current) updateFavorite();
}
function updateFavorite() { const yes=favorites.has(current.id); $('detail-favorite').textContent=yes?'★':'☆'; $('detail-favorite').setAttribute('aria-label',yes?'取消收藏':'收藏图表'); $('detail-favorite').setAttribute('aria-pressed',String(yes)); }
function rank(c, query) {
  if(!query) return 1;
  let score=0;
  for(const token of normalize(query).split(/\s+/).filter(Boolean)) {
    const aliases=synonyms.find(group=>group.includes(token)) || [token];
    if(!aliases.some(t=>c._search.includes(t))) return 0;
    score += c._title.includes(token)?10:aliases.some(t=>c._title.includes(t))?6:1;
  }
  return score;
}
function render() {
  $('favorite-count').textContent=favorites.size;
  $('total-count').textContent=cards.length;
  const scored = cards.filter(c=>(!state.favorites || favorites.has(c.id))&&(!$('editable-filter').checked||editableIds.has(c.id))).map(c=>({c,score:rank(c,state.query)})).filter(item=>item.score);
  $('categories').innerHTML=[{id:'all',name:'全部图表',icon:'▦'},...catalog.categories].map(cat=>{
    const count=scored.filter(({c})=>cat.id==='all'||c.categories.includes(cat.id)).length;
    return `<button class="category ${state.category===cat.id?'active':''}" data-category="${cat.id}" aria-pressed="${state.category===cat.id}"><span class="cat-icon" aria-hidden="true">${cat.icon}</span><span>${cat.name}</span><span>${count}</span></button>`;
  }).join('');
  results=scored.filter(({c})=>state.category==='all'||c.categories.includes(state.category)).sort((a,b)=>{
    if(state.sort==='number') return a.c.number-b.c.number;
    if(state.sort==='newest') return b.c.number-a.c.number;
    if(state.sort==='name') return a.c.display_name.localeCompare(b.c.display_name,'zh-CN');
    return b.score-a.score || a.c.feature_order-b.c.feature_order || a.c.number-b.c.number;
  }).map(item=>item.c);
  const pages=Math.ceil(results.length/SIZE); state.page=Math.max(1,Math.min(state.page,pages||1));
  $('library-tab').classList.toggle('active',!state.favorites); $('library-tab').setAttribute('aria-pressed',String(!state.favorites));
  $('favorites-tab').classList.toggle('active',state.favorites); $('favorites-tab').setAttribute('aria-pressed',String(state.favorites));
  $('result-title').textContent=state.favorites?'我的收藏':state.category==='all'?'全部图表':catalog.categories.find(c=>c.id===state.category).name;
  $('result-count').textContent=`${results.length} 张${state.query?'匹配':''}`;
  $('reset').hidden=state.category==='all'&&!state.query;
  $('clear-search').hidden=!state.query;
  $('active-query').hidden=!state.query;
  $('active-query').textContent=`关键词「${state.query}」 · 匹配名称、别名、用途和数据特征`;
  $('gallery').innerHTML=results.slice((state.page-1)*SIZE,state.page*SIZE).map(c=>`<article class="chart-card">
    <span class="card-number">NO.${String(c.number).padStart(3,'0')}</span>
    <button class="card-favorite ${favorites.has(c.id)?'selected':''}" data-favorite="${c.id}" aria-label="${favorites.has(c.id)?'取消收藏':'收藏'}${esc(c.display_name)}" aria-pressed="${favorites.has(c.id)}">${favorites.has(c.id)?'★':'☆'}</button>
    <button class="card-open" data-open="${c.id}" aria-label="查看${esc(c.display_name)}">
      <div class="card-preview"><img src="${previewURL(c.previews[0].thumb)}" alt="${esc(c.display_name)} · 粉彩少女${languageName()}预览" loading="lazy" width="520" height="350"><span class="preview-unavailable" role="status" hidden>${languageName()}预览暂不可用<br><small>可进入编辑器生成</small></span></div>
      ${c.previews.length>1?`<span class="card-variants">${c.previews.length} VIEWS</span>`:''}
      <div class="card-body"><h3>${esc(c.display_name)}</h3><p class="card-purpose">${esc(c.purpose)}</p><div class="card-bottom">${c.tags.slice(0,2).map(t=>`<span class="tag">${esc(t)}</span>`).join('')}<span class="card-arrow" aria-hidden="true">↗</span></div></div>
    </button>${editableIds.has(c.id)?`<a class="card-edit-link" href="${editorURL(c.id)}">修改数据，使用此模板 <span>→</span></a>`:''}</article>`).join('');
  $('empty').hidden=results.length>0;
  $('empty').querySelector('h3').textContent=state.favorites&&!favorites.size?'收藏夹还是空的':'暂时没有找到这张图';
  $('empty').querySelector('p').textContent=state.favorites&&!favorites.size?'点击图表右上角的星星，把想用的模板放在一起。':'换个关键词，或者清除分类后试试。';
  $('pagination').innerHTML=pages>1?`<span class="page-summary">${(state.page-1)*SIZE+1}–${Math.min(state.page*SIZE,results.length)} / ${results.length}</span><button data-page="${state.page-1}" aria-label="上一页" ${state.page===1?'disabled':''}>←</button>${Array.from({length:pages},(_,i)=>`<button data-page="${i+1}" class="${state.page===i+1?'active':''}" ${state.page===i+1?'aria-current="page"':''} aria-label="第 ${i+1} 页">${i+1}</button>`).join('')}<button data-page="${state.page+1}" aria-label="下一页" ${state.page===pages?'disabled':''}>→</button>`:'';
}
function setQuery(query) { state.query=query.trim(); state.page=1; $('search').value=query; render(); }
function reset() {state.category='all'; state.query=''; state.page=1; $('search').value='';render();}
function showVariant(n) {
  variant=n; const p=current.previews[n],url=previewURL(p.full),img=$('detail-image'),status=$('detail-preview-status');
  img.hidden=true;status.hidden=false;status.textContent=`正在加载${languageName()}预览…`;
  $('full-image').hidden=true;$('full-image').href=url;
  img.onload=()=>{img.hidden=false;status.hidden=true;$('full-image').hidden=false;};
  img.onerror=()=>{img.hidden=true;status.hidden=false;status.textContent=`${languageName()}预览暂不可用。可进入编辑器生成，或检查本地预览资源。`;$('full-image').hidden=true;};
  img.alt=`${current.display_name}，粉彩少女，${languageName()}，第 ${n+1} 张预览`;img.src=url;
  $('image-selector').innerHTML=current.previews.length>1?current.previews.map((_,i)=>`<button class="${i===n?'active':''}" data-variant="${i}" aria-pressed="${i===n}">预览 ${i+1}</button>`).join(''):'';
}
function setTab(name, focus=false) {
  const info=name==='info';
  $('info-content').hidden=!info; $('code-content').hidden=info;
  for(const type of ['info','code']) {const active=(type===name);$(type+'-tab').setAttribute('aria-selected',String(active)); $(type+'-tab').tabIndex=active?0:-1;}
  if(focus) $(name+'-tab').focus();
}
function updateSource() {
  const mode=$('source-mode').value;
  $('source-code').textContent=mode==='preview'?current.code:current.original;
  $('download-python').href=mode==='preview'?current.source_path:current.original_path;
  $('download-python').download=current.id+(mode==='preview'?'.pastel.py':'.original.py');
  $('code-note').textContent=mode==='preview'?(state.language==='en'?'共享模板源码。下载模板包后运行 python run_demo.py --language en 生成英文示例；辅助模块与语言映射已包含在包内。':'完整模板源码，已适配粉彩少女；辅助模块与示例启动器在下载包内。'):'库内源码原样保留；固定色或默认配色可能与粉彩预览不同。';
}
function openDetail(id, opener=null) {
  current=byId.get(id); if(!current) return;
  if(opener) trigger=opener;
  $('detail-number').textContent=`NO.${String(current.number).padStart(3,'0')} / ${current.id}`;
  $('detail-title').textContent=current.display_name;
  $('detail-kind').textContent=current.kind==='complete-template'||current.id.startsWith('template.')?'完整组合模板':'图表源码模板';
  $('detail-tags').innerHTML=current.tags.map(t=>`<button class="tag" data-tag="${esc(t)}">${esc(t)}</button>`).join('');
  $('purpose').textContent=current.purpose;
  $('requirements').innerHTML=current.data_requirements.map(t=>`<li>${esc(t)}</li>`).join('');
  $('features').innerHTML=current.visual_features.map(t=>`<li>${esc(t)}</li>`).join('');
  $('adaptation').textContent=current.adaptation_notes||current.composition;
  $('download-bundle').href=current.bundle; $('download-bundle').download=current.id+'.zip';
  $('use-template').hidden=!editableIds.has(current.id);$('use-template').href=editorURL(current.id);
  const position=results.findIndex(c=>c.id===id);
  $('detail-position').textContent=position>=0?`${position+1} / ${results.length}`:'';
  $('prev-chart').disabled=position<=0; $('next-chart').disabled=position<0||position===results.length-1;
  $('source-mode').value='preview'; updateSource(); updateFavorite(); setTab('info'); showVariant(0);
  $('info-content').scrollTop=0;
  if(!$('detail').open) {$('detail').showModal();document.body.style.overflow='hidden';}
  $('detail').scrollTop=0;
  history.replaceState(null,'',location.pathname+location.search+'#'+encodeURIComponent(id));
}
function closeDetail() {$('detail').close();}
$('detail').addEventListener('close',()=>{ document.body.style.overflow='';current=null; history.replaceState(null,'',location.pathname+location.search); if(trigger?.isConnected) trigger.focus();});
$('detail').addEventListener('click',e=>{if(e.target===$('detail')) {const r=$('detail').getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom) closeDetail();}});
$('close-detail').onclick=closeDetail;
$('search').addEventListener('input',e=>setQuery(e.target.value));
$('clear-search').onclick=()=>{setQuery('');$('search').focus();};
$('reset').onclick=reset;
$('empty-reset').onclick=()=>{state.favorites=false;reset();};
$('sort').onchange=e=>{state.sort=e.target.value;state.page=1;render();};
$('editable-filter').onchange=()=>{state.page=1;render();};
$('library-tab').onclick=()=>{state.favorites=false;state.page=1;render();};
$('favorites-tab').onclick=()=>{state.favorites=true;state.page=1;render();};
$('info-tab').onclick=()=>setTab('info'); $('code-tab').onclick=()=>setTab('code');
document.querySelector('.detail-tabs').addEventListener('keydown',e=>{if(['ArrowLeft','ArrowRight'].includes(e.key)){e.preventDefault();setTab($('info-content').hidden?'info':'code',true);}});
$('source-mode').onchange=updateSource;
function downloadBytes(base64,filename,type) {
  const bytes=Uint8Array.from(atob(base64),c=>c.charCodeAt(0));
  const url=URL.createObjectURL(new Blob([bytes],{type}));
  const anchor=document.createElement('a');anchor.href=url;anchor.download=filename;anchor.style.display='none';
  document.body.appendChild(anchor);anchor.click();anchor.remove();setTimeout(()=>URL.revokeObjectURL(url),30000);
}
$('download-python').onclick=e=>{
  e.preventDefault();const original=$('source-mode').value==='original';
  downloadBytes(original?current.original_base64:current.code_base64,current.id+(original?'.original.py':'.pastel.py'),'text/x-python');
};
const pendingDownloads=new Set();
$('download-bundle').onclick=e=>{
  e.preventDefault();const id=current.id;if(pendingDownloads.has(id))return;
  pendingDownloads.add(id);$('download-bundle').setAttribute('aria-busy','true');
  const script=document.createElement('script');script.src=`assets/downloads/${id}.js`;
  const done=()=>{script.remove();pendingDownloads.delete(id);$('download-bundle').removeAttribute('aria-busy');};
  script.onload=()=>{
    try{downloadBytes(window.VIVID_ZIPS[id],id+'.zip','application/zip');delete window.VIVID_ZIPS[id];toast('模板包已准备好，请查看浏览器下载');}
    catch{toast('下载未完成，请确认 assets 文件夹完整');}
    done();
  };
  script.onerror=()=>{done();toast('模板包未找到，请确认 assets 文件夹完整');};
  document.head.appendChild(script);
};
$('detail-favorite').onclick=()=>toggleFavorite(current.id);
function navigate(offset) {const pos=results.findIndex(c=>c.id===current?.id); if(pos>=0&&results[pos+offset]) openDetail(results[pos+offset].id);}
$('prev-chart').onclick=()=>navigate(-1);$('next-chart').onclick=()=>navigate(1);
document.addEventListener('click',e=>{
  const button=e.target.closest('button');if(!button)return;
  if(button.dataset.category){state.category=button.dataset.category;state.page=1;render();}
  if(button.dataset.query){state.category='all';setQuery(button.dataset.query);}
  if(button.dataset.open)openDetail(button.dataset.open,button);
  if(button.dataset.favorite)toggleFavorite(button.dataset.favorite);
  if(button.dataset.page){state.page=Number(button.dataset.page);render();$('gallery').scrollIntoView({block:'start',behavior:'instant'});}
  if(button.dataset.variant!==undefined)showVariant(Number(button.dataset.variant));
  if(button.dataset.tag){const query=button.dataset.tag;closeDetail();state.category='all';setQuery(query);}
});
$('copy-code').onclick=async()=>{
  const text=$('source-code').textContent;
  try {await navigator.clipboard.writeText(text);toast('完整源码已复制');}
  catch {
    const field=document.createElement('textarea'); field.value=text; field.style.cssText='position:fixed;left:0;top:0;width:1px;height:1px;opacity:0';$('detail').appendChild(field);field.select();
    const success=document.execCommand('copy'); field.remove();toast(success?'完整源码已复制':'请使用「单独下载 .py」保存源码');
  }
};
document.addEventListener('keydown',e=>{
  if(e.key==='/'&&!$('detail').open&&!['INPUT','TEXTAREA','SELECT'].includes(document.activeElement.tagName)){e.preventDefault();$('search').focus();}
});
document.querySelectorAll('[data-preview-language]').forEach(el=>el.addEventListener('change',e=>setLanguage(e.target.value)));
$('gallery').addEventListener('error',e=>{
  if(e.target.tagName!=='IMG')return;
  e.target.hidden=true;const message=e.target.parentElement.querySelector('.preview-unavailable');if(message)message.hidden=false;
},true);
$('gallery').addEventListener('load',e=>{
  if(e.target.tagName!=='IMG')return;
  e.target.hidden=false;const message=e.target.parentElement.querySelector('.preview-unavailable');if(message)message.hidden=true;
},true);
syncLanguageControls();
$('swatches').innerHTML=catalog.colors.map(c=>`<i style="background:${c}" title="${c}"></i>`).join('');
render();
const hash=decodeURIComponent(location.hash.slice(1)); if(byId.has(hash))openDetail(hash);
