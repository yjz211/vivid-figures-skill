"""Render and inspect an authored SVG using local Chromium; no FigGenie runtime."""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET


def parse_viewbox(value):
    """Accept the whitespace/comma SVG syntax used by the editing runtime."""
    try:
        values=[float(n) for n in re.split(r'[\s,]+',(value or '').strip())]
    except ValueError:
        values=[]
    if len(values)!=4 or not all(math.isfinite(n) for n in values) or values[2]<=0 or values[3]<=0:
        raise ValueError(f'Invalid SVG viewBox {value!r}: expected four finite numbers with positive width and height.')
    return values


def render(path, scale=2, min_font=7.5):
    from playwright.sync_api import sync_playwright
    import fitz
    svg=path.read_text(encoding='utf-8');root=ET.fromstring(svg)
    view=parse_viewbox(root.get('viewBox'));vx,vy,W,H=view
    width=float(re.match(r'[\d.]+',root.get('width','468')).group());height=width*H/W
    pxw,pxh=width*96/72,height*96/72
    html=f'''<!doctype html><meta charset="utf-8"><style>@page{{size:{width}pt {height}pt;margin:0}}html,body{{margin:0;background:white}}svg{{display:block;width:{width}pt;height:{height}pt}}</style>{svg}'''
    with sync_playwright() as p:
        browser=p.chromium.launch();page=browser.new_page(viewport={'width':int(pxw+.999),'height':int(pxh+.999)},device_scale_factor=scale)
        page.set_content(html);page.evaluate('document.fonts.ready')
        geometry=page.evaluate(r'''() => {
          const svg=document.querySelector('svg');
          const inverse=svg.getScreenCTM().inverse();
          function matrix(el){return inverse.multiply(el.getScreenCTM());}
          function box(el,b=el.getBBox()){const m=matrix(el);const pts=[[b.x,b.y],[b.x+b.width,b.y],[b.x,b.y+b.height],[b.x+b.width,b.y+b.height]].map(([x,y])=>new DOMPoint(x,y).matrixTransform(m));return [Math.min(...pts.map(p=>p.x)),Math.min(...pts.map(p=>p.y)),Math.max(...pts.map(p=>p.x)),Math.max(...pts.map(p=>p.y))];}
          function declaredBox(el,attribute){const value=el.getAttribute(attribute);if(!value)return null;const [x,y,width,height]=value.trim().split(/[\s,]+/).map(Number);return box(el,{x,y,width,height});}
          function fontRuns(el){
            const runs=[],walker=document.createTreeWalker(el,NodeFilter.SHOW_TEXT);
            let node;while(node=walker.nextNode()){
              if(!node.nodeValue.trim())continue;
              const source=node.parentElement,style=getComputedStyle(source),m=matrix(source);
              const font=Number.parseFloat(style.fontSize),fontScale=Math.hypot(m.c,m.d);
              runs.push({text:node.nodeValue,font,font_scale:fontScale,font_viewbox:font*fontScale});
            }
            return runs;
          }
          return {coordinate_space:'svg-viewbox',fonts:[...new Set([...document.querySelectorAll('text')].map(e=>getComputedStyle(e).fontFamily))],
            texts:[...document.querySelectorAll('text')].map(e=>({text:e.textContent,box:box(e),font:Number.parseFloat(getComputedStyle(e).fontSize),font_runs:fontRuns(e),constraint:e.getAttribute('data-text-box'),constraint_box:declaredBox(e,'data-text-box')})),
            groups:[...document.querySelectorAll('[data-vivid-part]')].map(e=>({id:e.id,bounds:e.getAttribute('data-bounds'),declared_box:declaredBox(e,'data-bounds'),box:box(e)}))};
        }''')
        page.screenshot(path=str(path.with_suffix('.png')),full_page=True)
        page.pdf(path=str(path.with_suffix('.pdf')),width=f'{width/72:.6f}in',height=f'{height/72:.6f}in',print_background=True,prefer_css_page_size=True,margin={'top':'0','right':'0','bottom':'0','left':'0'})
        browser.close()
    errors=[];warnings=[]
    for group in geometry['groups']:
        x,y,right,bottom=group['declared_box'];x0,y0,x1,y1=group['box']
        if x0<x-4.1 or y0<y-4.1 or x1>right+4.1 or y1>bottom+4.1:
            errors.append({'type':'part-export-crop','id':group['id'],'actual':group['box'],'declared':[x,y,right-x,bottom-y]})
    for t in geometry['texts']:
        x0,y0,x1,y1=t['box']
        if x0 < vx-.5 or y0 < vy-.5 or x1>vx+W+.5 or y1>vy+H+.5:errors.append({'type':'text-outside-canvas','text':t['text'],'box':t['box']})
        if t['constraint']:
            x,y,right,bottom=t['constraint_box']
            if x0<x-2 or x1>right+2 or y0<y-3 or y1>bottom+3:errors.append({'type':'text-overflow','text':t['text'],'box':t['box'],'expected':[x,y,right-x,bottom-y]})
        for run in t['font_runs']:run['print_font_pt']=run['font_viewbox']*width/W
        # A mixed-size label must not hide its smallest run behind its parent size.
        t['print_font_pt']=min((run['print_font_pt'] for run in t['font_runs']),default=None)
        if t['print_font_pt'] is not None and t['print_font_pt']<min_font:warnings.append({'type':'small-print-text','text':t['text'],'pt':round(t['print_font_pt'],2)})
    # Text intersections are findings, not a proof of full diagram correctness.
    for i,a in enumerate(geometry['texts']):
        for b in geometry['texts'][i+1:]:
            x=max(0,min(a['box'][2],b['box'][2])-max(a['box'][0],b['box'][0]));y=max(0,min(a['box'][3],b['box'][3])-max(a['box'][1],b['box'][1]))
            if x>3 and y>3:errors.append({'type':'text-overlap','texts':[a['text'],b['text']],'overlap':[round(x,1),round(y,1)]})
    doc=fitz.open(path.with_suffix('.pdf'));pdfpage=doc[0];fonts=pdfpage.get_fonts(full=True)
    font_meta=root.find("{http://www.w3.org/2000/svg}metadata[@id='vivid-font-profile']")
    font_report=None
    if font_meta is not None:
        font_report=json.loads(font_meta.text)
        expected={f['postscript_name'] for f in font_report['roles']}
        actual={f[3].split('+')[-1] for f in fonts}
        embedded=bool(fonts) and all(len(doc.extract_font(f[0])[3])>0 for f in fonts)
        font_report.update(pdf_fonts=sorted(actual),pdf_fonts_embedded=embedded,
                           pdf_matches_declared_fonts=actual==expected)
        if actual!=expected:errors.append({'type':'font-substitution','expected':sorted(expected),'actual':sorted(actual)})
        if not embedded:errors.append({'type':'font-not-embedded'})
        path.with_suffix('.fonts.json').write_text(json.dumps(font_report,ensure_ascii=False,indent=2),encoding='utf-8')
    result={'svg':str(path),'print_size_pt':[width,height],'text_count':len(geometry['texts']),'parts':len(geometry['groups']),'errors':errors,'warnings':warnings,'pdf':{'page_count':len(doc),'fonts':[{'name':f[3],'type':f[2]} for f in fonts],'images':len(pdfpage.get_images(full=True))},'scope':'Measured text bounds, intersections, print font size, and PDF structure. Connections and visual fidelity require actual image inspection.'}
    if font_report:result['font_profile']={k:font_report[k] for k in ['profile','svg_embeds_font_files','pdf_fonts_embedded','pdf_matches_declared_fonts']}
    path.with_suffix('.checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    path.with_suffix('.geometry.json').write_text(json.dumps(geometry,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))
    return 1 if errors else 0


if __name__=='__main__':
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('svg',type=Path);parser.add_argument('--scale',type=float,default=2);parser.add_argument('--min-font',type=float,default=7.5);args=parser.parse_args()
    raise SystemExit(render(args.svg.resolve(),args.scale,args.min_font))
