'use strict';
// Native SVG stays intact. Screen gestures become physical point offsets,
// replayed by object_editor.py for PNG, PDF and SVG.
const DirectEdit=(()=>{
  let doc,svg,frame,selectedBox,hoverBox,toolbar,tip,dockHint,drag=null,base=new Map(),elements=new Map(),textRegions=[],axisTargets=new Map();
  const ns='http://www.w3.org/2000/svg';
  let explicitSelection=false,frameObserver;
  function compatible(){
    if(!lastRender||!objectManifest||objectManifest.renderer!=='matplotlib')return false;
    const old=JSON.parse(lastRender.signature),now=JSON.parse(signature());old[5]=null;now[5]=null;
    return JSON.stringify(old)===JSON.stringify(now);
  }
  const obj=id=>objectManifest?.objects.find(o=>o.id===id);
  function props(id){const item=obj(id),edit=project.object_edits?.[id];return {...item?.props,...(edit?.guard===objectManifest?.guard?edit.props:{})};}
  function commit(id,delta){
    if(!compatible())return toast('数据或全局设置已改变，请等待预览更新');
    remember();project.object_edits??={};
    if(project.object_edits[id]?.guard!==objectManifest.guard)project.object_edits[id]={guard:objectManifest.guard,props:{}};
    Object.assign(project.object_edits[id].props,delta);changed();objectFields();sync();queueLiveRender(650);
  }
  function init(){
    selectedBox=document.createElement('div');selectedBox.className='chart-selection';selectedBox.hidden=true;
    selectedBox.innerHTML='<i></i><i></i><i></i><i></i>';
    hoverBox=document.createElement('div');hoverBox.className='chart-hover';hoverBox.hidden=true;
    tip=document.createElement('div');tip.className='chart-tip';tip.hidden=true;
    toolbar=document.createElement('div');toolbar.className='chart-mini-tools';toolbar.id='chart-mini-tools';toolbar.hidden=true;
    toolbar.innerHTML='<strong id="mini-name"></strong><span id="mini-hint" class="sr-only"></span><div class="mini-controls"><input id="mini-text" aria-label="修改选中文字" title="文字内容；更多属性在右侧" maxlength="300"><input id="mini-size" type="number" aria-label="文字字号" title="字号（pt）" min="4" max="72"><input id="mini-color" type="color" aria-label="文字颜色" title="文字颜色"><button id="mini-reset" title="恢复标签原位置">复位</button><button id="mini-render" title="重新生成当前图">更新</button><button id="mini-close" aria-label="取消对象选择" title="取消选择（Esc）">×</button></div>';
    // Reserve a row outside the SVG. Selection must never cover other labels,
    // or change the frame size between pointerdown and pointerup.
    const dock=document.createElement('div');dock.className='chart-edit-dock';
    dockHint=document.createElement('span');dockHint.className='chart-edit-hint';dockHint.textContent='点选图中文字后在此编辑 · 拖动可调整位置';
    dock.append(dockHint,toolbar);document.querySelector('.preview-tools').after(dock);
    document.body.append(selectedBox,hoverBox,tip);
    for(const [id,key,type] of [['mini-text','text','text'],['mini-size','fontsize','number'],['mini-color','color','color']]){
      $(id).onchange=e=>{if(type==='number'&&(!e.target.value||!e.target.checkValidity()))return;commit(selectedObject,{[key]:type==='number'?Number(e.target.value):e.target.value});};
    }
    $('mini-reset').onclick=()=>commit(selectedObject,{offset_x:0,offset_y:0});$('mini-render').onclick=render;
    $('mini-close').onclick=()=>{explicitSelection=false;position();window.Studio?.inspect('chart');};
    window.addEventListener('resize',position);document.addEventListener('scroll',position,true);
    window.addEventListener('blur',()=>{cancel();sync();});
  }
  function hide(){[selectedBox,hoverBox,toolbar,tip].forEach(el=>{if(el)el.hidden=true;});if(dockHint)dockHint.hidden=false;cancel();}
  function boxFor(id){
    const el=elements.get(id);if(!el||frame.hidden)return null;
    const r=el.getBoundingClientRect(),f=frame.getBoundingClientRect();
    if(!r.width&&!r.height)return null;
    const style=getComputedStyle(frame),sx=f.width/(parseFloat(style.width)||f.width),sy=f.height/(parseFloat(style.height)||f.height);
    return {left:r.left*sx+f.left,top:r.top*sy+f.top,width:r.width*sx,height:r.height*sy};
  }
  function placeBox(box,r){box.hidden=!r;if(!r)return;const z=box.currentCSSZoom||1;Object.assign(box.style,{left:((r.left-4)/z)+'px',top:((r.top-4)/z)+'px',width:((r.width+8)/z)+'px',height:((r.height+8)/z)+'px'});}
  function strokeHighlight(hoverId){
    for(const [id,paths] of axisTargets)for(const path of paths)path.style.strokeOpacity=(id===hoverId||(explicitSelection&&id===selectedObject))?'.65':'0';
  }
  function position(){
    if(!toolbar||!frame||frame.hidden||!compatible()){hide();return;}
    if(!explicitSelection){selectedBox.hidden=true;toolbar.hidden=true;dockHint.hidden=false;strokeHighlight();return;}
    const r=boxFor(selectedObject);placeBox(selectedBox,r);toolbar.hidden=!r;
    dockHint.hidden=!!r;
    if(axisTargets.has(selectedObject))selectedBox.hidden=true;
    strokeHighlight();
  }
  function updateToolbar(){
    const item=obj(selectedObject);if(!item||!toolbar)return;
    const p=props(item.id),movable=item.kind==='text'&&'offset_x' in p;
    $('mini-name').textContent=item.name;$('mini-hint').textContent=movable?'拖动文字移动 · Shift 锁定方向 · Esc 取消':'已选中 · 在右侧调整属性';
    for(const [id,key] of [['mini-text','text'],['mini-size','fontsize'],['mini-color','color']]){
      $(id).hidden=!(key in p);if(key in p&&document.activeElement!==$(id))$(id).value=p[key];
    }
    $('mini-reset').hidden=!movable;
  }
  function sync(){
    if(!doc||!frame||frame.hidden)return;
    if(!compatible()){hide();return;}
    for(const [id,el] of elements){
      const item=obj(id),p=props(id),b=base.get(id);if(!item||!b)continue;
      if('offset_x' in p){
        const dx=(p.offset_x||0)-(item.props.offset_x||0),dy=(p.offset_y||0)-(item.props.offset_y||0);
        el.setAttribute('transform',`translate(${dx} ${dy}) ${b.transform}`);
      }
      if(p.color&&item.kind==='text')el.querySelectorAll('use,text').forEach(n=>n.style.fill=p.color);
    }
    updateToolbar();position();
  }
  function choose(id){selectObject(id);updateToolbar();position();}
  function localPoint(e,el){return new DOMPoint(e.clientX,e.clientY).matrixTransform(el.parentElement.getScreenCTM().inverse());}
  function targetAt(e){
    // Test lettering before background paths. SVG <use> glyphs, gaps and 3D
    // occlusion must all select the same label, regardless of event retargeting.
    const hits=[];
    for(const region of textRegions){
      const r=region.node.getBoundingClientRect();
      if(!r.width||!r.height||e.clientX<r.left-2||e.clientX>r.right+2||e.clientY<r.top-2||e.clientY>r.bottom+2)continue;
      const matrix=region.node.getScreenCTM();if(!matrix)continue;
      const inverse=matrix.inverse(),p=new DOMPoint(e.clientX,e.clientY).matrixTransform(inverse),b=region.bounds;
      const tx=2*Math.hypot(inverse.a,inverse.c),ty=2*Math.hypot(inverse.b,inverse.d);
      if(p.x<b.x-tx||p.x>b.x+b.width+tx||p.y<b.y-ty||p.y>b.y+b.height+ty)continue;
      const exact=p.x>=b.x&&p.x<=b.x+b.width&&p.y>=b.y&&p.y<=b.y+b.height;
      hits.push({id:region.id,exact,distance:Math.hypot((p.x-b.x-b.width/2)/Math.max(1,b.width),(p.y-b.y-b.height/2)/Math.max(1,b.height))});
    }
    hits.sort((a,b)=>Number(b.exact)-Number(a.exact)||a.distance-b.distance);
    if(hits.length)return hits[0].id;
    const path=e.composedPath?e.composedPath():[e.target];
    for(const node of path){const id=node.dataset?.vividObject;if(id&&obj(id)?.kind!=='text')return id;}
    return null;
  }
  function cancel(){
    if(!drag)return;
    drag.el.setAttribute('transform',drag.transform);drag=null;if(svg)svg.style.cursor='';
  }
  function bind(newFrame){
    hide();frame=newFrame;doc=frame.contentDocument;svg=doc?.documentElement;if(!svg)return;
    frameObserver?.disconnect();frameObserver=new ResizeObserver(()=>{hoverBox.hidden=true;tip.hidden=true;position();});frameObserver.observe(frame);
    base=new Map();elements=new Map();textRegions=[];axisTargets=new Map();
    svg.setAttribute('width','100%');svg.setAttribute('height','100%');svg.setAttribute('tabindex','0');svg.style.touchAction='none';svg.style.userSelect='none';
    const style=doc.createElementNS(ns,'style');style.textContent='[data-vivid-object]{cursor:inherit}';svg.append(style);
    for(const item of objectManifest.objects){
      let el=doc.getElementById(item.dom_id);
      const axis=['axis','colorbar'].includes(item.kind);
      // Older saved previews used duplicate axis gids for pane/grid/axis.
      if(axis&&!item.dom_id.endsWith('-line')){
        el=Array.from(doc.querySelectorAll('[id]')).filter(n=>n.id===item.dom_id).map(n=>n.querySelector(':scope > g[id^="line2d"] > path')).find(Boolean);
      }
      if(!el)continue;
      elements.set(item.id,el);base.set(item.id,{transform:el.getAttribute('transform')||''});el.dataset.vividObject=item.id;
      if(axis){
        // Only a 6 CSS-pixel stroke is selectable; panes, grids and label groups
        // receive no axis identity. Avoid a giant rectangular axis highlight.
        const paths=el.tagName==='path'?[el]:Array.from(el.querySelectorAll('path'));
        const targets=[];
        for(const path of paths){const hit=path.cloneNode(false);hit.removeAttribute('id');hit.removeAttribute('style');hit.dataset.vividObject=item.id;hit.dataset.vividAxisHit='true';
          for(const [key,value] of Object.entries({fill:'none',stroke:'#98517f','stroke-width':'6','stroke-opacity':'0','vector-effect':'non-scaling-stroke','pointer-events':'stroke'}))hit.setAttribute(key,value);
          path.parentElement.append(hit);targets.push(hit);
        }
        axisTargets.set(item.id,targets);
      }
      if(item.kind==='text'&&'offset_x' in item.props){
        el.dataset.vividDrag='true';
        const glyphs=Array.from(el.children).filter(n=>n.tagName==='g'&&n.hasAttribute('transform')&&n.querySelector('use,text'));
        for(const glyph of glyphs.length?glyphs:[el]){
          const bounds=glyph.getBBox();if(bounds.width&&bounds.height)textRegions.push({id:item.id,node:glyph,bounds});
        }
      }
    }
    const target=targetAt;
    doc.addEventListener('pointermove',e=>{
      if(drag){
        const q=localPoint(e,drag.el);let dx=q.x-drag.start.x,dy=q.y-drag.start.y;
        if(e.shiftKey){if(Math.abs(dx)>Math.abs(dy))dy=0;else dx=0;}
        drag.dx=Math.max(-720,Math.min(720,drag.offsetX+dx))-drag.offsetX;drag.dy=Math.max(-720,Math.min(720,drag.offsetY+dy))-drag.offsetY;
        if(Math.hypot(e.clientX-drag.screenX,e.clientY-drag.screenY)>3)drag.moved=true;
        if(drag.moved){drag.el.setAttribute('transform',`translate(${drag.dx} ${drag.dy}) ${drag.transform}`);position();$('mini-hint').textContent=`位置偏移 ${(drag.offsetX+drag.dx).toFixed(1)}, ${(drag.offsetY+drag.dy).toFixed(1)} pt`;}
        return;
      }
      if(!compatible())return;
      const id=target(e),r=id?boxFor(id):null;placeBox(hoverBox,r);tip.hidden=!r;strokeHighlight(id);
      if(axisTargets.has(id))hoverBox.hidden=true;
      svg.style.cursor=id?(obj(id)?.kind==='text'?'grab':'pointer'):'';
      if(r){const z=tip.currentCSSZoom||1;tip.textContent=obj(id)?.name+(obj(id)?.kind==='text'?' · 可拖动':'');tip.style.left=(Math.min(window.innerWidth-230,r.left)/z)+'px';tip.style.top=(Math.max(6,r.top-26)/z)+'px';}
    });
    doc.addEventListener('pointerleave',()=>{hoverBox.hidden=true;tip.hidden=true;strokeHighlight();});
    doc.addEventListener('pointerdown',e=>{
      if(e.button!==0||!compatible())return;const id=target(e);if(!id)return;
      choose(id);const item=obj(id),el=elements.get(id);if(item.kind!=='text'||!('offset_x' in item.props))return;
      e.preventDefault();svg.focus();svg.setPointerCapture(e.pointerId);hoverBox.hidden=true;tip.hidden=true;
      const p=props(id);drag={id,el,start:localPoint(e,el),screenX:e.clientX,screenY:e.clientY,offsetX:p.offset_x||0,offsetY:p.offset_y||0,dx:0,dy:0,moved:false,transform:el.getAttribute('transform')||''};
    });
    doc.addEventListener('pointerup',()=>{if(!drag)return;const d=drag;drag=null;if(d.moved)commit(d.id,{offset_x:Math.round((d.offsetX+d.dx)*100)/100,offset_y:Math.round((d.offsetY+d.dy)*100)/100});position();});
    doc.addEventListener('pointercancel',()=>{cancel();sync();});
    doc.addEventListener('click',e=>{if(compatible()){const id=target(e);if(id)choose(id);else{explicitSelection=false;position();window.Studio?.inspect('chart');}}});
    doc.addEventListener('keydown',e=>{
      if(e.key==='Escape'){e.preventDefault();if(!drag){explicitSelection=false;window.Studio?.inspect('chart');}cancel();sync();}
      if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='z'){e.preventDefault();(e.shiftKey?$('redo'):$('undo')).click();}
      if(['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(e.key)&&'offset_x' in props(selectedObject)){
        e.preventDefault();const p=props(selectedObject),step=e.shiftKey?10:1;
        commit(selectedObject,{offset_x:Math.max(-720,Math.min(720,(p.offset_x||0)+(e.key==='ArrowLeft'?-step:e.key==='ArrowRight'?step:0))),offset_y:Math.max(-720,Math.min(720,(p.offset_y||0)+(e.key==='ArrowUp'?-step:e.key==='ArrowDown'?step:0)))});
      }
    });
    sync();
  }
  return {init,bind,hide,sync,position,compatible,commit,updateToolbar,isDragging:()=>!!drag,activate:()=>{explicitSelection=true;}};
})();
