"""Expand Vivid's SVG arrow markers into ordinary editable geometry records.

Only straight line/polyline and single-subpath M/L/H/V hosts are supported.
Unsupported marker contents/orientation/placement fail explicitly.
"""

MARKER_EXTRACT_JS = r'''(element) => {
 const root=element.ownerSVGElement, hostStyle=getComputedStyle(element);
 if(hostStyle.markerMid && hostStyle.markerMid!=='none')throw Error('marker-mid is not supported by native PPT export');
 if([hostStyle.markerStart,hostStyle.markerEnd].every(v=>!v||v==='none'))return [];
 const number=(value,fallback=0)=>{
  if(value===null||value===undefined||value==='')return fallback;
  if(!/^[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?(?:px)?$/.test(String(value).trim()))throw Error('Marker length must resolve to a number: '+value);
  return parseFloat(value);
 };
 const arr=m=>[m.a,m.b,m.c,m.d,m.e,m.f];
 const dm=m=>new DOMMatrix(arr(m));
 const own=e=>e.transform?.baseVal?.consolidate()?.matrix?dm(e.transform.baseVal.consolidate().matrix):new DOMMatrix();
 const mat=dm(root.getScreenCTM()).inverse().multiply(dm(element.getScreenCTM()));
 const attrs=e=>Object.fromEntries([...e.attributes].map(a=>[a.name,a.value]));
 const point=(m,p)=>new DOMPoint(...p).matrixTransform(m);
 let points=[];
 if(element.tagName==='line')points=[[element.x1.baseVal.value,element.y1.baseVal.value],[element.x2.baseVal.value,element.y2.baseVal.value]];
 else if(element.tagName==='polyline')points=[...Array(element.points.numberOfItems)].map((_,i)=>{const p=element.points.getItem(i);return[p.x,p.y]});
 else if(element.tagName==='path'){
  const d=element.getAttribute('d')||'';
  // Library connectors are polylines. Reject curves/compound/closed paths,
  // rather than estimating tangent angles or losing per-subpath markers.
  if(/[a-df-gi-kno-uw-z]/i.test(d))throw Error('Marker path host supports only open M/L/H/V segments');
  const t=d.match(/[MLHVmlhv]|[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?/g)||[];
  let i=0,cmd=null,x=0,y=0,move=false;
  while(i<t.length){
   if(/^[MLHVmlhv]$/.test(t[i]))cmd=t[i++];
   if(!cmd)throw Error('Invalid marker host path');
   const relative=cmd===cmd.toLowerCase(), upper=cmd.toUpperCase();
   const take=()=>{const v=Number(t[i++]);if(!Number.isFinite(v))throw Error('Invalid marker path coordinate');return v};
   if(upper==='M'||upper==='L'){
    if(upper==='M'&&move)throw Error('Compound marker host path is unsupported');
    const xx=take(),yy=take();x=relative?x+xx:xx;y=relative?y+yy:yy;
    if(upper==='M'){move=true;cmd=relative?'l':'L'}
   }else if(upper==='H'){const xx=take();x=relative?x+xx:xx}
   else if(upper==='V'){const yy=take();y=relative?y+yy:yy}
   points.push([x,y]);
  }
 }else throw Error('Markers on '+element.tagName+' are not supported');
 if(points.length<2)throw Error('Marker host has no usable segment');
 const tangent=position=>{
  const p=position==='start'?points[0]:points.at(-1);
  const candidates=position==='start'?points.slice(1):points.slice(0,-1).reverse();
  const q=candidates.find(q=>Math.hypot(q[0]-p[0],q[1]-p[1])>1e-10);
  if(!q)throw Error('Zero-length marker host direction is unsupported');
  return {p,angle:Math.atan2(position==='start'?q[1]-p[1]:p[1]-q[1],position==='start'?q[0]-p[0]:p[0]-q[0])*180/Math.PI};
 };
 let opacity=Number(hostStyle.opacity);
 for(let a=element.parentElement;a&&a instanceof SVGElement;a=a.parentElement)opacity*=Number(getComputedStyle(a).opacity);
 const result=[];
 for(const position of ['start','end']){
  const value=position==='start'?hostStyle.markerStart:hostStyle.markerEnd;
  if(!value||value==='none')continue;
  const id=value.match(/#([^"')]+)/)?.[1], marker=id&&document.getElementById(id);
  if(!marker||marker.tagName!=='marker')throw Error('Unresolved SVG marker '+value);
  const ms=getComputedStyle(marker);
  if(Number(ms.opacity)!==1||ms.filter!=='none'||ms.maskImage!=='none'||ms.clipPath!=='none')throw Error('Marker-level opacity/filter/mask/clip is unsupported');
  const width=number(marker.getAttribute('markerWidth'),3),height=number(marker.getAttribute('markerHeight'),3);
  if(width<=0||height<=0)continue;
  const units=marker.getAttribute('markerUnits')||'strokeWidth';
  if(!['strokeWidth','userSpaceOnUse'].includes(units))throw Error('Unsupported markerUnits '+units);
  const unitScale=units==='strokeWidth'?number(hostStyle.strokeWidth,1):1;
  if(unitScale===0)continue;
  let view=new DOMMatrix();
  if(marker.hasAttribute('viewBox')){
   const vb=marker.viewBox.baseVal;
   if(vb.width<=0||vb.height<=0)throw Error('Invalid marker viewBox');
   const par=(marker.getAttribute('preserveAspectRatio')||'xMidYMid meet').trim().split(/\s+/);
   if(par[0]==='defer')par.shift();
   const align=par[0], mode=par[1]||'meet';
   if(!['meet','slice'].includes(mode))throw Error('Unsupported marker preserveAspectRatio');
   let sx=width/vb.width,sy=height/vb.height,dx=0,dy=0;
   if(align!=='none'){
    if(!/^x(Min|Mid|Max)Y(Min|Mid|Max)$/.test(align))throw Error('Unsupported marker alignment '+align);
    sx=sy=mode==='slice'?Math.max(sx,sy):Math.min(sx,sy);
    const [,ax,ay]=align.match(/^x(Min|Mid|Max)Y(Min|Mid|Max)$/);
    const ratio={Min:0,Mid:.5,Max:1};dx=(width-vb.width*sx)*ratio[ax];dy=(height-vb.height*sy)*ratio[ay];
   }
   view=new DOMMatrix().translate(dx,dy).scale(sx,sy).translate(-vb.x,-vb.y);
  }
  const ref=point(view,[number(marker.getAttribute('refX')),number(marker.getAttribute('refY'))]);
  const vertex=tangent(position),orient=marker.getAttribute('orient')||'0';
  let angle;
  if(orient==='auto'||orient==='auto-start-reverse')angle=vertex.angle+(orient==='auto-start-reverse'&&position==='start'?180:0);
  else {
   const a=orient.trim().match(/^([-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)(deg|rad|grad|turn)?$/);
   if(!a)throw Error('Unsupported marker orient '+orient);
   angle=Number(a[1])*({deg:1,rad:180/Math.PI,grad:.9,turn:360}[a[2]||'deg']);
  }
  const viewport=mat.translate(...vertex.p).rotate(angle).scale(unitScale).translate(-ref.x,-ref.y);
  const content=viewport.multiply(view);
  const rawClips=[];
  if(ms.overflow!=='visible')rawClips.push([{tag:'rect',attrs:{x:0,y:0,width,height},matrix:arr(viewport),fillRule:'nonzero'}]);
  let index=0;
  for(const child of marker.children){
   if(['title','desc','metadata'].includes(child.tagName))continue;
   if(!['path','polygon','polyline','line','rect','circle','ellipse'].includes(child.tagName))throw Error('Unsupported marker content '+child.tagName);
   const cs=getComputedStyle(child);
   if(cs.display==='none'||cs.visibility==='hidden')continue;
   if(cs.clipPath!=='none'||cs.maskImage!=='none'||cs.filter!=='none'||cs.mixBlendMode!=='normal')throw Error('Complex marker child effect unsupported');
   if([cs.markerStart,cs.markerMid,cs.markerEnd].some(v=>v&&v!=='none'))throw Error('Recursive marker unsupported');
   const m=content.multiply(own(child)), b=child.getBBox();
   const corners=[[b.x,b.y],[b.x+b.width,b.y],[b.x,b.y+b.height],[b.x+b.width,b.y+b.height]].map(p=>point(m,p));
   const x=Math.min(...corners.map(p=>p.x)),y=Math.min(...corners.map(p=>p.y));
   const color=v=>v==='context-stroke'?hostStyle.stroke:v==='context-fill'?hostStyle.fill:v;
   const key=(element.getAttribute('data-asset-key')||element.id||'connector')+'__marker_'+position+'_'+(++index);
   result.push({key,tag:child.tagName,attrs:attrs(child),matrix:arr(m),bbox:[x,y,Math.max(...corners.map(p=>p.x))-x,Math.max(...corners.map(p=>p.y))-y],
    markerPosition:position,markerId:id,rawClips,
    style:{fill:color(cs.fill),stroke:color(cs.stroke),strokeWidth:cs.strokeWidth,fillOpacity:cs.fillOpacity,strokeOpacity:cs.strokeOpacity,
     opacity:Number(cs.opacity)*opacity,linecap:cs.strokeLinecap,linejoin:cs.strokeLinejoin,miterlimit:cs.strokeMiterlimit,
     dasharray:cs.strokeDasharray,dashoffset:cs.strokeDashoffset,fillRule:cs.fillRule,vectorEffect:cs.vectorEffect,paintOrder:cs.paintOrder}});
  }
 }
 return result;
}'''
