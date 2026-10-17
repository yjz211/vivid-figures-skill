"""Semantic SVG primitives for the Vivid architecture recipes (logical units).

Every exported part is a named group with declared local bounds. Edges retain
their semantic endpoints. Geometry is intentionally visible and editable.
"""
from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
import json
import math
from pathlib import Path
import re
import textwrap
import xml.etree.ElementTree as ET

NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", NS)
INK = "#29333b"
PALETTE = {"blue": "#cbdff3", "green": "#c8ddb6", "yellow": "#ffe5a0",
           "pink": "#f2c8cb", "peach": "#f7d9c2", "purple": "#ded2e8",
           "grey": "#e6e9e9", "white": "#ffffff", "ink": INK}


def tag(name):
    return f"{{{NS}}}{name}"


def slug(text):
    return re.sub(r"[^a-zA-Z0-9_-]+", "-", str(text)).strip("-") or "part"


class Diagram:
    def __init__(self, width, height, title, *, print_width=468, palette=None):
        self.width, self.height = width, height
        self.palette = dict(PALETTE, **(palette or {}))
        self.root = ET.Element(tag("svg"), {"viewBox": f"0 0 {width} {height}",
            "width": f"{print_width}pt", "height": f"{print_width * height / width:.4f}pt",
            "data-vivid-architecture": "1", "font-family": "Arial, sans-serif",
            "font-size": "18", "fill": INK})
        ET.SubElement(self.root, tag("title")).text = title
        self.defs = ET.SubElement(self.root, tag("defs"))
        self.stack = [self.root]
        self.parts, self.edges = {}, []
        self.rect(0, 0, width, height, fill="white", stroke="none")

    def color(self, value):
        return self.palette.get(value, value)

    def add(self, name, **attrs):
        values = {key.replace('_', '-'): str(value) for key, value in attrs.items() if value is not None}
        return ET.SubElement(self.stack[-1], tag(name), values)

    @contextmanager
    def group(self, ident, bounds, role="component", *, export=True, description=None):
        ident = slug(ident)
        if ident in self.parts:
            raise ValueError(f"Duplicate semantic ID: {ident}")
        attrs = {"id": ident, "data-role": role, "data-bounds": " ".join(map(str, bounds))}
        if export:
            attrs["data-vivid-part"] = ident
        element = ET.SubElement(self.stack[-1], tag("g"), attrs)
        if description:
            ET.SubElement(element, tag("desc")).text = description
        self.parts[ident] = {"id": ident, "bounds": list(bounds), "role": role, "export": export}
        self.stack.append(element)
        try:
            yield element
        finally:
            self.stack.pop()

    def rect(self, x, y, w, h, fill="white", stroke=INK, sw=1.6, rx=0, dash=None):
        return self.add("rect", x=x, y=y, width=w, height=h, rx=rx,
                        fill=self.color(fill), stroke=self.color(stroke), stroke_width=sw,
                        stroke_dasharray=dash)

    def circle(self, x, y, r, fill="blue", stroke=INK, sw=1.5):
        return self.add("circle", cx=x, cy=y, r=r, fill=self.color(fill), stroke=self.color(stroke), stroke_width=sw)

    def ellipse(self, x, y, rx, ry, fill="blue", stroke="none", sw=1.5):
        return self.add("ellipse", cx=x, cy=y, rx=rx, ry=ry, fill=self.color(fill), stroke=self.color(stroke), stroke_width=sw)

    def path(self, points, *, stroke=INK, sw=1.7, dash=None, arrow=False, fill="none"):
        d = points if isinstance(points, str) else "M " + " L ".join(f"{x:g} {y:g}" for x,y in points)
        marker = None
        if arrow:
            mid = "arrow-" + slug(self.color(stroke))
            if self.defs.find(f".//*[@id='{mid}']") is None:
                m = ET.SubElement(self.defs, tag("marker"), {"id": mid, "viewBox": "0 0 10 8", "refX": "9", "refY": "4", "markerWidth": "6", "markerHeight": "5", "orient": "auto-start-reverse", "markerUnits": "strokeWidth"})
                ET.SubElement(m, tag("path"), {"d": "M0 0 L10 4 L0 8 Z", "fill": self.color(stroke)})
            marker = f"url(#{mid})"
        return self.add("path", d=d, fill=self.color(fill), stroke=self.color(stroke), stroke_width=sw,
                        stroke_dasharray=dash, marker_end=marker, stroke_linejoin="round")

    def text(self, x, y, value, size=18, anchor="middle", weight="normal", fill=INK, width=None, italic=False):
        # Coordinates describe the centre of the text block. Browser geometry is
        # subsequently checked against data-text-box; wrapping is never proof.
        lines = []
        for line in str(value).split("\n"):
            if width:
                lines.extend(textwrap.wrap(line, max(1, int(width/(size*.55))), break_long_words=False, break_on_hyphens=False) or [""])
            else:
                lines.append(line)
        line_height = size * 1.18
        first_y = y - (len(lines)-1)*line_height/2 + size*.34
        e = self.add("text", x=x, y=first_y, font_size=size, text_anchor=anchor,
                     font_weight=weight, fill=self.color(fill), font_style="italic" if italic else None)
        if width:
            left = x-width/2 if anchor=="middle" else (x-width if anchor=="end" else x)
            e.set("data-text-box", f"{left} {y-len(lines)*line_height/2-3} {width} {len(lines)*line_height+6}")
        for i,line in enumerate(lines):
            span = ET.SubElement(e, tag("tspan"), {"x": str(x), "y": str(first_y+i*line_height)})
            span.text = line
        return e

    def node(self, ident, x, y, w, h, label, *, fill="grey", size=19, weight="normal", rx=0, stroke=INK, dash=None):
        with self.group(ident, (x,y,w,h)):
            self.rect(x,y,w,h,fill=fill,stroke=stroke,rx=rx,dash=dash)
            if label:self.text(x+w/2,y+h/2,label,size=size,width=w-14,weight=weight)

    def edge(self, ident, source, target, points, *, label=None, at=None, color=INK, dash=None, arrow=True):
        e = self.path(points,stroke=color,dash=dash,arrow=arrow)
        e.set("id",slug(ident)); e.set("data-from",slug(source)); e.set("data-to",slug(target))
        self.edges.append({"id":slug(ident),"from":slug(source),"to":slug(target)})
        if label and at:
            self.text(*at,label,size=17,fill=color)

    def save(self, directory, filename="fig.svg"):
        directory=Path(directory); directory.mkdir(parents=True,exist_ok=True)
        for edge in self.edges:
            for side in ("from","to"):
                if edge[side] not in self.parts:
                    raise ValueError(f"Unknown edge endpoint: {edge}")
        ET.indent(self.root)
        (directory/filename).write_text(ET.tostring(self.root,encoding="unicode"),encoding="utf-8")
        (directory/"structure.json").write_text(json.dumps({"canvas":[self.width,self.height],"parts":list(self.parts.values()),"edges":self.edges},indent=2),encoding="utf-8")
        return directory/filename


def glyph(d, ident, x, y, w, h, spec):
    """Compound objects; explicit nodes/edges/values belong to the caller.

    Default shapes are schematic specimens, never measured or solved results.
    """
    if isinstance(spec,str): spec={"kind":spec}
    kind=spec.get("kind","document")
    colors=spec.get("colors",["blue","yellow","green","pink"])
    with d.group(ident,(x,y,w,h),role="object",description=spec.get("description",kind)):
        if kind=="graph":
            nodes=spec.get("nodes",[{"id":"a","x":.12,"y":.5},{"id":"b","x":.38,"y":.22},{"id":"c","x":.38,"y":.78},{"id":"d","x":.68,"y":.5},{"id":"e","x":.9,"y":.5}])
            pts={n["id"]:(x+n["x"]*w,y+n["y"]*h) for n in nodes}
            edges=spec.get("edges",[["a","b"],["a","c"],["b","d"],["c","d"],["d","e"]])
            for a,b in edges:
                if a not in pts or b not in pts: raise ValueError(f"Unknown graph endpoints {a,b}")
                ax,ay=pts[a]; bx,by=pts[b]; length=math.hypot(bx-ax,by-ay)
                pad=min(9,length*.2)
                d.path([(ax+(bx-ax)*pad/length,ay+(by-ay)*pad/length),(bx-(bx-ax)*pad/length,by-(by-ay)*pad/length)],arrow=spec.get("directed",True),sw=1.4)
            for i,n in enumerate(nodes):
                px,py=pts[n["id"]]; d.circle(px,py,spec.get("radius",9),n.get("color",colors[i%len(colors)]))
                if n.get("label"): d.text(px,py+21,n["label"],size=15)
        elif kind=="slots":
            rows=spec.get("rows",[[0,0,1,1,2],[1,2,2,0,0]])
            gap=5; cols=max(map(len,rows)); cw=(w-(cols-1)*gap)/cols; rh=min(24,(h-(len(rows)-1)*8)/len(rows))
            top=y+(h-len(rows)*rh-(len(rows)-1)*8)/2
            for r,row in enumerate(rows):
                for c,value in enumerate(row):
                    fill="white" if value is None else (colors[value%len(colors)] if isinstance(value,int) else value)
                    d.rect(x+c*(cw+gap),top+r*(rh+8),cw,rh,fill=fill,sw=1)
        elif kind=="timeline":
            rows=spec.get("rows",[[[0,2,0],[3,2,1]],[[1,2,2],[4,2,0]],[[2,2,1],[5,2,2]]])
            end=max((float(a)+float(b) for row in rows for a,b,*_ in row),default=1)
            dy=(h-15)/len(rows)
            for r,row in enumerate(rows):
                yy=y+r*dy; d.path([(x,yy+dy-5),(x+w,yy+dy-5)],stroke="#b3bdc4",sw=.8)
                for start,duration,*category in row:
                    d.rect(x+start/end*(w-4),yy+2,duration/end*(w-4)-2,dy-9,fill=colors[(category[0] if category else r)%len(colors)],sw=1)
            d.path([(x,y+h-3),(x+w,y+h-3)],arrow=True,sw=1)
        elif kind=="matrix":
            cells=spec.get("cells",[[1,0,0,1],[0,1,1,0],[1,0,1,0]])
            nr,nc=len(cells),len(cells[0]); gap=4; cw=(w-gap*(nc-1))/nc; ch=(h-gap*(nr-1))/nr
            for r,row in enumerate(cells):
                if len(row)!=nc: raise ValueError("Ragged matrix")
                for c,value in enumerate(row):
                    d.rect(x+c*(cw+gap),y+r*(ch+gap),cw,ch,fill=colors[r%len(colors)] if value else "white",sw=1)
        elif kind=="curves":
            if not spec.get('schematic') and not spec.get('evidence'):
                raise ValueError('Curves need evidence or an explicit schematic flag')
            d.path([(x+7,y+2),(x+7,y+h-5),(x+w,y+h-5)],arrow=True,sw=1.2)
            for i,points in enumerate(spec['series']):
                d.path([(x+12+px*(w-20),y+4+(1-py)*(h-15)) for px,py in points],stroke=colors[i%len(colors)],sw=2.5)
        elif kind=="stack":
            count=spec.get("count",3); offset=7; bw=w-offset*(count-1); bh=h-offset*(count-1)
            for i in reversed(range(count)):
                d.rect(x+i*offset,y+(count-1-i)*offset,bw,bh,fill=colors[i%len(colors)],sw=1.3)
            if spec.get("label"): d.text(x+bw/2,y+(count-1)*offset+bh/2,spec["label"],size=17,width=bw-8)
        elif kind=="document":
            d.rect(x,y,w,h,fill="white",sw=1.3)
            rows=spec.get("lines",["Input","Constraints","Output"])
            for i,line in enumerate(rows):
                yy=y+(i+.7)*h/len(rows); d.circle(x+8,yy,1.8,INK,stroke="none")
                d.text(x+16,yy,line,size=spec.get('font_size',18),anchor="start",width=w-24)
        else:
            raise ValueError(f"Unknown glyph {kind}; add a meaningful object implementation in diagram.py")


def export_parts(svg_path, out_dir):
    """Extract authored semantic groups, preserving vector elements and defs."""
    root=ET.parse(svg_path).getroot(); out=Path(out_dir);out.mkdir(parents=True,exist_ok=True)
    records=[]; all_defs=root.find(tag("defs"))
    for group in root.iter(tag("g")):
        name=group.get("data-vivid-part")
        if not name: continue
        x,y,w,h=map(float,group.get("data-bounds").split()); pad=4
        part=ET.Element(tag("svg"),{"viewBox":f"0 0 {w+2*pad:g} {h+2*pad:g}","width":str(w+2*pad),"height":str(h+2*pad),"font-family":root.get("font-family","Arial, sans-serif"),"font-size":root.get("font-size","18"),"fill":root.get("fill",INK)})
        if all_defs is not None: part.append(deepcopy(all_defs))
        wrapper=ET.SubElement(part,tag("g"),{"transform":f"translate({pad-x:g} {pad-y:g})"});wrapper.append(deepcopy(group))
        path=out/(name+".svg");path.write_text(ET.tostring(part,encoding="unicode"),encoding="utf-8")
        records.append({"id":name,"file":path.name,"role":group.get("data-role"),"source_bounds":[x,y,w,h]})
    (out/"index.json").write_text(json.dumps(records,indent=2),encoding="utf-8")
    return records


def run_recipe(build, recipe_file):
    import argparse
    parser=argparse.ArgumentParser(description=build.__doc__)
    parser.add_argument('--config',type=Path,default=Path(recipe_file).with_name('example.json'))
    parser.add_argument('--out',type=Path,default=Path.cwd())
    parser.add_argument('--print-width',type=float,default=468)
    parser.add_argument('--parts',action='store_true')
    args=parser.parse_args(); cfg=json.loads(args.config.read_text(encoding='utf-8'))
    d=build(cfg);d.root.set('width',f'{args.print_width}pt');d.root.set('height',f'{args.print_width*d.height/d.width:.4f}pt')
    path=d.save(args.out)
    (args.out/'config.used.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2),encoding='utf-8')
    if cfg.get('caption'): (args.out/'caption.txt').write_text(cfg['caption']+'\n',encoding='utf-8')
    if args.parts: export_parts(path,args.out/'parts')
    print(path)
