"""Editable labels and reusable original vector pieces for the Helix composition.

The source pieces retain original-author rights; this helper is new glue code.
No image crop, font outline or linked bitmap is used.
"""
from copy import deepcopy
from pathlib import Path
import json
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parent
LAYOUT=json.loads((ROOT/'source_layout.json').read_text(encoding='utf-8'))
COMPONENTS={g.get('id'):g for g in ET.parse(ROOT/'source_components.svg').getroot()}
NS='http://www.w3.org/2000/svg'
SERIF='Times New Roman, Times, serif'
MONO='Consolas, monospace'
COLORS={'controller':'#deebf7','blue':'#bdd7ee','green':'#c5e0b4',
        'yellow':'#ffe699','queue':'#a8d08c','layer':'#d0cece','event':'#e7e6e6'}


def union_bounds(pieces=(),labels=()):
    boxes=[LAYOUT['components'][p]['bounds'] for p in pieces]
    boxes.extend(LAYOUT['labels'][n]['bounds'] for n in labels)
    x=min(b[0] for b in boxes);y=min(b[1] for b in boxes)
    return x,y,max(b[0]+b[2] for b in boxes)-x,max(b[1]+b[3] for b in boxes)-y


def piece(d,name,*,at=None,size=None,recolor=None,keep_stroke=True):
    """Stamp an actual source vector. at is a new top-left, size is new w/h.

    Without arguments the exact original geometry is retained. Keep aspect for
    icons; resize frame backgrounds separately from text, icons and connectors.
    Scaled pieces keep a thin non-scaling outline by default. Set keep_stroke=False
    only if scaling the stroke with the shape is intentional. The caller owns
    the semantic group/declared bounds at its new location.
    """
    g=deepcopy(COMPONENTS[name]);g.attrib.pop('id',None);g.attrib.pop('data-bounds',None)
    g.set('data-source-piece',name)
    x,y,w,h=LAYOUT['components'][name]['bounds']
    if at is not None or size is not None:
        tx,ty=at or (x,y);nw,nh=size or (w,h)
        if not w or not h:raise ValueError('Use native paths for zero-area connector pieces')
        g.set('transform',f'translate({tx} {ty}) scale({nw/w} {nh/h}) translate({-x} {-y})')
        if size is not None and keep_stroke:
            for element in g.iter():
                if element.get('stroke') not in (None,'none'):
                    element.set('vector-effect','non-scaling-stroke')
    if recolor:
        for e in g.iter():
            for attr in ['fill','stroke']:
                if e.get(attr) in recolor:e.set(attr,recolor[e.get(attr)])
    d.stack[-1].append(g)
    return g


def label(d,name,overrides=None):
    """Retain editable, normally shaped text; no per-character x constraints."""
    spec=LAYOUT['labels'][name];lines=spec['lines']
    values=(overrides or {}).get(name,[line['text'] for line in lines])
    if isinstance(values,str):values=values.split('\n')
    if len(values)!=len(lines):
        raise ValueError(f'{name}: changed line count needs local layout adaptation')
    for line,value in zip(lines,values):
        e=d.add('text',x=line['x'],y=line['y'],font_size=spec['font_size'],
                font_family=spec['font_family'],fill='#000000',transform=spec['transform'])
        e.text=value


def source_block(d,ident,pieces,labels=(),*,role='component',overrides=None):
    with d.group(ident,union_bounds(pieces,labels),role=role):
        for name in pieces:piece(d,name)
        for name in labels:label(d,name,overrides)


def source_edge(d,ident,source,target,name,*,kind='flow'):
    g=piece(d,name);g.set('id',ident);g.set('data-from',source);g.set('data-to',target)
    d.edges.append({'id':ident,'from':source,'to':target,'kind':kind})
