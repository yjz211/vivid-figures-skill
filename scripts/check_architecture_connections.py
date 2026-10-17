"""Advisory pre-export check for semantic straight-line SVG connections crossing text.

Reads an SVG without editing it or exporting an image. Only annotated simple
paths, lines and polylines are supported; this is not a design/fidelity review.
Requires the same Playwright/Chromium installation as render_architecture.py.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET


DEFAULT_TOLERANCE_PX = 0.75
EPSILON = 1e-7

# Measurements and transformed path points use CSS pixels relative to the root
# SVG at its declared display size. This makes the contact tolerance independent
# of the viewBox's arbitrary local units. No screenshot or PDF is generated.
MEASURE_JS = r'''() => {
  const root=document.querySelector('svg'), origin=root.getBoundingClientRect();
  const all=[...root.querySelectorAll('*')], order=new Map(all.map((e,i)=>[e,i]));
  function chain(e){const out=[];while(e){out.push(e);if(e===root)break;e=e.parentElement;}return out;}
  function opacity(e){return chain(e).reduce((v,n)=>v*Number(getComputedStyle(n).opacity),1);}
  function visible(e){return opacity(e)>0 && chain(e).every(n=>{const s=getComputedStyle(n);return s.display!=='none' && s.visibility!=='hidden' && s.visibility!=='collapse';});}
  function paintAlpha(value){const v=value.trim().toLowerCase();if(v==='none'||v==='transparent')return 0;const body=v.slice(v.indexOf('(')+1,-1);let alpha=null;if(body.includes('/'))alpha=body.split('/').pop().trim();else if(v.startsWith('rgba('))alpha=body.split(',').pop().trim();if(alpha===null)return 1;const n=alpha.endsWith('%')?Number.parseFloat(alpha)/100:Number.parseFloat(alpha);return Number.isFinite(n)?Math.max(0,Math.min(1,n)):1;}
  function painted(e,kind){const s=getComputedStyle(e);return paintAlpha(s[kind])>0&&Number(s[kind+'Opacity'])>0&&(kind!=='stroke'||Number.parseFloat(s.strokeWidth)>0);}
  function unsupported(e){const reasons=[];for(const n of chain(e)){const s=getComputedStyle(n);if(s.clipPath!=='none')reasons.push('clip-path');if(s.maskImage!=='none'||(n.getAttribute('mask')||'none')!=='none')reasons.push('mask');if(s.filter!=='none')reasons.push('filter');}return [...new Set(reasons)];}
  function matrix(e){const m=e.getScreenCTM();return [m.a,m.b,m.c,m.d,m.e-origin.left,m.f-origin.top];}
  function point(e,x,y){const [a,b,c,d,tx,ty]=matrix(e);return [a*x+c*y+tx,b*x+d*y+ty];}
  function box(e){const b=e.getBBox();const pts=[[b.x,b.y],[b.x+b.width,b.y],[b.x+b.width,b.y+b.height],[b.x,b.y+b.height]].map(([x,y])=>point(e,x,y));return [Math.min(...pts.map(p=>p[0])),Math.min(...pts.map(p=>p[1])),Math.max(...pts.map(p=>p[0])),Math.max(...pts.map(p=>p[1]))];}
  function owners(e){return chain(e).filter(n=>n.tagName.toLowerCase()==='g'&&n.id).map(n=>({id:n.id,role:n.getAttribute('data-role')}));}
  function axisAligned(e){const m=matrix(e);return Math.abs(m[1])<1e-8&&Math.abs(m[2])<1e-8;}
  const skipped_texts=[], texts=[];
  for(const e of root.querySelectorAll('text')){
    const reasons=unsupported(e);if(!visible(e))reasons.push('invisible');
    if(!axisAligned(e)||e.querySelector('[rotate]')||e.hasAttribute('rotate'))reasons.push('rotated-or-skewed-text');
    if(e.querySelector('textPath'))reasons.push('text-path');
    const spans=[...e.querySelectorAll('tspan')];
    if(spans.some(t=>t.querySelector('tspan'))||(spans.length&&[...e.childNodes].some(n=>n.nodeType===3&&n.textContent.trim())))reasons.push('mixed-or-nested-text-runs');
    if(reasons.length){skipped_texts.push({text:e.textContent.replace(/\s+/g,' ').trim(),reasons:[...new Set(reasons)]});continue;}
    for(const run of spans.length?spans:[e]){
      if(!run.textContent.trim())continue;
      const runReasons=unsupported(run);if(!visible(run))runReasons.push('invisible');if(!painted(run,'fill')&&!painted(run,'stroke'))runReasons.push('no-visible-text-paint');if(!axisAligned(run))runReasons.push('rotated-or-skewed-text');
      if(runReasons.length){skipped_texts.push({text:run.textContent.trim(),reasons:[...new Set(runReasons)]});continue;}
      texts.push({text:run.textContent.trim(),full_text:e.textContent.replace(/\s+/g,' ').trim(),box:box(run),order:order.get(e),owners:owners(e),visible:true,unsupported:[],edge_label_for:e.getAttribute('data-edge-label-for')});
    }
  }
  const paths=[...root.querySelectorAll('[data-from][data-to]')].map(e=>{
    const s=getComputedStyle(e),m=matrix(e),tag=e.tagName.toLowerCase();let d=e.getAttribute('d');const reasons=unsupported(e);
    if(tag==='line')d=`M ${e.x1.baseVal.value} ${e.y1.baseVal.value} L ${e.x2.baseVal.value} ${e.y2.baseVal.value}`;
    else if(tag==='polyline'){d=[...e.points].map((p,i)=>`${i?'L':'M'} ${p.x} ${p.y}`).join(' ');}
    else if(tag!=='path')reasons.push('unsupported-element:'+tag);
    if(!root.querySelector(`[id="${CSS.escape(e.getAttribute('data-from'))}"]`)||!root.querySelector(`[id="${CSS.escape(e.getAttribute('data-to'))}"]`))reasons.push('unresolved-semantic-endpoint');
    return {id:e.id||`edge-at-${order.get(e)}`,from:e.getAttribute('data-from'),to:e.getAttribute('data-to'),d,matrix:m,order:order.get(e),visible:visible(e)&&painted(e,'stroke'),unsupported:reasons,stroke_width:Number.parseFloat(s.strokeWidth)*Math.max(Math.hypot(m[0],m[1]),Math.hypot(m[2],m[3]))};
  });
  const rects=[...root.querySelectorAll('rect')].filter(visible).map(e=>{const s=getComputedStyle(e),rx=s.rx==='auto'?0:Number.parseFloat(s.rx),ry=s.ry==='auto'?0:Number.parseFloat(s.ry);return {order:order.get(e),box:box(e),fill:s.fill,effective_opacity:opacity(e),fill_opacity:Number(s.fillOpacity),simple:axisAligned(e)&&rx===0&&ry===0&&!unsupported(e).length};});
  return {paths,texts,rects,skipped_texts,display_size_css_px:[origin.width,origin.height]};
}'''


def parse_polyline_path(d):
    """Parse only M/L/H/V commands, including relative and implicit repetition."""
    token_re = re.compile(r'[A-Za-z]|[-+]?(?:\d*\.\d+|\d+\.?\d*)(?:[eE][-+]?\d+)?')
    tokens = token_re.findall(d or '')
    if token_re.sub('', d or '').strip(' ,\t\r\n'):
        raise ValueError('unparsed-path-data')
    if not tokens or tokens[0] not in ('M', 'm'):
        raise ValueError('path-must-start-with-moveto')
    if any(t.isalpha() and t not in 'MmLlHhVv' for t in tokens):
        raise ValueError('unsupported-path-command')
    result, i, command, current = [], 0, None, (0.0, 0.0)
    while i < len(tokens):
        if tokens[i].isalpha():
            command = tokens[i]
            i += 1
        count = 2 if command.upper() in 'ML' else 1
        if i + count > len(tokens) or any(t.isalpha() for t in tokens[i:i+count]):
            raise ValueError('incomplete-path-command')
        values = list(map(float, tokens[i:i+count])); i += count
        if not all(math.isfinite(v) for v in values):
            raise ValueError('non-finite-path-coordinate')
        x, y = current
        if command.upper() in 'ML':
            target = tuple(values) if command.isupper() else (x+values[0], y+values[1])
        elif command.upper() == 'H':
            target = (values[0] if command.isupper() else x+values[0], y)
        else:
            target = (x, values[0] if command.isupper() else y+values[0])
        if command.upper() != 'M':
            if current != target: result.append((current, target))
        else:
            command = 'L' if command == 'M' else 'l'
        current = target
    if not result:
        raise ValueError('no-nonzero-line-segments')
    return result


def segment_box_intersection(a, b, box):
    """Clip a segment to a bbox interior; a bbox-only path overlap is not a hit."""
    x0, y0, x1, y1 = box
    x0 += EPSILON; y0 += EPSILON; x1 -= EPSILON; y1 -= EPSILON
    if x0 >= x1 or y0 >= y1: return None
    dx, dy = b[0]-a[0], b[1]-a[1]
    lo, hi = 0.0, 1.0
    for p, q in ((-dx,a[0]-x0),(dx,x1-a[0]),(-dy,a[1]-y0),(dy,y1-a[1])):
        if abs(p)<EPSILON:
            if q<0: return None
        else:
            t=q/p
            if p<0: lo=max(lo,t)
            else: hi=min(hi,t)
            if lo>hi: return None
    if (hi-lo)*math.hypot(dx,dy)<EPSILON: return None
    return ((a[0]+lo*dx,a[1]+lo*dy),(a[0]+hi*dx,a[1]+hi*dy))


def opaque_color(fill):
    """Conservatively recognize opaque solid CSS colors, never paint servers."""
    value=str(fill).strip().lower()
    if value in ('none','transparent','') or value.startswith('url('): return False
    if value.startswith('#'):
        digits=value[1:]
        if not re.fullmatch('[0-9a-f]+',digits): return False
        return len(digits) in (3,6) or (len(digits)==4 and digits[-1]=='f') or (len(digits)==8 and digits[-2:]=='ff')
    match=re.fullmatch(r'rgba?\(([^)]+)\)',value)
    if match:
        content=match.group(1)
        if '/' in content:
            channels,alpha=content.rsplit('/',1)
        else:
            items=[v for v in re.split(r'[,\s]+',content.strip()) if v]
            if len(items)==3: return True
            if len(items)!=4: return False
            alpha=items[-1]
        try:
            alpha=alpha.strip()
            return float(alpha[:-1])/100 >= 1 if alpha.endswith('%') else float(alpha)>=1
        except ValueError:
            return False
    # Chromium normally returns rgb()/rgba(). A few literal names also make
    # pure-function tests and hand-authored geometry unambiguous.
    return value in ('white','black','red','green','blue','yellow','gray','grey')


def rect_is_opaque(rect):
    return (rect.get('simple',False) and rect.get('effective_opacity',0)>=1
            and rect.get('fill_opacity',0)>=1 and opaque_color(rect.get('fill','')))


def _transform(point, matrix):
    x,y=point; a,b,c,d,e,f=matrix
    return a*x+c*y+e,b*x+d*y+f


def _inside(point, box, margin=0):
    return (box[0]+margin-EPSILON<=point[0]<=box[2]-margin+EPSILON
            and box[1]+margin-EPSILON<=point[1]<=box[3]-margin+EPSILON)


def _near(a,b,tolerance):
    return math.hypot(a[0]-b[0],a[1]-b[1])<=tolerance+EPSILON


def analyze_geometry(geometry, tolerance_px=DEFAULT_TOLERANCE_PX):
    """Return advisory findings, retaining covered and minor contacts separately."""
    if not math.isfinite(tolerance_px) or tolerance_px<0:
        raise ValueError('tolerance_px must be a finite nonnegative number')
    findings, skipped, supported = [], [], 0
    for edge in geometry['paths']:
        reasons=list(edge.get('unsupported',[]))
        if not edge.get('visible',True): reasons.append('invisible-or-no-visible-stroke')
        if reasons:
            skipped.append({'edge':edge['id'],'reasons':reasons});continue
        try:
            segments=[(_transform(a,edge['matrix']),_transform(b,edge['matrix'])) for a,b in parse_polyline_path(edge['d'])]
        except ValueError as exc:
            skipped.append({'edge':edge['id'],'reasons':[str(exc)]});continue
        supported+=1
        for text in geometry['texts']:
            if not text.get('visible',True) or text.get('unsupported'): continue
            for index,(a,b) in enumerate(segments):
                overlap=segment_box_intersection(a,b,text['box'])
                if overlap is None: continue
                length=math.dist(*overlap)
                covers=[r for r in geometry['rects'] if rect_is_opaque(r)
                        and edge['order']<r['order']<text['order']
                        and all(_inside(p,r['box'],edge.get('stroke_width',0)/2) for p in overlap)]
                component_ids={o['id'] for o in text.get('owners',[]) if o.get('role') not in ('region','connection')}
                touches_source=(index==0 and edge['from'] in component_ids and _near(overlap[0],a,tolerance_px))
                touches_target=(index==len(segments)-1 and edge['to'] in component_ids and _near(overlap[1],b,tolerance_px))
                if covers: category='occluded-intersection'
                elif length<=tolerance_px and (touches_source or touches_target): category='minor-endpoint-contact'
                elif length<=tolerance_px: category='minor-text-contact'
                else: category='visible-text-intrusion'
                findings.append({'category':category,'edge':edge['id'],'from':edge['from'],'to':edge['to'],
                    'text':text['text'],'text_owners':text.get('owners',[]),'segment_index':index,
                    'text_box_css_px':text['box'],'intersection_css_px':[list(p) for p in overlap],
                    'intersection_length_css_px':length,
                    'declared_edge_label':text.get('edge_label_for')==edge['id'],
                    'covering_rectangles':[{'fill':r['fill'],'box_css_px':r['box'],'paint_order':r['order']} for r in covers]})
    counts={key:0 for key in ('visible-text-intrusion','minor-endpoint-contact','minor-text-contact','occluded-intersection')}
    counts.update(Counter(f['category'] for f in findings))
    total=len(geometry['paths'])
    if total==0: status='not-applicable'
    elif supported==0: status='not-checked'
    elif counts['visible-text-intrusion']: status='review-needed'
    elif findings: status='contacts-to-review'
    else: status='no-candidates-in-supported-geometry'
    return {'schema_version':1,'status':status,'advisory':True,
        'coverage':{'semantic_edges':total,'supported_edges':supported,'skipped_edges':len(skipped),
                    'tested_text_runs':len(geometry['texts']),'skipped_text_runs':len(geometry.get('skipped_texts',[]))},
        'coordinate_system':'CSS pixels relative to root SVG at declared display size',
        'display_size_css_px':geometry.get('display_size_css_px'),
        'contact_tolerance_css_px':tolerance_px,
        'tolerance_note':'Only intersections no longer than this tolerance are classified as minor. All remain reported; a component label is never exempt merely because it belongs to an endpoint.',
        'raw_hits':len(findings),'counts':counts,'findings':findings,
        'skipped_edges':skipped,'skipped_texts':geometry.get('skipped_texts',[]),
        'scope':'Annotated M/L/H/V paths, lines and polylines against actual unrotated text-run bounding boxes. Curves, close-path, clip/mask/filter and rotated text are not supported. Only fully opaque axis-aligned unrounded rectangles are considered as occluders. A bbox is not a glyph outline; candidates require visual review. Stroke width, arrowheads, dashed gaps, arbitrary overpainting, semantic correctness, design quality and template fidelity are not validated. No-candidates is not an overall pass.'}


def inspect_svg(path):
    """Measure one saved SVG and return the report without writing or rendering it."""
    from playwright.sync_api import sync_playwright
    path=Path(path).resolve()
    svg=path.read_text(encoding='utf-8')
    root=ET.fromstring(svg)
    if root.tag.split('}')[-1]!='svg': raise ValueError('Input root must be svg')
    with sync_playwright() as p:
        browser=p.chromium.launch()
        try:
            context=browser.new_context(viewport={'width':1600,'height':1200},java_script_enabled=False)
            context.route('**/*',lambda route:route.abort())
            page=context.new_page()
            page.set_content('<!doctype html><meta charset="utf-8"><style>html,body{margin:0}svg{display:block}</style>'+svg)
            page.evaluate('document.fonts.ready')
            geometry=page.evaluate(MEASURE_JS)
        finally:
            browser.close()
    result=analyze_geometry(geometry)
    result['svg']=str(path)
    return result


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('svg',type=Path)
    args=parser.parse_args(argv)
    try:
        path=args.svg.resolve()
        report=inspect_svg(path)
        output=path.with_suffix('.connections.json')
        output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    except Exception as exc:
        print(f'Connection check could not inspect input: {exc}',file=sys.stderr)
        return 2
    coverage=report['coverage'];counts=report['counts']
    print(f"Connection check (advisory): {report['status']}; "
          f"{coverage['supported_edges']}/{coverage['semantic_edges']} edges supported, "
          f"{coverage['skipped_edges']} skipped; "
          f"{counts['visible-text-intrusion']} text-intrusion candidates, "
          f"{counts['minor-endpoint-contact']+counts['minor-text-contact']} minor contacts, "
          f"{counts['occluded-intersection']} occluded intersections. Report: {output}")
    return 0


if __name__=='__main__':
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8')
    raise SystemExit(main())
