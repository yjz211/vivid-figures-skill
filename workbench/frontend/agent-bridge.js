'use strict';
// Same-origin embedded editor: all chart edits still use the original editor pipeline.
window.VividBridge=(()=>{
  let muted=true,timer;
  const view=new URLSearchParams(location.search).get('view');
  function emit(type,detail={}){if(window.VIVID_EMBED)parent.postMessage({vivid:true,view,type,...detail},location.origin);}
  function snapshot(){signature();return {project:clone(project),job:lastRender?.signature===signature()?lastRender.job:null,selectedObject};}
  function changed(){if($('quick-palette'))$('quick-palette').value=project.settings.palette;if(muted)return;clearTimeout(timer);timer=setTimeout(()=>emit('change',snapshot()),220);}
  async function load(chart){
    muted=true;clearTimeout(timer);project=clone(chart.project);sampleProject=await api('/api/sample?id='+encodeURIComponent(project.template));
    objectManifest=null;selectedObject='';historyStack=[];redoStack=[];lastRender=null;page=0;refresh();
    if(chart.job){
      const result=await api('/api/jobs/'+chart.job);
      if(result.state==='done'){
        lastRender={signature:signature(),job:chart.job,base:result.base};
        $('output-image').src=result.base+'preview.png';$('output-image').hidden=false;$('preview-placeholder').hidden=true;
        $('open-image').href=result.base+'figure.png';$('open-image').hidden=false;
        $('method-notes').textContent=(result.notes||[]).join(' ');applyZoom(0);await loadObjects(result.base);
      }
    }
    changedBase();muted=false;emit('loaded',snapshot());
    if(!lastRender)await render();
  }
  function changedBase(){window.Studio?.sync();$('export-toggle').disabled=!lastRender;setStatus(lastRender?'当前结果已更新':'点击更新预览开始绘图',lastRender?'ready':'dirty');}
  function ready(){document.body.classList.add('agent-embedded');emit('ready');}
  function setup(){
    if(!window.VIVID_EMBED)return;
    const shell=$('editor-shell');shell.classList.add('data-folded','settings-folded');
    $('show-data').hidden=false;$('show-settings').hidden=false;
    $('show-settings').textContent='样式 / 对象';
    $('show-settings').onclick=()=>window.Studio?.inspect(selectedObject?'object':'chart');
    const palette=document.createElement('select');palette.id='quick-palette';palette.setAttribute('aria-label','快速切换配色');
    document.querySelector('.preview-tools').prepend(palette);
    palette.onchange=()=>{const source=$('palette-select');source.value=palette.value;source.dispatchEvent(new Event('change',{bubbles:true}));};
    const sync=()=>{palette.innerHTML=$('palette-select').innerHTML;palette.value=$('palette-select').value;};
    const observer=new MutationObserver(sync);observer.observe($('palette-select'),{childList:true,subtree:true});
    document.querySelector('.settings-panel').addEventListener('change',()=>queueMicrotask(sync));
    new ResizeObserver(()=>{if(zoom===0)applyZoom(0);}).observe($('canvas'));
    sync();
  }
  setup();
  return {ready,load:async chart=>{await load(chart);if($('quick-palette'))$('quick-palette').value=project.settings.palette;},snapshot,changed,clearSelection:()=>DirectEdit.clearSelection(),selection:id=>emit('selection',{id,name:objectManifest?.objects.find(o=>o.id===id)?.name||id}),render,export:()=>$('export-toggle').click(),status:text=>$('autosave-status').textContent=text};
})();
