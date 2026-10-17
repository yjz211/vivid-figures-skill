"""Resolve authored SVG into a browser-measured native PowerPoint scene."""
from pathlib import Path
import json
import math
from playwright.sync_api import sync_playwright
from pptx_geometry import _primitive, transform_subpaths
from pptx_text import TEXT_EXTRACT_JS
from pptx_markers import MARKER_EXTRACT_JS


SCENE_JS = r'''(extractText, extractMarkers) => {
 const root=document.querySelector('svg'), inv=root.getScreenCTM().inverse();
 const matrix=e=>{const m=inv.multiply(e.getScreenCTM());return [m.a,m.b,m.c,m.d,m.e,m.f]};
 const matArr=m=>[m.a,m.b,m.c,m.d,m.e,m.f];
 const own=e=>e.transform?.baseVal?.consolidate()?.matrix||root.createSVGMatrix();
 const attrs=e=>Object.fromEntries([...e.attributes].map(a=>[a.name,a.value]));
 const bbox=e=>{const b=e.getBBox(),m=inv.multiply(e.getScreenCTM());
  const p=[[b.x,b.y],[b.x+b.width,b.y],[b.x,b.y+b.height],[b.x+b.width,b.y+b.height]].map(p=>new DOMPoint(...p).matrixTransform(m));
  const x=Math.min(...p.map(p=>p.x)),y=Math.min(...p.map(p=>p.y));
  return [x,y,Math.max(...p.map(p=>p.x))-x,Math.max(...p.map(p=>p.y))-y]};
 function clips(e){
  let all=[];
  for(let node=e;node&&node!==root.parentElement;node=node.parentElement){
   const val=getComputedStyle(node).clipPath;
   if(!val||val==='none')continue;
   const id=val.match(/#([^"')]+)/)?.[1], clip=id&&document.getElementById(id);
   if(!clip||clip.tagName!=='clipPath')throw Error('Unsupported clip '+val);
   let base=inv.multiply(node.getScreenCTM());
   if(clip.getAttribute('clipPathUnits')==='objectBoundingBox'){
    const b=node.getBBox();base=base.translate(b.x,b.y).scaleNonUniform(b.width,b.height);
   }
   base=base.multiply(own(clip));
   const children=[];
   function walk(parent,m){for(const ch of parent.children){
    const cm=m.multiply(own(ch)),st=getComputedStyle(ch);
    if(st.clipPath!=='none')throw Error('Nested clipPath requires flattening');
    if(ch.tagName==='g')walk(ch,cm);
    else if(['path','rect','circle','ellipse','line','polyline','polygon'].includes(ch.tagName))
     children.push({tag:ch.tagName,attrs:attrs(ch),matrix:matArr(cm),fillRule:st.clipRule});
    else throw Error('Unsupported clip child '+ch.tagName);
   }}
   walk(clip,base);all.push(children);
  }
  return all;
 }
 const items=[];
 let counter=0;
 function walk(node){
  if(node.tagName==='svg'&&node!==root)throw Error('Nested SVG viewports require explicit flattening');
  if(['defs','style','metadata','title','desc','clipPath','mask'].includes(node.tagName))return;
  const st=getComputedStyle(node);
  if(st.display==='none'||Number(st.opacity)===0)return;
  if(st.filter!=='none'||st.maskImage!=='none'||st.mixBlendMode!=='normal')throw Error('Unsupported filter, mask or blend on '+node.tagName);
  if(node.tagName==='svg'||node.tagName==='g'||node.tagName==='a'){
   if(Number(st.opacity)!==1&&node.querySelectorAll('path,rect,circle,ellipse,line,polyline,polygon,text,use,image').length>1)throw Error('Overlapping group opacity must be flattened explicitly');
   for(const ch of node.children)walk(ch);return;
  }
  if(st.visibility==='hidden'||st.visibility==='collapse')return;
  const key=node.getAttribute('data-asset-key')||node.id||'svg-'+(++counter);
  const group_ids=[];for(let a=node.parentElement;a&&a!==root;a=a.parentElement)if(a.id&&a.tagName==='g')group_ids.push(a.id);
  const base={key,tag:node.tagName,attrs:attrs(node),matrix:matrix(node),bbox:bbox(node),rawClips:clips(node),group_ids};
  if(node.tagName==='text'){
   const records=extractText(node);for(const record of records)items.push({...base,...record,key,tag:'text',bbox:base.bbox});return;
  }
  if(!['path','rect','circle','ellipse','line','polyline','polygon'].includes(node.tagName))throw Error('Unsupported SVG element '+node.tagName);
  const markers=extractMarkers(node);
  base.style={fill:st.fill,stroke:st.stroke,fillOpacity:st.fillOpacity,strokeOpacity:st.strokeOpacity,opacity:st.opacity,
   strokeWidth:st.strokeWidth,linecap:st.strokeLinecap,linejoin:st.strokeLinejoin,miterlimit:st.strokeMiterlimit,
   dasharray:st.strokeDasharray,dashoffset:st.strokeDashoffset,fillRule:st.fillRule,vectorEffect:st.vectorEffect,paintOrder:st.paintOrder};
  for(let a=node.parentElement;a&&a instanceof SVGElement;a=a.parentElement)base.style.opacity*=Number(getComputedStyle(a).opacity);
  const mm=base.matrix,extent=parseFloat(st.strokeWidth)*Math.max(Math.hypot(mm[0],mm[1]),Math.hypot(mm[2],mm[3]))/2*Math.max(1,parseFloat(st.strokeMiterlimit));
  base.paint_bbox=st.stroke==='none'?base.bbox:[base.bbox[0]-extent,base.bbox[1]-extent,base.bbox[2]+2*extent,base.bbox[3]+2*extent];
  items.push(base);
  for(let i=0;i<markers.length;i++){
   const mark=markers[i];mark.key=key+':marker:'+i;mark.source_key=key;mark.group_ids=group_ids;
   mark.rawClips=[...base.rawClips,...(mark.rawClips||[])];items.push(mark);
  }
 }
 walk(root);
 return {viewBox:[root.viewBox.baseVal.x,root.viewBox.baseVal.y,root.viewBox.baseVal.width,root.viewBox.baseVal.height],items};
}'''


def path_string(subs):
    out=[]
    for sub in subs:
        out.append('M '+' '.join(map(str,sub['start'])))
        for command in sub['pts']:out.append(command[0]+' '+' '.join(map(str,command[1:])))
        if sub['closed']:out.append('Z')
    return ' '.join(out)


def extract_scene(svg, preview=None):
    svg=Path(svg)
    with sync_playwright() as p:
        browser=p.chromium.launch()
        page=browser.new_page(viewport={'width':1800,'height':1600},device_scale_factor=1)
        # The SVG is an authored local document; scripts and network are disabled.
        page.route('**/*',lambda route:route.abort() if route.request.url.startswith(('http:','https:')) else route.continue_())
        page.set_content('<!doctype html><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'; font-src data:; img-src data:"><style>html,body{margin:0;background:white}svg{display:block}</style>'+svg.read_text(encoding='utf-8'))
        page.evaluate('document.fonts.ready')
        scene=page.evaluate('() => ('+SCENE_JS+')('+TEXT_EXTRACT_JS+','+MARKER_EXTRACT_JS+')')
        if preview:page.locator('svg').screenshot(path=str(preview))
        browser.close()
    seen=set()
    for item in scene['items']:
        clips=[]
        for children in item.pop('rawClips'):
            clips.append({'children':[{'d':path_string(transform_subpaths(_primitive(child),child['matrix'])),
                                       'fillRule':child['fillRule']} for child in children]})
        item['clips']=clips
        if item['tag']!='text' and item['key'] in seen:raise ValueError('Duplicate SVG object key '+item['key'])
        if item['tag']!='text':seen.add(item['key'])
    return scene
