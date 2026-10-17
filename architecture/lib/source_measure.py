"""Measure source SVG leaf objects in viewBox coordinates using Chromium."""
from pathlib import Path
import json
import xml.etree.ElementTree as ET

MEASURE_JS=r'''() => {
 const svg=document.querySelector('svg'),inv=svg.getScreenCTM().inverse(), vb=svg.viewBox.baseVal;
 const elements=[...svg.querySelectorAll('[data-asset-key]')].map(e=>{
  let b=e.getBBox(),m=inv.multiply(e.getScreenCTM()),pm=inv.multiply(e.parentElement.getScreenCTM());
  const p=[[b.x,b.y],[b.x+b.width,b.y],[b.x,b.y+b.height],[b.x+b.width,b.y+b.height]].map(([x,y])=>new DOMPoint(x,y).matrixTransform(m));
  let xs=p.map(x=>x.x),ys=p.map(x=>x.y),s=getComputedStyle(e),ts=e.querySelector('tspan'),f=ts?getComputedStyle(ts):s;
  const fontScale=Math.hypot(m.c,m.d)||Math.hypot(m.a,m.b);
  return {key:e.getAttribute('data-asset-key'),id:e.id,tag:e.localName,bounds:[Math.min(...xs),Math.min(...ys),Math.max(...xs)-Math.min(...xs),Math.max(...ys)-Math.min(...ys)],parent_matrix:[pm.a,pm.b,pm.c,pm.d,pm.e,pm.f],visible:s.display!=='none'&&s.visibility!=='hidden'&&s.opacity!=='0',text:e.localName==='text'?e.textContent:null,font_family:f.fontFamily,font_size:parseFloat(f.fontSize)*fontScale,font_weight:f.fontWeight,font_style:f.fontStyle,fill:s.fill,stroke:s.stroke};
 });return {viewBox:[vb.x,vb.y,vb.width,vb.height],elements};
}'''

def html(svg,width=1000):
    return f'<html><meta charset="utf-8"><style>html,body{{margin:0;background:white}}body>svg{{display:block;width:{width}px;height:auto}}</style>{svg}</html>'

def measure_page(page,svg,width=1000):
    page.set_content(html(svg,width));page.evaluate('document.fonts.ready')
    return page.evaluate(MEASURE_JS)

def measure_file(path):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b=p.chromium.launch();page=b.new_page(viewport={'width':1200,'height':900})
        g=measure_page(page,Path(path).read_text(encoding='utf-8'));b.close();return g
